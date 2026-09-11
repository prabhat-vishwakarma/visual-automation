"""Owner-gated web demo for the visual-automation workflow.

Serves a browser page that runs the bundled authorized local test harness and
streams the run's JSON events (state changes, OCR results, outcome) live.

Security posture:
    - binds to 127.0.0.1 only (no external access),
    - only the two bundled configs are allowed (no arbitrary paths),
    - never reads or writes any third-party site.

Run:
    webapp/run_webapp.sh
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import urllib.request
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from tools.ensure_chromium_deps import (
    MISSING_NAME_MAP,
    download_and_extract,
    find_browser_binaries,
    missing_libraries,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIGS = {
    "local-test": "config/local-test.yaml",
    "demo": "config/demo.yaml",
}
TEST_SITE_PORT = 8800
TEST_SITE_URL = f"http://127.0.0.1:{TEST_SITE_PORT}/"

app = FastAPI(title="Visual Automation demo", docs_url=None, redoc_url=None)
app.mount(
    "/assets",
    StaticFiles(directory=str(REPO_ROOT / "assets")),
    name="assets",
)

_active: list[asyncio.subprocess.Process] = []
_site_proc: subprocess.Popen | None = None


def _chromium_env() -> dict[str, str]:
    env = dict(os.environ)
    try:
        packages: set[str] = set()
        for binary in find_browser_binaries():
            for lib in missing_libraries(binary):
                packages.add(MISSING_NAME_MAP[lib])
        if packages:
            lib_dir = download_and_extract(packages)
            existing = env.get("LD_LIBRARY_PATH", "")
            env["LD_LIBRARY_PATH"] = (
                f"{lib_dir}{os.pathsep + existing if existing else ''}"
            )
    except Exception as exc:
        print(f"chromium deps check skipped: {exc}", file=sys.stderr)
    return env


def test_site_running() -> bool:
    try:
        with urllib.request.urlopen(TEST_SITE_URL, timeout=2):
            return True
    except Exception:
        return False


@app.on_event("shutdown")
async def _shutdown() -> None:
    for proc in _active:
        try:
            proc.terminate()
            await proc.wait()
        except ProcessLookupError:
            pass
    if _site_proc is not None:
        _site_proc.terminate()


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return (Path(__file__).parent / "index.html").read_text()


@app.get("/api/health")
async def health() -> dict[str, bool]:
    return {"status": True, "site_running": test_site_running()}


async def _run_stream(config: str) -> AsyncIterator[str]:
    python = REPO_ROOT / ".venv" / "bin" / "python"
    command = [str(python), "-m", "app.main", "--config", CONFIGS[config]]
    if not python.exists():
        command[0] = sys.executable

    proc = await asyncio.create_subprocess_exec(
        *command,
        cwd=REPO_ROOT,
        env=_chromium_env(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    _active.append(proc)

    yield _event_json({"kind": "started", "pid": proc.pid})
    assert proc.stdout is not None
    while True:
        raw = await proc.stdout.readline()
        if not raw:
            break
        line = raw.decode(errors="replace").rstrip("\n")
        if line:
            yield _event_json({"kind": "event", "line": line})
    code = await proc.wait()
    if proc in _active:
        _active.remove(proc)
    await asyncio.sleep(0.2)
    yield _event_json({"kind": "exit", "code": code})


def _event_json(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@app.get("/api/run")
async def run_demo(config: str = "local-test") -> StreamingResponse:
    if config not in CONFIGS:
        raise HTTPException(status_code=404, detail="unknown config")
    if _active:
        raise HTTPException(status_code=409, detail="a run is already in progress")
    return StreamingResponse(
        _run_stream(config),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def main() -> None:
    import uvicorn

    global _site_proc
    if not _is_open(TEST_SITE_PORT):
        _site_proc = subprocess.Popen(
            [
                ".venv/bin/python",
                "-m",
                "tools.serve_test_site",
                "--port",
                str(TEST_SITE_PORT),
            ],
            cwd=REPO_ROOT,
        )
    uvicorn.run(app, host="127.0.0.1", port=8710, log_level="info")


if __name__ == "__main__":
    main()