"""Tests for individual agent adapters (mock mode)."""

from pathlib import Path

from orchestrator.adapters.opendevin_adapter import OpenDevinAdapter
from orchestrator.adapters.swe_agent_adapter import SWEAgentAdapter
from orchestrator.config import PipelineConfig
from orchestrator.docker_manager import DockerManager
from orchestrator.state import HandoverContext


def _mock_config(tmp_path: Path) -> PipelineConfig:
    return PipelineConfig(
        mode="mock",
        workspace_dir=tmp_path / "workspace",
        state_file=tmp_path / "workspace" / "state.json",
    )


def test_opendevin_mock_success(tmp_path: Path) -> None:
    config = _mock_config(tmp_path)
    docker = DockerManager(config)
    adapter = OpenDevinAdapter(config, docker)
    result = adapter.execute_task(
        task_description="Build an app",
        repo_path="/tmp/repo",
        simulate_failure=False,
    )
    assert result.success is True
    assert result.agent_name == "opendevin"
    assert len(result.files_modified) > 0


def test_opendevin_mock_failure(tmp_path: Path) -> None:
    config = _mock_config(tmp_path)
    docker = DockerManager(config)
    adapter = OpenDevinAdapter(config, docker)
    result = adapter.execute_task(
        task_description="Build an app",
        repo_path="/tmp/repo",
        simulate_failure=True,
    )
    assert result.success is False
    assert "TypeError" in result.error
    assert result.metadata.get("failing_file") == "target_repo/utils.py"


def test_swe_agent_mock_success(tmp_path: Path) -> None:
    config = _mock_config(tmp_path)
    docker = DockerManager(config)
    adapter = SWEAgentAdapter(config, docker)
    handover = HandoverContext(
        failing_file="target_repo/utils.py",
        error_type="TypeError",
        traceback="line 15",
        task_description="Fix the bug",
    )
    result = adapter.debug_and_patch(handover, repo_path="/tmp/repo")
    assert result.success is True
    assert result.agent_name == "swe-agent"
    assert "target_repo/utils.py" in result.files_modified
    assert "patch" in result.metadata


def test_swe_agent_builds_problem_statement(tmp_path: Path) -> None:
    handover = HandoverContext(
        failing_file="utils.py",
        error_type="ValueError",
        traceback="Traceback ...",
        task_description="Fix the value error",
        attempted_fix="tried casting",
    )
    stmt = SWEAgentAdapter._build_problem_statement(handover)
    assert "Fix the value error" in stmt
    assert "ValueError" in stmt
    assert "Traceback" in stmt
    assert "tried casting" in stmt
