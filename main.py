"""
Job Link Screenshot Agent
Entry point — orchestrates the full pipeline.
"""

import asyncio
import logging
import sys
from pathlib import Path

from config import settings
from excel_parser import parse_job_links
from screenshot_agent import capture_all_screenshots
from email_sender import send_results_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


async def run_pipeline(xlsx_path: str) -> None:
    """End-to-end pipeline: parse → screenshot → email."""

    # ── 1. Parse Excel ────────────────────────────────────────────────────────
    log.info("Parsing job links from: %s", xlsx_path)
    jobs = parse_job_links(xlsx_path)
    if not jobs:
        log.error("No jobs found in %s — aborting.", xlsx_path)
        sys.exit(1)
    log.info("Found %d job(s) to process.", len(jobs))

    # ── 2. Capture screenshots ────────────────────────────────────────────────
    output_dir = Path(settings.SCREENSHOTS_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = await capture_all_screenshots(jobs, output_dir)

    successes = [r for r in results if r["success"]]
    failures  = [r for r in results if not r["success"]]

    log.info(
        "Screenshot results: %d succeeded, %d failed.",
        len(successes),
        len(failures),
    )

    # ── 3. Send email ─────────────────────────────────────────────────────────
    log.info("Sending results email to: %s", settings.EMAIL_TO)
    send_results_email(successes, failures)
    log.info("Pipeline complete.")


if __name__ == "__main__":
    xlsx = sys.argv[1] if len(sys.argv) > 1 else "option1_job_links.xlsx"
    asyncio.run(run_pipeline(xlsx))