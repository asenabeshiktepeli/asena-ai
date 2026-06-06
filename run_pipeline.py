#!/usr/bin/env python3
"""Entry point for the multi-agent orchestration pipeline.

Usage
-----
Mock mode (default — no Docker or API keys needed):

    python run_pipeline.py

    # Simulate OpenDevin failure + handover to SWE-agent:
    python run_pipeline.py --simulate-failure

Live mode (requires Docker + OPENAI_API_KEY):

    AGENT_FACTORY_MODE=live OPENAI_API_KEY=sk-... python run_pipeline.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from orchestrator.config import PipelineConfig
from orchestrator.pipeline import OrchestrationPipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the multi-agent orchestration pipeline.",
    )
    parser.add_argument(
        "--simulate-failure",
        action="store_true",
        help="Force OpenDevin to fail so the handover to SWE-agent is tested.",
    )
    parser.add_argument(
        "--task",
        default=(
            "Fix the TypeError in target_repo/utils.py where calculate_total "
            "performs arithmetic on a string tax_rate parameter."
        ),
        help="Task description to send to the agents.",
    )
    parser.add_argument(
        "--repo",
        default=str(Path(__file__).resolve().parent / "target_repo"),
        help="Absolute path to the target repository.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG logging.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    config = PipelineConfig.from_env()
    pipeline = OrchestrationPipeline(config)

    print(f"\n{'='*60}")
    print(f"  Multi-Agent Orchestration Pipeline")
    print(f"  Mode: {config.mode.upper()}")
    print(f"  Task: {args.task[:80]}…" if len(args.task) > 80 else f"  Task: {args.task}")
    print(f"  Repo: {args.repo}")
    print(f"  Simulate failure: {args.simulate_failure}")
    print(f"{'='*60}\n")

    state = pipeline.run(
        task_description=args.task,
        target_repo=args.repo,
        simulate_failure=args.simulate_failure,
    )

    print(f"\n{'='*60}")
    print("  FINAL STATE")
    print(f"{'='*60}")
    print(json.dumps(json.loads(state.to_json()), indent=2))


if __name__ == "__main__":
    main()
