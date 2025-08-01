from __future__ import annotations

import ast
import importlib
import importlib.metadata as im
import logging
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
logging.basicConfig(
    format="%(levelname)s | %(message)s",
    level=logging.INFO,
)
LOG = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------
MAX_PASSES = 3
TIMEOUT = 45  # seconds per external call

# Mandatory base tools
BASE_PKGS: tuple[str, ...] = (
    "autopep8",
    "autoflake",
    "bandit",
    "isort",
    "pyright",
    "pyupgrade",
    "refurb",
    "ruff",
)

# Optional LLM runtimes (installed if absent)
LLM_PKGS: tuple[str, ...] = (
    "llama-cpp-python",  # wheels for most OSes
    "gpt4all",
    "ctransformers",
)

REQUIRED_PKGS = BASE_PKGS + LLM_PKGS

# Env-vars
LLAMA_MODEL_ENV = "LLAMA_MODEL_PATH"
GPT4ALL_MODEL_ENV = "GPT4ALL_MODEL_PATH"
OFFLINE_LLM_CMD_ENV = "OFFLINE_LLM_CMD"

# ------------------------------------------------------------------------------
# Dependency bootstrap
# ------------------------------------------------------------------------------

def _ensure_pip() -> None:
    """Make sure `pip` is importable (runs ensurepip if missing)."""
    try:
        import pip  # noqa: F401
    except ModuleNotFoundError:
        import ensurepip  # noqa: WPS433
        ensurepip.bootstrap(upgrade=True)
        importlib.invalidate_caches()


def _install(pkgs: Iterable[str]) -> None:
    if not pkgs:
        return
    LOG.info("Installing: %s", ", ".join(pkgs))
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", *pkgs],
            check=True,
            timeout=TIMEOUT * 3,
        )
    except subprocess.CalledProcessError as err:
        LOG.error("pip install failed: %s", err)


def _bootstrap() -> None:
    _ensure_pip()
    missing = [
        p for p in REQUIRED_PKGS if not im.packages_distributions().get(p.split("==")[0])
    ]
    if missing:
        _install(missing)
    importlib.invalidate_caches()


_bootstrap()

# Mandatory imports now safe
import autopep8  # noqa: E402
from isort import code as isort_code  # noqa: E402

