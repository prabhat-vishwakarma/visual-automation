"""Application entry point.

Exit code:
    0 on success
    1 on failure (with diagnostics logged and artifacts saved)
"""

from __future__ import annotations

import argparse
import asyncio

from app.config import AppConfig, load_config
from app.telemetry.logger import get_logger
from app.workflow.orchestrator import WorkflowOrchestrator

logger = get_logger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="visual-automation",
        description="Authorized browser automation with local OCR.",
    )
    parser.add_argument(
        "--config",
        default="config/site.yaml",
        help="path to site YAML configuration",
    )
    return parser.parse_args()


async def _run(config: AppConfig) -> int:
    workflow = WorkflowOrchestrator(config)
    result = await workflow.run()

    if not result.success:
        logger.info(
            "run_finished",
            success=result.success,
            state=result.final_state,
            reason=result.reason,
        )
        return 1

    logger.info(
        "run_finished",
        success=result.success,
        state=result.final_state,
        attempts=result.attempts,
    )
    return 0


def main() -> int:
    args = _parse_args()
    config = load_config(args.config)
    return asyncio.run(_run(config))


if __name__ == "__main__":
    raise SystemExit(main())