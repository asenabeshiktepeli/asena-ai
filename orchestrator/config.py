"""Configuration module for the multi-agent orchestration pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class OpenDevinConfig:
    """Configuration for the OpenDevin (All Hands AI) agent."""

    image: str = "ghcr.io/all-hands-ai/openhands:main"
    container_name: str = "agent-factory-opendevin"
    workspace_mount: str = "/opt/workspace"
    port: int = 3000
    sandbox_type: str = "exec"
    llm_model: str = "gpt-4o"
    llm_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    max_iterations: int = 30
    timeout_seconds: int = 600


@dataclass
class SWEAgentConfig:
    """Configuration for the SWE-agent (Princeton) agent."""

    image: str = "sweagent/swe-agent:latest"
    container_name: str = "agent-factory-swe-agent"
    model: str = "gpt-4o"
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    per_instance_cost_limit: float = 3.0
    timeout_seconds: int = 600


@dataclass
class PipelineConfig:
    """Top-level configuration for the orchestration pipeline."""

    mode: Literal["live", "mock"] = "mock"
    workspace_dir: Path = field(
        default_factory=lambda: Path.home() / "agent-factory-workspace"
    )
    state_file: Path = field(
        default_factory=lambda: Path.home() / "agent-factory-workspace" / "state.json"
    )
    max_retries: int = 2
    opendevin: OpenDevinConfig = field(default_factory=OpenDevinConfig)
    swe_agent: SWEAgentConfig = field(default_factory=SWEAgentConfig)

    def __post_init__(self) -> None:
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> PipelineConfig:
        """Build config from environment variables with sensible defaults."""
        mode = os.getenv("AGENT_FACTORY_MODE", "mock")
        if mode not in ("live", "mock"):
            mode = "mock"
        return cls(
            mode=mode,  # type: ignore[arg-type]
            opendevin=OpenDevinConfig(
                llm_api_key=os.getenv("OPENAI_API_KEY", ""),
                llm_model=os.getenv("OPENDEVIN_MODEL", "gpt-4o"),
            ),
            swe_agent=SWEAgentConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model=os.getenv("SWE_AGENT_MODEL", "gpt-4o"),
            ),
        )
