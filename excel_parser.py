"""
excel_parser.py — Reads the job links Excel file.

Returns a list of dicts with keys:
    row_number, job_title, company, url
The Status and Notes columns are intentionally ignored.
"""

import logging
from pathlib import Path
from typing import Any

import openpyxl

log = logging.getLogger(__name__)

# Column indices (1-based) matching the spec
COL_ROW_NUMBER = 1   # #
COL_JOB_TITLE  = 2   # Job Title
COL_COMPANY    = 3   # Company
COL_URL        = 4   # URL
# Columns 5 (Status) and 6 (Notes) are skipped deliberately.


def parse_job_links(xlsx_path: str) -> list[dict[str, Any]]:
    """
    Parse the job-links spreadsheet and return one dict per job row.

    Skips rows that are missing a URL.  Strips leading/trailing whitespace
    from all string values before returning.
    """
    path = Path(xlsx_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path.resolve()}")

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    jobs: list[dict[str, Any]] = []
    header_skipped = False

    for row in ws.iter_rows(values_only=True):
        # Skip the header row (first row that contains non-numeric first cell)
        if not header_skipped:
            header_skipped = True
            log.debug("Skipping header row: %s", row)
            continue

        row_number = row[COL_ROW_NUMBER - 1]
        job_title  = row[COL_JOB_TITLE  - 1]
        company    = row[COL_COMPANY    - 1]
        url        = row[COL_URL        - 1]

        if not url:
            log.warning("Row %s has no URL — skipping.", row_number)
            continue

        jobs.append({
            "row_number": row_number,
            "job_title":  str(job_title).strip() if job_title else "Unknown Title",
            "company":    str(company).strip()   if company   else "Unknown Company",
            "url":        str(url).strip(),
        })
        log.debug("Parsed job: %s @ %s → %s", job_title, company, url)

    wb.close()
    log.info("Parsed %d job(s) from %s", len(jobs), path.name)
    return jobs