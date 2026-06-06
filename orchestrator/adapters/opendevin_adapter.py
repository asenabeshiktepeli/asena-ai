"""Adapter for OpenDevin (All Hands AI / OpenHands).

Wraps the OpenDevin REST API (or CLI) behind a uniform interface so the
orchestrator can invoke it without knowing transport details.  In *mock*
mode every call returns a synthetic result for pipeline testing.
"""

from __future__ import annotations

import logging
import time
import traceback
from pathlib import Path
from typing import Optional

from orchestrator.config import PipelineConfig
from orchestrator.docker_manager import DockerManager
from orchestrator.state import AgentResult

logger = logging.getLogger(__name__)

# Simulated outputs used in mock mode
_MOCK_SUCCESS_OUTPUT = (
    "OpenDevin successfully built the project architecture.\n"
    "Created files: src/app.py, src/utils.py, tests/test_app.py\n"
    "All tests passed."
)

_MOCK_FAILURE_OUTPUT = (
    "OpenDevin attempted to build the project but encountered an error.\n"
    "File: target_repo/utils.py\n"
    "Error: TypeError – unsupported operand type(s) for +: 'int' and 'str'\n"
    "Traceback (most recent call last):\n"
    '  File "target_repo/utils.py", line 15, in calculate_total\n'
    "    return subtotal + tax_rate\n"
    "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
)


class OpenDevinAdapter:
    """Uniform interface to the OpenDevin coding agent."""

    def __init__(
        self,
        config: PipelineConfig,
        docker: DockerManager,
    ) -> None:
        self._config = config
        self._docker = docker
        self._mock = config.mode == "mock"

    def execute_task(
        self,
        task_description: str,
        repo_path: str,
        *,
        simulate_failure: bool = False,
    ) -> AgentResult:
        """Ask OpenDevin to work on *task_description* inside *repo_path*.

        Parameters
        ----------
        task_description:
            Natural-language description of the coding task.
        repo_path:
            Absolute path to the target repository on disk.
        simulate_failure:
            When ``True`` (only in mock mode) the adapter pretends that
            OpenDevin failed, so the handover path can be tested.

        Returns
        -------
        AgentResult with ``success=False`` when the agent could not solve
        the task, plus diagnostic fields the orchestrator uses to build
        a :class:`HandoverContext`.
        """
        start = time.time()

        if self._mock:
            return self._mock_execute(
                task_description, repo_path, simulate_failure=simulate_failure
            )

        return self._live_execute(task_description, repo_path)

    # ── Mock mode ────────────────────────────────────────────────

    def _mock_execute(
        self,
        task_description: str,
        repo_path: str,
        *,
        simulate_failure: bool = False,
    ) -> AgentResult:
        logger.info("[mock] OpenDevin executing task …")
        time.sleep(0.5)  # simulate latency

        if simulate_failure:
            logger.warning("[mock] OpenDevin encountered an error (simulated)")
            return AgentResult(
                agent_name="opendevin",
                success=False,
                output=_MOCK_FAILURE_OUTPUT,
                error=(
                    "TypeError: unsupported operand type(s) "
                    "for +: 'int' and 'str'"
                ),
                files_modified=["target_repo/utils.py"],
                duration_seconds=0.5,
                metadata={
                    "failing_file": "target_repo/utils.py",
                    "failing_line": 15,
                    "error_type": "TypeError",
                    "traceback": (
                        'File "target_repo/utils.py", line 15, in calculate_total\n'
                        "    return subtotal + tax_rate\n"
                        "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
                    ),
                },
            )

        logger.info("[mock] OpenDevin completed successfully")
        return AgentResult(
            agent_name="opendevin",
            success=True,
            output=_MOCK_SUCCESS_OUTPUT,
            files_modified=["src/app.py", "src/utils.py", "tests/test_app.py"],
            duration_seconds=0.5,
        )

    # ── Live mode ────────────────────────────────────────────────

    def _live_execute(
        self,
        task_description: str,
        repo_path: str,
    ) -> AgentResult:
        start = time.time()
        try:
            self._docker.start_opendevin(repo_path)

            # In a production setup this would call the OpenDevin REST API:
            #   POST http://localhost:{port}/api/submit
            #   { "task": task_description }
            # and poll until completion.  For now we shell out to the CLI.
            import subprocess

            result = subprocess.run(
                [
                    "docker", "exec",
                    self._config.opendevin.container_name,
                    "python", "-m", "openhands.core.main",
                    "-t", task_description,
                    "-d", self._config.opendevin.workspace_mount,
                ],
                capture_output=True,
                text=True,
                timeout=self._config.opendevin.timeout_seconds,
            )

            elapsed = time.time() - start
            success = result.returncode == 0

            return AgentResult(
                agent_name="opendevin",
                success=success,
                output=result.stdout,
                error=result.stderr if not success else "",
                duration_seconds=elapsed,
                metadata={"exit_code": result.returncode},
            )

        except Exception as exc:
            elapsed = time.time() - start
            logger.exception("OpenDevin live execution failed")
            return AgentResult(
                agent_name="opendevin",
                success=False,
                output="",
                error=str(exc),
                duration_seconds=elapsed,
                metadata={"traceback": traceback.format_exc()},
            )
