# Job Link Screenshot Agent

A Python agentic workflow that reads job posting URLs from an Excel file, captures a full-page screenshot of each page using Playwright, and delivers all screenshots via email — with a clear error summary for any URLs that failed.

## Option chosen: Option 1 — Job Link Screenshot Agent

I chose Option 1 because it showcases a clean multi-step agentic pipeline with clear separation of concerns, real-world error handling challenges (dead links, paywalls, rate limits), and a complete end-to-end deliverable in a short amount of code.

---

## Project structure

```
screenshot-agent/
├── main.py              # Pipeline orchestrator — start here
├── config.py            # Settings loaded from environment variables
├── excel_parser.py      # Reads option1_job_links.xlsx with openpyxl
├── screenshot_agent.py  # Playwright browser automation
├── email_sender.py      # SMTP/Gmail delivery with attachments
├── requirements.txt
├── .env.example         # Template for required environment variables
├── .env                 # Your local credentials (never commit this)
└── screenshots/         # Created at runtime — PNG output lives here
```

---

## Setup and installation

### Prerequisites

- Python 3.11+
- A Gmail account with an **App Password** (see below)

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd screenshot-agent
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium      # Downloads the Chromium browser binary
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```
EMAIL_USER=your.address@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx   # Gmail App Password
EMAIL_FROM=your.address@gmail.com
EMAIL_TO=recipient@example.com
```

**Creating a Gmail App Password:**
1. Go to your Google Account → Security → 2-Step Verification (must be enabled)
2. Scroll down to "App passwords" → generate one for "Mail"
3. Use the 16-character code as `EMAIL_PASSWORD` — not your regular password

### 3. Add the input file

Place `option1_job_links.xlsx` in the project root (alongside `main.py`).

### 4. Run the agent

```bash
python main.py
# or specify a custom path:
python main.py path/to/option1_job_links.xlsx
```

---

## How it works

```
Excel file → [parse] → [screenshot each URL] → [build report] → [send email]
```

1. **`excel_parser.py`** — Opens the workbook with `openpyxl`, skips the header row, reads columns 1–4 (`#`, `Job Title`, `Company`, `URL`). The `Status` and `Notes` columns are intentionally ignored — all 5 URLs are treated as unknown inputs.

2. **`screenshot_agent.py`** — Launches a headless Chromium browser via Playwright's async API. For each job, it opens a new page, navigates to the URL, waits for the DOM to load, pauses briefly for lazy content to settle, then captures a full-page PNG. Each URL is processed independently — a failure on one does not affect the others.

3. **`email_sender.py`** — Builds a `multipart/mixed` email with an HTML body (success table + error table) and one PNG attachment per successful screenshot. Sends via `smtplib` with SSL on port 465.

---

## Error handling strategy

| Failure type | Behaviour |
|---|---|
| URL timeout | Caught, logged, recorded as failure — pipeline continues |
| HTTP 4xx/5xx | Detected from response status, recorded as failure |
| Network error | Caught by broad exception handler, recorded as failure |
| Empty URL in Excel | Row is skipped with a warning before Playwright is invoked |
| SMTP auth failure | Raises immediately with a clear message pointing to the App Password docs |
| Missing screenshot file | Skipped from attachments with a warning; body still sent |

---

## Key design decisions

- **Sequential not concurrent:** URLs are processed one at a time. This keeps memory usage predictable, avoids hammering servers simultaneously, and makes the logs easy to follow. For larger inputs, swapping the sequential loop for `asyncio.gather` would speed things up.
- **Async Playwright:** The browser automation uses Playwright's `async_api` to keep I/O non-blocking and compatible with any future parallelism.
- **New page per URL:** Each job gets a fresh `page` object (not a fresh browser context). This avoids session bleed between sites while reusing the browser process.
- **Settle wait:** A configurable `SCREENSHOT_WAIT_MS` pause after `domcontentloaded` catches lazy-loaded images and JS-rendered content without having to wait for `networkidle` (which hangs on polling sites).
- **Sanitised filenames:** Screenshot filenames are derived from the job metadata so they're human-readable in the email attachment list.

---

## Assumptions

- The Excel file always has a header row; the URL is always in column 4.
- Gmail SMTP with SSL (port 465) is used; the setup is easily adapted to other SMTP providers by changing `SMTP_HOST`, `SMTP_PORT`.
- Screenshots are full-page PNGs. A truncated viewport screenshot could be substituted by removing `full_page=True`.
- The agent does not attempt retries on failure. One retry with exponential backoff would be a straightforward addition.

---

## What I would improve given more time

- **Retry logic** — retry transient failures (network blips, rate limits) up to N times with exponential backoff before recording as a failure.
- **Concurrent processing** — process URLs in parallel with a semaphore to cap concurrency, significantly reducing total runtime.
- **Richer error classification** — distinguish between DNS failure, timeout, HTTP error, and JS error for more actionable error messages.
- **Screenshot quality options** — clip to a fixed viewport height as a fallback for very long pages; optionally save as JPEG to reduce attachment size.
- **CI integration** — a GitHub Actions workflow to run a smoke test against a mock URL on every push.

---

## Demo video

[Link to Loom / YouTube recording]

---

## Environment variables reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `EMAIL_USER` | ✓ | — | Gmail address used to authenticate |
| `EMAIL_PASSWORD` | ✓ | — | Gmail App Password |
| `EMAIL_FROM` | ✓ | — | Sender address in the email |
| `EMAIL_TO` | ✓ | — | Recipient address |
| `SMTP_HOST` | | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT` | | `465` | SMTP port (SSL) |
| `PAGE_TIMEOUT_MS` | | `15000` | Max ms to wait for page load |
| `SCREENSHOT_WAIT_MS` | | `2000` | Extra ms settle-wait after load |
| `SCREENSHOTS_DIR` | | `screenshots` | Output directory for PNGs |