"""Tests for the orchestration pipeline (mock mode only)."""

import json
from pathlib import Path

from orchestrator.config import PipelineConfig
from orchestrator.pipeline import OrchestrationPipeline
from orchestrator.state import TaskStatus


def _make_pipeline(tmp_path: Path) -> OrchestrationPipeline:
    config = PipelineConfig(
        mode="mock",
        workspace_dir=tmp_path / "workspace",
        state_file=tmp_path / "workspace" / "state.json",
    )
    return OrchestrationPipeline(config)


def test_pipeline_success_path(tmp_path: Path) -> None:
    """When OpenDevin succeeds, SWE-agent should NOT be invoked."""
    pipeline = _make_pipeline(tmp_path)
    state = pipeline.run(
        task_description="Build a hello world app",
        target_repo="/tmp/repo",
        simulate_failure=False,
    )
    assert state.status == TaskStatus.COMPLETED
    assert state.opendevin_result is not None
    assert state.opendevin_result.success is True
    assert state.swe_agent_result is None  # never invoked
    assert state.handover_context is None


def test_pipeline_handover_path(tmp_path: Path) -> None:
    """When OpenDevin fails, the pipeline should hand over to SWE-agent."""
    pipeline = _make_pipeline(tmp_path)
    state = pipeline.run(
        task_description="Fix the TypeError in utils.py",
        target_repo="/tmp/repo",
        simulate_failure=True,
    )
    assert state.status == TaskStatus.COMPLETED
    # OpenDevin should have failed
    assert state.opendevin_result is not None
    assert state.opendevin_result.success is False
    # Handover context should be populated
    assert state.handover_context is not None
    assert state.handover_context.failing_file == "target_repo/utils.py"
    assert state.handover_context.error_type == "TypeError"
    # SWE-agent should have succeeded
    assert state.swe_agent_result is not None
    assert state.swe_agent_result.success is True


def test_pipeline_state_persistence(tmp_path: Path) -> None:
    """Pipeline state should be persisted to disk after every step."""
    pipeline = _make_pipeline(tmp_path)
    pipeline.run(
        task_description="test persistence",
        target_repo="/tmp/repo",
        simulate_failure=True,
    )
    state_file = tmp_path / "workspace" / "state.json"
    assert state_file.exists()
    data = json.loads(state_file.read_text())
    assert data["task_description"] == "test persistence"
    assert data["status"] == "completed"
    assert len(data["history"]) > 0


def test_pipeline_history_records_all_transitions(tmp_path: Path) -> None:
    """The history log should capture every status transition."""
    pipeline = _make_pipeline(tmp_path)
    state = pipeline.run(
        task_description="history test",
        target_repo="/tmp/repo",
        simulate_failure=True,
    )
    statuses = [h["to"] for h in state.history]
    assert "opendevin_running" in statuses
    assert "opendevin_failed" in statuses
    assert "handover" in statuses
    assert "swe_agent_running" in statuses
    assert "completed" in statuses
