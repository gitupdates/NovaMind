# NovaMind Architecture Overview

NovaMind is a modular, self-upgrading hybrid intelligence framework. The system supports autonomous benchmarking, auditing, and live introspection through GUI and web interfaces.

## Directory Structure

NovaMind/
├── .github/
│   └── workflows/                   # GitHub Actions for CI/CD automation
├── cores/                           # Cognitive cores: memory manager, migration, scrubber, etc.
│   ├── memory_manager.py
│   ├── memory_migration.py
│   └── ...
├── quantum/                         # Quantum simulation, optimization, error correction
│   ├── quantum_memory_superposition.py
│   ├── quantum_optimizer.py
│   └── ...
├── engine/                          # Core orchestration, benchmarking, audit flow
│   ├── engine.py
│   ├── engine_benchmark_overlay.py
│   └── intelligent_orchestrator_core.py
├── gui/                             # Desktop GUI (Tkinter-based)
│   └── virtual_chatbot_gui.py
├── dashboard_module.py              # Modular Flask blueprint for web dashboard
├── templates/                       # HTML templates for Flask dashboard
│   └── dashboard.html
├── static/                          # Optional CSS/JS for Flask UI
├── logs/                            # Runtime traces, crash logs, attention maps
│   └── recall_traces/
├── benchmark/                       # Pre/post-upgrade benchmark CSVs
│   └── benchmark_diff_*.csv
├── registry.json                    # Master config: core metadata, versions, capabilities
├── Dockerfile                       # Containerized deployment build script
├── requirements.txt                 # Python dependencies
├── README.md                        # Project overview and usage
└── app.py                           # Entrypoint: registers GUI and/or dashboard modules

## Python Code Assistant

The repository includes python_code_assistant.py **v1.1**, an optional
utility that executes and analyzes snippets of Python code. To run it
interactively:

```bash
python python_code_assistant.py
```

To analyze a file in one shot:

```bash
python python_code_assistant.py --file path/to/script.py
```

Use `--format` to print a PEP&nbsp;8 formatted version of the file when
autopep8 is available:

```bash
python python_code_assistant.py --file path/to/script.py --format
```

### Dependencies

Install requirements within a virtual environment. autopep8 is optional and
only needed if you want automatic formatting suggestions:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you prefer not to use requirements.txt, you can manually install
autopep8 using:

```bash
pip install autopep8
```

## Interactive Snippet Assistant

Version 3.8 of the interactive snippet assistant adds optional JSON output and
the ability to select a custom Python interpreter.
Run the `interactive_snippet_assistant_v3_8.py` script similarly to the code
assistant:

```bash
python interactive_snippet_assistant_v3_8.py --file my_script.py
```

You can also pipe code via standard input:

```bash
echo "print('hi')" | python interactive_snippet_assistant_v3_8.py
```

Use --stdin-data to pass input to the snippet and --timeout to control the
execution timeout. You can also change resource limits:

```
--cpu-seconds <N>  # CPU time limit (default 5 seconds)
--mem-mb <N>       # Memory limit in megabytes (default 128)
```

Additional options include `--json` to emit structured output and
`--python-exe` to choose the interpreter.

For example:

```bash
python interactive_snippet_assistant_v3_8.py --file script.py --cpu-seconds 10 --mem-mb 256 --json
```

## Evolutionary Problem Solver

The `evo_problem_solver.py` script combines a suite of local linters and
formatters with optional offline language models to repair or modernize Python
code. It can also generate new code entirely from a problem description.

Basic usage examples:

```bash
# Generate code from a text prompt
python evo_problem_solver.py solve "calculate fibonacci numbers"

# Repair a file in place
python evo_problem_solver.py repair my_script.py --inplace

# Upgrade a file and print modernization hints
python evo_problem_solver.py upgrade legacy.py
```

The tool installs required dependencies on first run. For best results, provide
a local LLM path via `$LLAMA_MODEL_PATH` or `$GPT4ALL_MODEL_PATH`, or set
`$OFFLINE_LLM_CMD` to pipe prompts to another model.
