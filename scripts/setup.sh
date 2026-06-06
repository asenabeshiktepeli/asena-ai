#!/usr/bin/env bash
# ============================================================
# setup.sh — Bootstrap the multi-agent orchestration environment
#
# Usage:
#   ./scripts/setup.sh          # mock mode (no Docker needed)
#   ./scripts/setup.sh --live   # pull Docker images for agents
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "  Multi-Agent Orchestration Pipeline — Setup"
echo "============================================================"

# ── 1. Python dependencies ───────────────────────────────────
echo ""
echo "[1/4] Installing Python dependencies …"
cd "$PROJECT_DIR"

if [ -f requirements.txt ]; then
    pip install -r requirements.txt --quiet 2>/dev/null || \
    pip3 install -r requirements.txt --quiet
    echo "      ✓ Python packages installed"
else
    echo "      ⚠ requirements.txt not found, skipping"
fi

# ── 2. Workspace directory ───────────────────────────────────
echo ""
echo "[2/4] Creating workspace directory …"
WORKSPACE="$HOME/agent-factory-workspace"
mkdir -p "$WORKSPACE"
echo "      ✓ $WORKSPACE"

# ── 3. Docker images (only in --live mode) ───────────────────
echo ""
if [[ "${1:-}" == "--live" ]]; then
    echo "[3/4] Pulling Docker images (live mode) …"

    if ! command -v docker &>/dev/null; then
        echo "      ✗ Docker is not installed. Please install Docker first."
        exit 1
    fi

    echo "      Pulling OpenDevin (OpenHands) …"
    docker pull ghcr.io/all-hands-ai/openhands:main
    echo "      ✓ OpenDevin image pulled"

    echo "      Pulling SWE-agent …"
    docker pull sweagent/swe-agent:latest
    echo "      ✓ SWE-agent image pulled"
else
    echo "[3/4] Skipping Docker pull (mock mode — pass --live to pull images)"
fi

# ── 4. Verify installation ───────────────────────────────────
echo ""
echo "[4/4] Verifying installation …"
cd "$PROJECT_DIR"
python3 -c "
from orchestrator.config import PipelineConfig
from orchestrator.pipeline import OrchestrationPipeline
from orchestrator.state import PipelineState, TaskStatus
print('      ✓ All modules import successfully')
print(f'      ✓ Default mode: {PipelineConfig.from_env().mode}')
"

echo ""
echo "============================================================"
echo "  Setup complete!"
echo ""
echo "  Quick start:"
echo "    python run_pipeline.py                     # success path"
echo "    python run_pipeline.py --simulate-failure   # handover path"
echo "    python run_pipeline.py -v                   # verbose logging"
echo "============================================================"
