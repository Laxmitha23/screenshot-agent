"""
screenshot_agent.py — Visits each URL and captures a full-page screenshot.

Design decisions:
  - Uses Playwright's async API for non-blocking I/O.
  - Each URL is processed independently; failures are caught and logged
    without stopping the rest of the pipeline.
  - Screenshots are saved as PNG with a sanitised filename derived from
    the job title and company name.
  - A short settle-wait after load catches lazy-loaded content.
"""

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from config import settings

log = logging.getLogger(__name__)


def _safe_filename(job: dict[str, Any]) -> str:
    """Convert job metadata to a filesystem-safe PNG filename."""
    raw = f"{job['row_number']}_{job['job_title']}_{job['company']}"
    safe = re.sub(r"[^\w\-]", "_", raw).lower()
    safe = re.sub(r"_+", "_", safe).strip("_")
    return f"{safe}.png"


async def _capture_one(
    page,
    job: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    """
    Navigate to a single URL and capture a full-page screenshot.

    Returns a result dict regardless of success or failure so the caller
    can always aggregate results uniformly.
    """
    url      = job["url"]
    filename = _safe_filename(job)
    out_path = output_dir / filename

    log.info("Processing [%s] %s — %s", job["row_number"], job["job_title"], url)

    try:
        response = await page.goto(url, timeout=settings.PAGE_TIMEOUT_MS, wait_until="domcontentloaded")

        # Allow lazy content to settle before capturing
        await page.wait_for_timeout(settings.SCREENSHOT_WAIT_MS)

        # Check for HTTP error status codes
        if response and response.status >= 400:
            raise RuntimeError(
                f"HTTP {response.status} returned for URL: {url}"
            )

        await page.screenshot(path=str(out_path), full_page=True)
        log.info("  ✓ Saved: %s", out_path.name)

        return {
            "success":    True,
            "job":        job,
            "screenshot": str(out_path),
            "error":      None,
        }

    except PWTimeout:
        err = f"Timed out after {settings.PAGE_TIMEOUT_MS}ms loading {url}"
        log.warning("  ✗ %s", err)
        return {"success": False, "job": job, "screenshot": None, "error": err}

    except Exception as exc:  # noqa: BLE001
        err = str(exc)
        log.warning("  ✗ Failed (%s): %s", type(exc).__name__, err)
        return {"success": False, "job": job, "screenshot": None, "error": err}


async def capture_all_screenshots(
    jobs: list[dict[str, Any]],
    output_dir: Path,
) -> list[dict[str, Any]]:
    """
    Launch a single Playwright browser, open one page per job (sequentially),
    and return a list of result dicts.

    Sequential processing (not concurrent) keeps browser memory usage
    predictable and avoids overwhelming targets with simultaneous requests.
    To process in parallel, replace the sequential loop with asyncio.gather.
    """
    results: list[dict[str, Any]] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        for job in jobs:
            page = await context.new_page()
            result = await _capture_one(page, job, output_dir)
            results.append(result)
            await page.close()

        await context.close()
        await browser.close()

    return results