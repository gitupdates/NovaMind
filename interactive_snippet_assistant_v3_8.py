#!/usr/bin/env python3
"""Interactive Snippet Assistant v3.8.0

Runs Python snippets in a subprocess with basic resource limits and
provides simple error diagnostics. Version 3.8 adds optional JSON output
and custom interpreter selection for greater flexibility.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from typing import Any, Dict, Optional, Tuple

VERSION = "3.8.0"

# Precompile for faster and more reliable error-type extraction
ERROR_LINE_RE = re.compile(r"^([A-Za-z_][\w\.]*):\s*(.*)$")


def _posix_preexec(cpu_seconds: int, mem_mb: int):
    """Return a function to set resource limits in a child process."""

    def _set_limits():
        try:
            import resource
            import signal

            if hasattr(resource, "RLIMIT_CPU"):
                resource.setrlimit(resource.RLIMIT_CPU,
                                   (cpu_seconds, cpu_seconds))
            mem_bytes = mem_mb * 1024 * 1024
            if hasattr(resource, "RLIMIT_AS"):
                resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
            if hasattr(resource, "RLIMIT_FSIZE"):
                resource.setrlimit(resource.RLIMIT_FSIZE,
                                   (16 * 1024 * 1024, 16 * 1024 * 1024))
            if hasattr(resource, "RLIMIT_NOFILE"):
                try:
                    cur_soft, cur_hard = resource.getrlimit(
                        resource.RLIMIT_NOFILE)
                    new_soft = min(256, cur_soft if cur_soft !=
                                   resource.RLIM_INFINITY else 256)
                    resource.setrlimit(
                        resource.RLIMIT_NOFILE, (new_soft, cur_hard))
                except Exception:
                    pass
            # ensure SIGPIPE is default (avoid BrokenPipe crashes)
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        except Exception as e:
            sys.stderr.write(f"[warn] Failed to set POSIX limits: {e}\n")

    return _set_limits


def _parse_error_fields(stderr_text: str) -> Tuple[Optional[str], Optional[str]]:
    if not stderr_text:
        return None, None
    for raw in reversed(stderr_text.strip().splitlines()):
        m = ERROR_LINE_RE.match(raw.strip())
        if m:
            return m.group(1), m.group(2)
    return None, None


def error_correct_code_suggestion(execution_result: Dict[str, Any]) -> str:
    """Return a suggestion message based on captured error info."""

    if execution_result["status"] == "success":
        return "No errors detected. Code executed successfully."

    error_type = execution_result.get("error_type")
    error_message = execution_result.get("error_message", "")
    suggestion = f"Error Type: **{error_type}**\nError Message: {error_message}\n\n"

    if error_type == "SyntaxError":
        suggestion += (
            "Suggestion: Check for typos, missing colons, incorrect indentation, or unclosed parentheses/brackets/quotes."
        )
    elif error_type == "NameError":
        suggestion += (
            "Suggestion: A variable or function was used before being defined or is misspelled."
        )
    elif error_type == "TypeError":
        suggestion += (
            "Suggestion: Incompatible data types were used together. Verify variable types before operations."
        )
    elif error_type == "IndentationError":
        suggestion += (
            "Suggestion: Python relies on consistent indentation. Ensure spaces/tabs are correct."
        )
    elif error_type in {"ImportError", "ModuleNotFoundError"}:
        suggestion += (
            "Suggestion: Required module not found. Install missing dependencies and check virtual environments."
        )
    elif error_type == "ZeroDivisionError":
        suggestion += "Suggestion: Ensure divisors are not zero before dividing."
    elif error_type == "KeyError":
        suggestion += "Suggestion: Accessing missing dict key. Use dict.get() or verify the key exists."
    elif error_type == "IndexError":
        suggestion += "Suggestion: Sequence index is out of range or negative. Check length before accessing."
    elif error_type == "AttributeError":
        suggestion += (
            "An attribute or method is missing on an object. Double-check the object's type and available attributes (dir(obj))."
        )
    elif error_type == "ValueError":
        suggestion += (
            "A function received a value of correct type but invalid content. Validate inputs before using them."
        )
    elif error_type == "FileNotFoundError":
        suggestion += (
            "The file path does not exist. Check working directory and use absolute paths if necessary."
        )
    elif error_type == "RecursionError":
        suggestion += (
            "Maximum recursion depth exceeded. Convert deep recursion to iteration or increase the limit cautiously via sys.setrecursionlimit()."
        )
    elif error_type == "MemoryError":
        suggestion += (
            "The operation ran out of memory. Process data in chunks, use generators, or increase limits."
        )
    elif error_type == "OSError":
        suggestion += (
            "An OS-level error occurred (permissions, missing resources, etc.). Log e.errno and e.strerror for details."
        )
    elif error_type == "TimeoutExpired":
        suggestion += (
            "The code took too long. Consider optimizing or increasing the timeout. If the snippet waits on input(), pass --stdin-data or remove blocking reads."
        )
    else:
        suggestion += "Suggestion: Review the traceback to identify where the error occurred."

    suggestion += (
        "\n\nFor more details, see the Python docs: https://docs.python.org/3/reference/index.html"
    )
    return suggestion


def execute_in_subprocess(
    src: str,
    timeout: int = 5,
    stdin_data: str | bytes | None = None,
    cpu_seconds: int = 5,
    mem_mb: int = 128,
    python_exe: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the given code in a separate Python process and capture results."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(src)
        tmp_path = tmp.name

    python_exe = python_exe or sys.executable
    cmd = [python_exe, "-I", "-B", tmp_path]
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "LC_ALL": "C.UTF-8",
        "LANG": "C.UTF-8",
    }

    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "stdin": subprocess.PIPE if stdin_data is not None else None,
        "text": True,
        "close_fds": True,
        "env": env,
    }
    if os.name != "nt":
        kwargs["preexec_fn"] = _posix_preexec(cpu_seconds, mem_mb)

    if isinstance(stdin_data, bytes) and kwargs.get("text", True):
        try:
            stdin_data = stdin_data.decode("utf-8")
        except Exception:
            stdin_data = stdin_data.decode("utf-8", errors="replace")

    try:
        proc = subprocess.run(cmd, input=stdin_data, timeout=timeout, **kwargs)
        stdout = proc.stdout
        stderr = proc.stderr
        status = "success" if proc.returncode == 0 else "error"
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout or ""
        stderr = e.stderr or ""
        status = "timeout"
        error_type = "TimeoutExpired"
        error_message = str(e)
        return {
            "status": status,
            "stdout": stdout,
            "stderr": stderr,
            "error_type": error_type,
            "error_message": error_message,
        }
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    error_type, error_message = _parse_error_fields(stderr)
    return {
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "error_type": error_type,
        "error_message": error_message,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Python snippets safely")
    parser.add_argument("--file", "-f", type=str,
                        help="File containing Python code")
    parser.add_argument("--stdin-data", type=str, default=None,
                        help="Data passed to snippet's stdin")
    parser.add_argument("--python-exe", type=str, default=None,
                        help="Python interpreter to run the snippet")
    parser.add_argument("--json", action="store_true",
                        help="Output execution result as JSON")
    parser.add_argument("--version", action="version",
                        version=f"Interactive Snippet Assistant {VERSION}")
    parser.add_argument("--timeout", type=int, default=5,
                        help="Timeout in seconds")
    parser.add_argument("--cpu-seconds", type=int, default=5,
                        help="CPU time limit for the snippet")
    parser.add_argument("--mem-mb", type=int, default=128,
                        help="Memory limit in MB for the snippet")
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()
        except OSError as exc:
            print(f"Failed to read file: {exc}")
            return
    else:
        code = sys.stdin.read()
        if not code:
            print("No code provided on stdin and no file specified.")
            return

    result = execute_in_subprocess(
        code,
        timeout=args.timeout,
        stdin_data=args.stdin_data,
        cpu_seconds=args.cpu_seconds,
        mem_mb=args.mem_mb,
        python_exe=args.python_exe,
    )

    if args.json:
        import json
        print(json.dumps(result, indent=2))
        return

    print(result["stdout"], end="")
    if result["stderr"]:
        print(result["stderr"], file=sys.stderr, end="")
    if result["status"] != "success":
        print(error_correct_code_suggestion(result))


if __name__ == "__main__":
    main()
