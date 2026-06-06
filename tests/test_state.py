"""Tests for the pipeline state module."""

import json
import tempfile
from pathlib import Path

from orchestrator.state import (
    AgentResult,
    HandoverContext,
    PipelineState,
    TaskStatus,
)


def test_state_creation() -> None:
    state = PipelineState(
        task_id="test-001",
        task_description="Fix a bug",
        target_repo="/tmp/repo",
    )
    assert state.status == TaskStatus.PENDING
    assert state.task_id == "test-001"
    assert state.opendevin_result is None


def test_state_transition() -> None:
    state = PipelineState(task_id="test-002", task_description="test")
    state.transition(TaskStatus.OPENDEVIN_RUNNING, "starting")
    assert state.status == TaskStatus.OPENDEVIN_RUNNING
    assert len(state.history) == 1
    assert state.history[0]["from"] == "pending"
    assert state.history[0]["to"] == "opendevin_running"
    assert state.history[0]["note"] == "starting"


def test_state_save_and_load(tmp_path: Path) -> None:
    state = PipelineState(
        task_id="test-003",
        task_description="roundtrip test",
        target_repo="/tmp/repo",
    )
    state.opendevin_result = AgentResult(
        agent_name="opendevin",
        success=False,
        output="failed output",
        error="TypeError",
    )
    state.handover_context = HandoverContext(
        failing_file="utils.py",
        error_type="TypeError",
        traceback="line 15",
        task_description="roundtrip test",
    )
    state.transition(TaskStatus.OPENDEVIN_FAILED, "test fail")

    path = tmp_path / "state.json"
    state.save(path)
    assert path.exists()

    loaded = PipelineState.load(path)
    assert loaded.task_id == "test-003"
    assert loaded.status == TaskStatus.OPENDEVIN_FAILED
    assert loaded.opendevin_result is not None
    assert loaded.opendevin_result.agent_name == "opendevin"
    assert loaded.handover_context is not None
    assert loaded.handover_context.failing_file == "utils.py"
    assert len(loaded.history) == 1


def test_state_to_json() -> None:
    state = PipelineState(task_id="test-004", task_description="json test")
    raw = state.to_json()
    parsed = json.loads(raw)
    assert parsed["task_id"] == "test-004"
    assert parsed["status"] == "pending"
