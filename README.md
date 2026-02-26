# NeuralOpenClaw

[![CI](https://github.com/linda-agi/neural-openclaw/actions/workflows/ci.yml/badge.svg)](https://github.com/linda-agi/neural-openclaw/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Integration of NeuralMemory with OpenClaw for intelligent episodic memory and token-efficient AI interactions.

## Overview

NeuralOpenClaw bridges OpenClaw's traditional memory system with NeuralMemory's graph-based episodic memory layer. This enables:

- **Smart caching** of tool results to avoid redundant calls
- **Session compression** to maintain context while saving tokens
- **Decision recall** for architectural and technical choices
- **Context assembly** optimized for token efficiency

## Features

- 🔧 **Neural Memory Layer**: Persistent episodic memory storage
- 🤖 **Smart Memory Router**: Intelligent query routing between memory types
- 📦 **Context Assembler**: Token-optimized context injection
- 🗃️ **Session Compressor**: Automatic history compression
- ⚡ **Tool Result Caching**: TTL-based caching with freshness rules
- 🛡️ **Privacy Safe**: Auto-redaction of sensitive data

## Installation

```bash
pip install neural-memory
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ OpenClaw Agent                                            │
├─────────────────────────────────────────────────────────────┤
│                                                           │
│ User Request → [SmartMemoryRouter]                        │
│                                                           │
│ ┌─────────────┴─────────────┐                             │
│ ▼                           ▼                             │
│ [NeuralMemory Layer]    [Traditional Memory]              │
│ • Decisions               • Documents / RAG               │
│ • Causal chains           • Code snippets                 │
│ • Tool result cache       • API references                │
│ • Project context         • Long-term facts               │
│ • Session episodics       • Vector search                 │
│                                                           │
│ └─────────────┬─────────────┘                             │
│               ▼                                           │
│ [ContextAssembler]                                        │
│ (score-based, only inject relevant)                       │
│                                                           │
│ ▼                                                         │
│ Prompt optimized for tokens → LLM Call                    │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### CLI Interface (like `qmd`)

```bash
# Initialize project
python nocl.py init --project my-project

# Store a decision
python nocl.py decision "Using SQLite" --context "Lightweight and portable"

# Store session context (expires in 12h)
python nocl.py context "Working on feature X" --expires 12

# Store insight/lesson
python nocl.py insight "Bug fixed: race condition in async code"

# Store fact (permanent or with expiry)
python nocl.py fact "API endpoint: https://api.example.com" --expires 24

# Cache tool result
python nocl.py cache read_file '{"path": "config.json"}' '{"key": "value"}' --ttl 2

# Recall information
python nocl.py recall "Why did we choose SQLite?" --confidence 0.7 --depth 2

# Get task-optimized context
python nocl.py task "Implement caching layer" --max-tokens 800

# Show status
python nocl.py status --project my-project
```

### Python API Integration

```python
from neural_openclaw import NeuralMemoryLayer, SmartMemoryRouter

# Initialize
memory = NeuralMemoryLayer(project_name="my-project")

# Store a decision
await memory.store_decision(
    "Using SQLite for episodic memory", 
    "Because it's lightweight and portable"
)

# Cache a tool result
await memory.cache_tool_result(
    "read_file", 
    {"path": "config.json"}, 
    '{"api_key": "..."',
    ttl_hours=1
)

# Recall information
context = await memory.recall("Why did we choose SQLite?")
```

## Configuration

See `config/memory_config.yaml` for adjustable parameters.

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/linda-agi/neural-openclaw.git
cd neural-openclaw

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
pytest tests/test_core.py -v

# Run specific test class
pytest tests/test_core.py::TestSmartMemoryRouter -v
```

### Code Quality

```bash
# Lint with flake8
flake8 src tests

# Format with black
black src tests

# Sort imports with isort
isort src tests

# Type check with mypy
mypy src
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Ensure all tests pass (`pytest`)
6. Run linter (`flake8`)
7. Submit a pull request

### CI/CD

This project uses GitHub Actions for continuous integration. Every push and pull request automatically triggers:
- ✅ Python syntax validation
- ✅ Unit tests with pytest
- ✅ CLI command tests
- ✅ Code linting with flake8
- ✅ Security checks with safety

## License

MIT