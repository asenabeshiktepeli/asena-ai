"""Shared JSON state schema and persistence for the orchestration pipeline.

The pipeline state is a single JSON document that flows through every stage.
Each agent adapter reads from and writes to this state, making the entire
pipeline inspectable and recoverable.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class TaskStatus(str, Enum):
    """Lifecycle status of a pipeline task."""

    PENDING = "pending"
    OPENDEVIN_RUNNING = "opendevin_running"
    OPENDEVIN_SUCCESS = "opendevin_success"
    OPENDEVIN_FAILED = "opendevin_failed"
    HANDOVER = "handover"
    SWE_AGENT_RUNNING = "swe_agent_running"
    SWE_AGENT_SUCCESS = "swe_agent_success"
    SWE_AGENT_FAILED = "swe_agent_failed"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentResult:
    """Outcome produced by a single agent invocation."""

    agent_name: str = ""
    success: bool = False
    output: str = ""
    error: str = ""
    files_modified: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HandoverContext:
    """Context extracted on failure to pass to the next agent."""

    failing_file: str = ""
    error_type: str = ""
    traceback: str = ""
    task_description: str = ""
    attempted_fix: str = ""


@dataclass
class PipelineState:
    """Top-level shared state for one pipeline run."""

    task_id: str = ""
    task_description: str = ""
    target_repo: str = ""
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    opendevin_result: Optional[AgentResult] = None
    handover_context: Optional[HandoverContext] = None
    swe_agent_result: Optional[AgentResult] = None

    history: list[dict[str, Any]] = field(default_factory=list)

    # ── Persistence ──────────────────────────────────────────────

    def save(self, path: Path) -> None:
        """Persist state to a JSON file."""
        self.updated_at = time.time()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2, default=str))

    @classmethod
    def load(cls, path: Path) -> PipelineState:
        """Load state from a JSON file."""
        raw = json.loads(path.read_text())
        raw["status"] = TaskStatus(raw["status"])
        if raw.get("opendevin_result"):
            raw["opendevin_result"] = AgentResult(**raw["opendevin_result"])
        if raw.get("handover_context"):
            raw["handover_context"] = HandoverContext(**raw["handover_context"])
        if raw.get("swe_agent_result"):
            raw["swe_agent_result"] = AgentResult(**raw["swe_agent_result"])
        return cls(**raw)

    # ── Convenience ──────────────────────────────────────────────

    def transition(self, new_status: TaskStatus, note: str = "") -> None:
        """Record a status transition in the history log."""
        self.history.append(
            {
                "from": self.status.value,
                "to": new_status.value,
                "timestamp": time.time(),
                "note": note,
            }
        )
        self.status = new_status
        self.updated_at = time.time()

    def to_json(self) -> str:
        """Serialize to a pretty-printed JSON string."""
        return json.dumps(asdict(self), indent=2, default=str)
