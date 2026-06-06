"""Adapter for SWE-agent (Princeton NLP).

Wraps the SWE-agent CLI behind a uniform interface.  In *mock* mode
every call returns a synthetic patch result for pipeline testing.
"""

from __future__ import annotations

import logging
import time
import traceback
from pathlib import Path

from orchestrator.config import PipelineConfig
from orchestrator.docker_manager import DockerManager
from orchestrator.state import AgentResult, HandoverContext

logger = logging.getLogger(__name__)

_MOCK_PATCH = '''\
--- a/target_repo/utils.py
+++ b/target_repo/utils.py
@@ -13,5 +13,5 @@
 def calculate_total(subtotal: int, tax_rate: str) -> float:
     """Calculate total with tax."""
-    return subtotal + tax_rate
+    return subtotal + float(tax_rate)
'''

_MOCK_OUTPUT = (
    "SWE-agent deep-debug session completed.\n"
    "Root cause: `tax_rate` parameter is a str but used in arithmetic.\n"
    "Fix: cast `tax_rate` to float before addition.\n"
    "Patch applied to target_repo/utils.py\n"
    "Status: RESOLVED"
)


class SWEAgentAdapter:
    """Uniform interface to the SWE-agent deep-debugging agent."""

    def __init__(
        self,
        config: PipelineConfig,
        docker: DockerManager,
    ) -> None:
        self._config = config
        self._docker = docker
        self._mock = config.mode == "mock"

    def debug_and_patch(
        self,
        handover: HandoverContext,
        repo_path: str,
    ) -> AgentResult:
        """Invoke SWE-agent to debug and patch the issue described in *handover*.

        Parameters
        ----------
        handover:
            Context extracted from the previous agent's failure —
            includes the failing file, error type, traceback, and
            original task description.
        repo_path:
            Absolute path to the target repository.

        Returns
        -------
        AgentResult describing whether SWE-agent resolved the issue.
        """
        start = time.time()

        if self._mock:
            return self._mock_debug(handover)

        return self._live_debug(handover, repo_path)

    # ── Mock mode ────────────────────────────────────────────────

    def _mock_debug(self, handover: HandoverContext) -> AgentResult:
        logger.info("[mock] SWE-agent deep-debugging …")
        time.sleep(0.5)

        logger.info("[mock] SWE-agent resolved the issue")
        return AgentResult(
            agent_name="swe-agent",
            success=True,
            output=_MOCK_OUTPUT,
            files_modified=[handover.failing_file or "target_repo/utils.py"],
            duration_seconds=0.5,
            metadata={
                "patch": _MOCK_PATCH,
                "root_cause": "type mismatch — str used in int arithmetic",
                "resolution": "cast tax_rate to float",
            },
        )

    # ── Live mode ────────────────────────────────────────────────

    def _live_debug(
        self,
        handover: HandoverContext,
        repo_path: str,
    ) -> AgentResult:
        start = time.time()
        problem_statement = self._build_problem_statement(handover)

        try:
            output = self._docker.run_swe_agent(
                repo_path=repo_path,
                problem_statement=problem_statement,
            )

            elapsed = time.time() - start
            resolved = "RESOLVED" in output.upper() or "PATCH APPLIED" in output.upper()

            return AgentResult(
                agent_name="swe-agent",
                success=resolved,
                output=output,
                error="" if resolved else "SWE-agent could not resolve the issue",
                duration_seconds=elapsed,
                metadata={"problem_statement": problem_statement},
            )

        except Exception as exc:
            elapsed = time.time() - start
            logger.exception("SWE-agent live execution failed")
            return AgentResult(
                agent_name="swe-agent",
                success=False,
                output="",
                error=str(exc),
                duration_seconds=elapsed,
                metadata={"traceback": traceback.format_exc()},
            )

    @staticmethod
    def _build_problem_statement(ctx: HandoverContext) -> str:
        """Compose a natural-language problem statement for SWE-agent."""
        parts = [
            f"Task: {ctx.task_description}",
            f"\nThe previous agent attempted this task but failed.",
            f"\nFailing file: {ctx.failing_file}",
            f"Error type: {ctx.error_type}",
        ]
        if ctx.traceback:
            parts.append(f"\nTraceback:\n{ctx.traceback}")
        if ctx.attempted_fix:
            parts.append(f"\nPrevious attempted fix:\n{ctx.attempted_fix}")
        parts.append(
            "\nPlease analyse the root cause, apply a minimal fix, "
            "and verify that the issue is resolved."
        )
        return "\n".join(parts)
