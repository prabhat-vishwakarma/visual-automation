"""Generate a 3-frame demo GIF (challenge → filled → success).

Run via:
    .venv/bin/python -m tools.ensure_chromium_deps \
        --command ".venv/bin/python -m tools.make_demo_gif"

Requires the local test site running on port 8800.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SITE_URL = "http://127.0.0.1:8800/"
CODE = "K7Q2P"


async def _run() -> None:
    ASSETS.mkdir(exist_ok=True)
    pw = await async_playwright().start()

    try:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 900, "height": 600})

        # Frame 1 — challenge page as loaded
        await page.goto(SITE_URL, wait_until="networkidle")
        await page.wait_for_timeout(600)
        await page.screenshot(path=str(ASSETS / "frame1.png"))
        print("  frame 1 captured")

        # Frame 2 — code filled into input
        await page.fill('[data-testid="verification-input"]', CODE)
        await page.wait_for_timeout(400)
        await page.screenshot(path=str(ASSETS / "frame2.png"))
        print("  frame 2 captured")

        # Frame 3 — success after Continue
        await page.click('[data-testid="continue-button"]')
        await page.wait_for_timeout(600)
        await page.screenshot(path=str(ASSETS / "frame3.png"))
        print("  frame 3 captured")

        await browser.close()
    finally:
        await pw.stop()

    # Build animated GIF
    frames = [Image.open(ASSETS / f"frame{i}.png") for i in [1, 2, 3]]
    gif_path = ASSETS / "demo.gif"
    frames[0].save(
        str(gif_path),
        save_all=True,
        append_images=frames[1:],
        duration=[2000, 2000, 3000],  # ms per frame
        loop=0,
    )
    print(f"  demo.gif saved ({gif_path.stat().st_size:,} bytes)")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()