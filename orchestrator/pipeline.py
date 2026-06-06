"""Central orchestration pipeline.

Coordinates the multi-agent workflow:

1. Create a shared :class:`PipelineState`.
2. Invoke **OpenDevin** to build / solve the task.
3. If OpenDevin succeeds → mark COMPLETED.
4. If OpenDevin fails → extract :class:`HandoverContext`, transition to
   HANDOVER, and invoke **SWE-agent** to deep-debug the specific failure.
5. If SWE-agent succeeds → COMPLETED.  Otherwise → FAILED.

All transitions are recorded in ``state.history`` and the state JSON is
persisted after every step for crash recovery.
"""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

from orchestrator.adapters.opendevin_adapter import OpenDevinAdapter
from orchestrator.adapters.swe_agent_adapter import SWEAgentAdapter
from orchestrator.config import PipelineConfig
from orchestrator.docker_manager import DockerManager
from orchestrator.state import (
    AgentResult,
    HandoverContext,
    PipelineState,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class OrchestrationPipeline:
    """Event-driven multi-agent orchestrator."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self._config = config or PipelineConfig.from_env()
        self._docker = DockerManager(self._config)
        self._opendevin = OpenDevinAdapter(self._config, self._docker)
        self._swe_agent = SWEAgentAdapter(self._config, self._docker)

    # ── Public API ───────────────────────────────────────────────

    def run(
        self,
        task_description: str,
        target_repo: str,
        *,
        simulate_failure: bool = False,
    ) -> PipelineState:
        """Execute the full pipeline for a single task.

        Parameters
        ----------
        task_description:
            Natural-language description of the coding task.
        target_repo:
            Absolute path to the target repository.
        simulate_failure:
            When ``True`` the OpenDevin adapter will pretend to fail so
            the handover to SWE-agent can be tested end-to-end.
        """
        state = self._init_state(task_description, target_repo)
        logger.info(
            "Pipeline started  task_id=%s  mode=%s",
            state.task_id,
            self._config.mode,
        )
        self._persist(state)

        # ── Step 1: OpenDevin ────────────────────────────────────
        state = self._run_opendevin(state, simulate_failure=simulate_failure)
        self._persist(state)

        if state.status == TaskStatus.OPENDEVIN_SUCCESS:
            state.transition(TaskStatus.COMPLETED, "OpenDevin solved the task")
            self._persist(state)
            self._log_summary(state)
            return state

        # ── Step 2: Handover ─────────────────────────────────────
        state = self._build_handover(state)
        self._persist(state)

        # ── Step 3: SWE-agent ────────────────────────────────────
        state = self._run_swe_agent(state)
        self._persist(state)

        if state.status == TaskStatus.SWE_AGENT_SUCCESS:
            state.transition(TaskStatus.COMPLETED, "SWE-agent patched the issue")
        else:
            state.transition(
                TaskStatus.FAILED,
                "Both agents failed to resolve the task",
            )

        self._persist(state)
        self._log_summary(state)
        return state

    # ── Internal steps ───────────────────────────────────────────

    def _init_state(
        self,
        task_description: str,
        target_repo: str,
    ) -> PipelineState:
        return PipelineState(
            task_id=uuid.uuid4().hex[:12],
            task_description=task_description,
            target_repo=target_repo,
            status=TaskStatus.PENDING,
        )

    def _run_opendevin(
        self,
        state: PipelineState,
        *,
        simulate_failure: bool = False,
    ) -> PipelineState:
        state.transition(TaskStatus.OPENDEVIN_RUNNING, "Invoking OpenDevin")
        logger.info("Invoking OpenDevin …")

        result = self._opendevin.execute_task(
            task_description=state.task_description,
            repo_path=state.target_repo,
            simulate_failure=simulate_failure,
        )
        state.opendevin_result = result

        if result.success:
            state.transition(TaskStatus.OPENDEVIN_SUCCESS, "OpenDevin succeeded")
            logger.info("OpenDevin succeeded in %.1fs", result.duration_seconds)
        else:
            state.transition(
                TaskStatus.OPENDEVIN_FAILED,
                f"OpenDevin failed: {result.error[:200]}",
            )
            logger.warning("OpenDevin failed: %s", result.error[:200])

        return state

    def _build_handover(self, state: PipelineState) -> PipelineState:
        """Extract context from OpenDevin's failure for SWE-agent."""
        state.transition(TaskStatus.HANDOVER, "Building handover context")
        result = state.opendevin_result
        if result is None:
            raise RuntimeError("Cannot build handover without an OpenDevin result")

        meta = result.metadata or {}
        handover = HandoverContext(
            failing_file=meta.get("failing_file", self._extract_file(result.output)),
            error_type=meta.get("error_type", self._extract_error_type(result.error)),
            traceback=meta.get("traceback", result.error),
            task_description=state.task_description,
            attempted_fix=result.output,
        )
        state.handover_context = handover
        logger.info(
            "Handover context built  file=%s  error=%s",
            handover.failing_file,
            handover.error_type,
        )
        return state

    def _run_swe_agent(self, state: PipelineState) -> PipelineState:
        state.transition(TaskStatus.SWE_AGENT_RUNNING, "Invoking SWE-agent")
        logger.info("Invoking SWE-agent for deep debugging …")

        if state.handover_context is None:
            raise RuntimeError("Cannot run SWE-agent without handover context")

        result = self._swe_agent.debug_and_patch(
            handover=state.handover_context,
            repo_path=state.target_repo,
        )
        state.swe_agent_result = result

        if result.success:
            state.transition(TaskStatus.SWE_AGENT_SUCCESS, "SWE-agent patched it")
            logger.info("SWE-agent resolved the issue in %.1fs", result.duration_seconds)
        else:
            state.transition(
                TaskStatus.SWE_AGENT_FAILED,
                f"SWE-agent failed: {result.error[:200]}",
            )
            logger.warning("SWE-agent failed: %s", result.error[:200])

        return state

    # ── Helpers ──────────────────────────────────────────────────

    def _persist(self, state: PipelineState) -> None:
        state.save(self._config.state_file)

    @staticmethod
    def _extract_file(output: str) -> str:
        """Best-effort extraction of a file path from agent output."""
        match = re.search(r"File[:\s]+([^\s,]+\.py)", output)
        return match.group(1) if match else ""

    @staticmethod
    def _extract_error_type(error: str) -> str:
        """Best-effort extraction of Python exception type."""
        match = re.search(r"(\w+Error|\w+Exception)", error)
        return match.group(1) if match else "UnknownError"

    @staticmethod
    def _log_summary(state: PipelineState) -> None:
        border = "=" * 60
        logger.info("\n%s", border)
        logger.info("PIPELINE SUMMARY")
        logger.info("%s", border)
        logger.info("Task ID      : %s", state.task_id)
        logger.info("Final Status : %s", state.status.value)
        if state.opendevin_result:
            r = state.opendevin_result
            logger.info(
                "OpenDevin    : %s  (%.1fs)",
                "SUCCESS" if r.success else "FAILED",
                r.duration_seconds,
            )
        if state.swe_agent_result:
            r = state.swe_agent_result
            logger.info(
                "SWE-agent    : %s  (%.1fs)",
                "SUCCESS" if r.success else "FAILED",
                r.duration_seconds,
            )
        logger.info("History      : %d transitions", len(state.history))
        logger.info("%s\n", border)
