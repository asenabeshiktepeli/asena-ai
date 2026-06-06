"""Docker container lifecycle manager for OpenDevin and SWE-agent.

Provides helpers to pull images, start/stop containers, and stream logs.
In mock mode every operation is a no-op that returns synthetic success.
"""

from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

from orchestrator.config import OpenDevinConfig, PipelineConfig, SWEAgentConfig

logger = logging.getLogger(__name__)


@dataclass
class ContainerStatus:
    """Snapshot of a Docker container's state."""

    name: str
    running: bool
    image: str
    ports: dict[str, str]
    started_at: Optional[float] = None


class DockerManager:
    """Manage Docker containers for the agent pipeline."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config
        self._mock = config.mode == "mock"

    # ── Public API ───────────────────────────────────────────────

    def pull_images(self) -> None:
        """Pull the latest images for both agents."""
        if self._mock:
            logger.info("[mock] Skipping docker pull")
            return
        for img in (self._config.opendevin.image, self._config.swe_agent.image):
            logger.info("Pulling %s …", img)
            self._run(["docker", "pull", img])

    def start_opendevin(self, workspace_path: str) -> ContainerStatus:
        """Start the OpenDevin container."""
        cfg = self._config.opendevin
        if self._mock:
            logger.info("[mock] OpenDevin container started")
            return ContainerStatus(
                name=cfg.container_name,
                running=True,
                image=cfg.image,
                ports={"3000": "3000"},
                started_at=time.time(),
            )

        self._stop_if_running(cfg.container_name)
        cmd = [
            "docker", "run", "-d",
            "--name", cfg.container_name,
            "-p", f"{cfg.port}:3000",
            "-v", f"{workspace_path}:{cfg.workspace_mount}",
            "-e", f"LLM_API_KEY={cfg.llm_api_key}",
            "-e", f"LLM_MODEL={cfg.llm_model}",
            "-e", f"SANDBOX_TYPE={cfg.sandbox_type}",
            cfg.image,
        ]
        self._run(cmd)
        logger.info("OpenDevin container started on port %d", cfg.port)
        return ContainerStatus(
            name=cfg.container_name,
            running=True,
            image=cfg.image,
            ports={str(cfg.port): "3000"},
            started_at=time.time(),
        )

    def run_swe_agent(
        self,
        repo_path: str,
        problem_statement: str,
    ) -> str:
        """Run SWE-agent against a target repo and return its stdout output."""
        cfg = self._config.swe_agent
        if self._mock:
            logger.info("[mock] SWE-agent run completed")
            return (
                "[mock] SWE-agent analysed the repository and applied a patch.\n"
                "Files modified: target_repo/utils.py\n"
                "Status: RESOLVED"
            )

        cmd = [
            "docker", "run", "--rm",
            "--name", cfg.container_name,
            "-v", f"{repo_path}:/repo",
            "-e", f"OPENAI_API_KEY={cfg.api_key}",
            cfg.image,
            "python", "run.py",
            "--model_name", cfg.model,
            "--data_path", "/repo",
            "--per_instance_cost_limit", str(cfg.per_instance_cost_limit),
            "--problem_statement", problem_statement,
        ]
        result = self._run(cmd, capture=True)
        return result

    def stop_all(self) -> None:
        """Stop and remove all agent containers."""
        if self._mock:
            logger.info("[mock] All containers stopped")
            return
        for name in (
            self._config.opendevin.container_name,
            self._config.swe_agent.container_name,
        ):
            self._stop_if_running(name)

    def status(self, container_name: str) -> ContainerStatus:
        """Check the current status of a container."""
        if self._mock:
            return ContainerStatus(
                name=container_name,
                running=True,
                image="mock",
                ports={},
            )
        running = self._is_running(container_name)
        return ContainerStatus(
            name=container_name,
            running=running,
            image="",
            ports={},
        )

    # ── Internals ────────────────────────────────────────────────

    def _run(
        self,
        cmd: list[str],
        *,
        capture: bool = False,
    ) -> str:
        logger.debug("Running: %s", " ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self._config.opendevin.timeout_seconds,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Command failed ({result.returncode}): {result.stderr.strip()}"
            )
        return result.stdout if capture else ""

    def _is_running(self, name: str) -> bool:
        try:
            out = self._run(
                ["docker", "inspect", "-f", "{{.State.Running}}", name],
                capture=True,
            )
            return out.strip().lower() == "true"
        except (RuntimeError, FileNotFoundError):
            return False

    def _stop_if_running(self, name: str) -> None:
        if self._is_running(name):
            logger.info("Stopping container %s", name)
            subprocess.run(
                ["docker", "rm", "-f", name],
                capture_output=True,
                timeout=30,
            )
