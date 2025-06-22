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