# ------------------------------------------------------------------------------
# Data structures
# ------------------------------------------------------------------------------
@dataclass(slots=True)
class Issue:
    line: int
    message: str
    source: str  # syntax | runtime | ruff | pyright | bandit

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _run_cmd(
    cmd: Sequence[str], *, inp: str | None = None, timeout: int = TIMEOUT
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=inp,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _tmp_transform(code: str, cmd: Sequence[str]) -> str:
    """Run an external transformer that rewrites a temp file."""
    try:
        with tempfile.NamedTemporaryFile("w+", suffix=".py", delete=False) as tf:
            path = Path(tf.name)
            tf.write(code)
            tf.flush()
        _run_cmd([*cmd, str(path)])
        return path.read_text("utf-8")
    except FileNotFoundError:
        LOG.debug("[%s] missing; skipped", cmd[0])
        return code
    finally:
        try:
            path.unlink()  # type: ignore[name-defined]
        except Exception:  # noqa: BLE001
            pass


def _stdin_transform(code: str, cmd: Sequence[str]) -> str:
    try:
        res = _run_cmd(cmd, inp=code)
        return res.stdout or code
    except FileNotFoundError:
        LOG.debug("[%s] missing; skipped", cmd[0])
        return code


def _python_target_flag() -> str:
    maj, min_ = sys.version_info[:2]
    return f"--py{maj}{min_}-plus"

# ------------------------------------------------------------------------------
# Fixer pipeline
# ------------------------------------------------------------------------------
class _Pipeline:
    def __init__(self) -> None:
        self.steps = [
            ("isort", lambda c: isort_code(c)),
            ("pyupgrade", lambda c: _tmp_transform(c, ["pyupgrade", _python_target_flag()])),
            ("refurb", lambda c: _tmp_transform(c, ["refurb", "--apply"])),
            ("autoflake", lambda c: _stdin_transform(c, ["autoflake", "--remove-unused-variables", "-"])),
            ("autopep8", lambda c: autopep8.fix_code(c)),
            ("ruff-fix", lambda c: _stdin_transform(c, ["ruff", "--fix", "--quiet", "-"]))
        ]

    def run(self, code: str) -> str:
        for label, fn in self.steps:
            new_code = fn(code)
            if new_code != code:
                LOG.debug("Applied %s", label)
            code = new_code
        return code

# ------------------------------------------------------------------------------
# Analysis
# ------------------------------------------------------------------------------

def _syntax_check(code: str) -> List[Issue]:
    try:
        ast.parse(code)
        return []
    except SyntaxError as e:
        return [Issue(e.lineno or 0, e.msg, "syntax")]


def _runtime_check(code: str) -> List[Issue]:
    try:
        compile(code, "<string>", "exec")
        return []
    except Exception as e:  # noqa: BLE001
        return [Issue(getattr(e, "lineno", 0) or 0, f"{type(e).__name__}: {e}", "runtime")]


def _lint_external(code: str) -> List[Issue]:
    tmp = Path(tempfile.mkstemp(suffix=".py")[1])
    tmp.write_text(code, "utf-8")
    issues: list[Issue] = []

    def capture(cmd: Sequence[str], tag: str) -> None:
        try:
            out = _run_cmd([*cmd, str(tmp)]).stdout
            for line in out.splitlines():
                parts = line.split(":", 3)
                if len(parts) >= 3 and parts[1].isdigit():
                    issues.append(Issue(int(parts[1]), parts[-1].strip(), tag))
        except FileNotFoundError:
            LOG.debug("[%s] missing; skipped", cmd[0])

    capture(["ruff", "--quiet"], "ruff")
    capture(["pyright", "-q"], "pyright")
    capture(["bandit", "-q", "-r"], "bandit")
    tmp.unlink(missing_ok=True)
    return issues

# ------------------------------------------------------------------------------
# Local LLM orchestration
# ------------------------------------------------------------------------------

def _solve_with_local_llm(prompt: str) -> str | None:
    """Return code string or None if no local model responded."""
    # 1. llama-cpp
    try:
        import llama_cpp  # noqa: E402
        model_path = os.getenv(LLAMA_MODEL_ENV)
        if model_path and Path(model_path).is_file():
            LOG.info("Using llama-cpp-python")
            llm = llama_cpp.Llama(model_path=model_path, n_ctx=4096)
            out = llm(prompt)["choices"][0]["text"]
            return out
    except Exception as e:  # noqa: BLE001
        LOG.debug("llama-cpp failed: %s", e)

    # 2. GPT4All
    try:
        from gpt4all import GPT4All  # noqa: E402
        model_path = os.getenv(GPT4ALL_MODEL_ENV)
        if model_path and Path(model_path).is_file():
            LOG.info("Using GPT4All-py")
            with GPT4All(model_path) as m:
                return m.generate(prompt, max_tokens=1024)
    except Exception as e:  # noqa: BLE001
        LOG.debug("GPT4All failed: %s", e)

    # 3. ctransformers
    try:
        from ctransformers import AutoModelForCausalLM  # noqa: E402
        model_path = (
            os.getenv(LLAMA_MODEL_ENV) or os.getenv(GPT4ALL_MODEL_ENV)
        )
        if model_path and Path(model_path).is_file():
            LOG.info("Using ctransformers")
            llm = AutoModelForCausalLM.from_pretrained(model_path, model_type="llama")
            return llm(prompt)
    except Exception as e:  # noqa: BLE001
        LOG.debug("ctransformers failed: %s", e)

    # 4. User-supplied pipe
    cmd = os.getenv(OFFLINE_LLM_CMD_ENV)
    if cmd:
        LOG.info("Using $OFFLINE_LLM_CMD")
        try:
            return _run_cmd(cmd.split(), inp=prompt).stdout
        except Exception as e:  # noqa: BLE001
            LOG.error("OFFLINE_LLM_CMD failed: %s", e)
    return None

# ------------------------------------------------------------------------------
# Main solver class
# ------------------------------------------------------------------------------
class PythonProblemSolver:
    def __init__(self, *, strip_non_ascii: bool = True) -> None:
        self.pipeline = _Pipeline()
        self.strip = strip_non_ascii

    # --------------- public --------------- #
    def solve_problem(self, description: str) -> str:
        prompt = (
            "Write valid Python that solves the task and output ONLY code:\n\n"
            + description
        )
        result = _solve_with_local_llm(prompt)
        if result is None:
            raise RuntimeError(
                "No local LLM available.  Install llama-cpp-python or set "
                f"{OFFLINE_LLM_CMD_ENV}."
            )
        return self._postprocess(result)

    def repair_code(self, code: str) -> Tuple[str, List[Issue]]:
        code = self._preprocess(code)
        for _ in range(MAX_PASSES):
            diag = self._diagnose(code)
            if not any(i.source == "runtime" for i in diag):
                break
            code = self.pipeline.run(code)
        return self._postprocess(code), self._diagnose(code)

    def upgrade_code(self, code: str) -> Tuple[str, dict[int, str]]:
        code = self.pipeline.run(self._preprocess(code))
        return self._postprocess(code), self._heuristics(code)

    # --------------- helpers --------------- #
    def _preprocess(self, code: str) -> str:
        if self.strip:
            code = re.sub(r"[^\x00-\x7F]+", "", code)
        return code.replace("\r\n", "\n")

    @staticmethod
    def _postprocess(code: str) -> str:
        return code.rstrip() + "\n"

    @staticmethod
    def _heuristics(code: str) -> dict[int, str]:
        hints: dict[int, str] = {}
        for n, line in enumerate(code.splitlines(), 1):
            if ".format(" in line:
                hints[n] = "Use f-string"
            elif "os.path" in line:
                hints[n] = "Use pathlib"
            elif "+" in line and any(q in line for q in ('"', "'")):
                hints[n] = "Use f-string"
        return hints

    @staticmethod
    def _diagnose(code: str) -> List[Issue]:
        return _syntax_check(code) + _runtime_check(code) + _lint_external(code)

# ------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------

def _cli() -> None:
    import argparse

    pa = argparse.ArgumentParser(prog="evo-problem-solver")
    sub = pa.add_subparsers(dest="cmd", required=True)

    s0 = sub.add_parser("solve");   s0.add_argument("desc")
    s1 = sub.add_parser("repair");  s1.add_argument("file", type=Path); s1.add_argument("--inplace", action="store_true")
    s2 = sub.add_parser("upgrade"); s2.add_argument("file", type=Path); s2.add_argument("--inplace", action="store_true")

    a = pa.parse_args()
    solver = PythonProblemSolver()

    if a.cmd == "solve":
        print(solver.solve_problem(a.desc))
        return

    text = a.file.read_text("utf-8")
    if a.cmd == "repair":
        fixed, issues = solver.repair_code(text)
    else:
        fixed, issues = solver.upgrade_code(text)

    (a.file if a.inplace else sys.stdout).write(fixed)
    if issues:
        LOG.info("--- diagnostics ---")
        for iss in issues:
            LOG.warning("%s:L%s %s: %s", a.file.name, iss.line, iss.source, iss.message)

if __name__ == "__main__":
    _cli()
