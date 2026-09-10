"""End-to-end integration test against the authorized local test page.

Covers the full flow: launch browser -> navigate -> wait for target ->
capture -> OCR -> validate -> fill -> submit -> verify.

Skipped automatically if Chromium cannot be launched (missing OS deps).
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from app.config import load_config
from app.workflow.orchestrator import WorkflowOrchestrator

REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]


@pytest_asyncio.fixture(scope="module")
async def site_url() -> str:
    from tools.serve_test_site import serve, site_url_of

    server = serve(port=0)
    try:
        yield site_url_of(server)
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.asyncio
async def test_full_workflow_succeeds(site_url: str):
    config = load_config(REPO_ROOT / "config" / "local-test.yaml")
    config.target.start_url = site_url
    config.artifacts.root = str(REPO_ROOT / "artifacts")

    orchestrator = WorkflowOrchestrator(config)
    result = await orchestrator.run()

    assert result.success is True, f"workflow failed: {result.reason}"
    assert result.final_state == "COMPLETE"