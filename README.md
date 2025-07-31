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

The repository includes python_code_assistant.py, an optional utility that
executes and analyzes snippets of Python code. To run it interactively:

```bash
python python_code_assistant.py
```

To analyze a file in one shot:

```bash
python python_code_assistant.py --file path/to/script.py
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

The interactive_snippet_assistant_v3_7.py script runs Python snippets in a
sandboxed subprocess with resource limits. Use it similarly to the code
assistant:

```bash
python interactive_snippet_assistant_v3_7.py --file my_script.py
```

You can also pipe code via standard input:

```bash
echo "print('hi')" | python interactive_snippet_assistant_v3_7.py
```

Use --stdin-data to pass input to the snippet and --timeout to control the
execution timeout. You can also change resource limits:

```
--cpu-seconds <N>  # CPU time limit (default 5 seconds)
--mem-mb <N>       # Memory limit in megabytes (default 128)
```

For example:

```bash
python interactive_snippet_assistant_v3_7.py --file script.py --cpu-seconds 10 --mem-mb 256
```
