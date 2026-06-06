# Multi-Agent Orchestration Pipeline

An autonomous AI multi-agent factory that orchestrates **OpenDevin (All Hands AI)** and **SWE-agent (Princeton NLP)** in an automated pipeline. When one agent fails, the system catches the error, extracts context, and hands over to the next agent for deep debugging.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Pipeline                       │
│                                                                 │
│  ┌──────────┐     ┌───────────────┐     ┌───────────────────┐  │
│  │  Shared   │────▶│   OpenDevin   │────▶│  Success? Done!   │  │
│  │  JSON     │     │  (Build/Fix)  │     └───────────────────┘  │
│  │  State    │     └───────┬───────┘                            │
│  │           │             │ FAILURE                             │
│  │           │     ┌───────▼───────┐                            │
│  │           │◀────│   Handover    │  Extract: file, error,     │
│  │           │     │   Context     │  traceback, task desc      │
│  │           │     └───────┬───────┘                            │
│  │           │             │                                    │
│  │           │     ┌───────▼───────┐     ┌───────────────────┐  │
│  │           │────▶│   SWE-agent   │────▶│  Patched! Done!   │  │
│  └──────────┘     │ (Deep Debug)  │     └───────────────────┘  │
│                    └───────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
agent-factory/
├── orchestrator/
│   ├── __init__.py
│   ├── config.py              # Dataclass-based configuration
│   ├── state.py               # Shared JSON state schema + persistence
│   ├── pipeline.py            # Central orchestration logic
│   ├── docker_manager.py      # Docker container lifecycle manager
│   └── adapters/
│       ├── __init__.py
│       ├── opendevin_adapter.py   # OpenDevin CLI/API wrapper
│       └── swe_agent_adapter.py   # SWE-agent CLI/API wrapper
├── target_repo/               # Dummy repo with a deliberate bug
│   ├── app.py                 # Entry point (passes str as tax_rate)
│   ├── utils.py               # BUG: arithmetic on string type
│   └── test_utils.py          # Tests that fail until bug is fixed
├── tests/                     # Pipeline unit tests
│   ├── test_state.py          # State serialization & transitions
│   ├── test_pipeline.py       # End-to-end pipeline (mock mode)
│   └── test_adapters.py       # Individual adapter tests
├── scripts/
│   └── setup.sh               # Environment bootstrap script
├── run_pipeline.py            # CLI entry point
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Setup

```bash
# Clone and install
git clone https://github.com/asenabeshiktepeli/asena-ai.git
cd asena-ai

# Install dependencies
pip install -r requirements.txt

# Or use the setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 2. Run in Mock Mode (no Docker or API keys needed)

```bash
# Happy path — OpenDevin succeeds, pipeline completes
python run_pipeline.py

# Failure path — OpenDevin fails, hands over to SWE-agent
python run_pipeline.py --simulate-failure

# Verbose logging
python run_pipeline.py --simulate-failure -v
```

### 3. Run Tests

```bash
pytest tests/ -v
```

### 4. Run in Live Mode (requires Docker + API key)

```bash
# Pull agent Docker images
./scripts/setup.sh --live

# Run with real agents
AGENT_FACTORY_MODE=live OPENAI_API_KEY=sk-... python run_pipeline.py
```

## How It Works

### Pipeline Flow

1. **Task Submission** — A coding task is submitted via CLI or API
2. **State Initialization** — A shared JSON state document is created with a unique task ID
3. **OpenDevin Phase** — The pipeline invokes OpenDevin to build/fix the project
4. **Error Detection** — If OpenDevin fails, the pipeline catches the error and extracts:
   - Failing file path
   - Error type (e.g., `TypeError`, `ValueError`)
   - Full traceback
   - Original task description
5. **Handover** — Context is packaged into a `HandoverContext` object
6. **SWE-agent Phase** — SWE-agent receives the context and deep-debugs the specific file
7. **Resolution** — The pipeline reports success/failure with full audit trail

### Shared JSON State

Every pipeline run produces a persistent JSON state file:

```json
{
  "task_id": "a1b2c3d4e5f6",
  "task_description": "Fix the TypeError in utils.py",
  "status": "completed",
  "opendevin_result": {
    "agent_name": "opendevin",
    "success": false,
    "error": "TypeError: unsupported operand type(s)..."
  },
  "handover_context": {
    "failing_file": "target_repo/utils.py",
    "error_type": "TypeError",
    "traceback": "..."
  },
  "swe_agent_result": {
    "agent_name": "swe-agent",
    "success": true,
    "output": "Patch applied..."
  },
  "history": [
    {"from": "pending", "to": "opendevin_running", "timestamp": 1234567890},
    {"from": "opendevin_running", "to": "opendevin_failed", "timestamp": 1234567891},
    {"from": "opendevin_failed", "to": "handover", "timestamp": 1234567892},
    {"from": "handover", "to": "swe_agent_running", "timestamp": 1234567893},
    {"from": "swe_agent_running", "to": "completed", "timestamp": 1234567894}
  ]
}
```

### The Deliberate Bug (target_repo)

The `target_repo/` directory contains a Python project with an intentional `TypeError`:

```python
# target_repo/utils.py — line 30
def calculate_total(subtotal: int, tax_rate: str) -> float:
    return subtotal + subtotal * tax_rate  # BUG: tax_rate is a string!
```

The pipeline detects this failure, extracts the context, and SWE-agent patches it to:

```python
    return subtotal + subtotal * float(tax_rate)  # Fixed
```

## Configuration

All configuration is driven by environment variables and dataclass defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_FACTORY_MODE` | `mock` | `mock` for testing, `live` for real agents |
| `OPENAI_API_KEY` | — | Required for live mode |
| `OPENDEVIN_MODEL` | `gpt-4o` | LLM model for OpenDevin |
| `SWE_AGENT_MODEL` | `gpt-4o` | LLM model for SWE-agent |

## Technologies

- **Python 3.11+** — Type hints, dataclasses, enums
- **Docker** — Container orchestration for agent runtimes
- **OpenDevin / OpenHands** — AI coding agent (architecture building)
- **SWE-agent** — AI debugging agent (deep patching)
- **pytest** — Unit and integration testing

## Roadmap

- [ ] Add LangGraph-based workflow for complex multi-step tasks
- [ ] Support additional agents (Aider, Cursor, etc.)
- [ ] Web dashboard for pipeline monitoring
- [ ] Webhook integration for GitHub Issues → automatic agent dispatch
- [ ] Parallel agent execution with voting/consensus
