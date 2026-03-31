"""
email_sender.py — Sends all screenshots (and error summary) via Gmail/SMTP.

Design decisions:
  - Uses smtplib with SSL (port 465) — the simplest reliable setup for Gmail.
  - Builds a multipart/mixed email: HTML body + one attachment per screenshot.
  - Screenshots are inlined as attachments, not base64-embedded in HTML,
    keeping the HTML body readable and the email size manageable.
  - A clear error table is included in the body for any failed URLs.
"""

import logging
import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from config import settings

log = logging.getLogger(__name__)


def _build_html_body(
    successes: list[dict[str, Any]],
    failures:  list[dict[str, Any]],
) -> str:
    """Compose an HTML email body with a results table."""

    success_rows = ""
    for r in successes:
        j = r["job"]
        success_rows += (
            f"<tr>"
            f"<td>{j['row_number']}</td>"
            f"<td>{j['job_title']}</td>"
            f"<td>{j['company']}</td>"
            f"<td><a href='{j['url']}'>{j['url']}</a></td>"
            f"<td style='color:#2a7a3b;font-weight:600'>✓ Attached</td>"
            f"</tr>"
        )

    failure_rows = ""
    for r in failures:
        j = r["job"]
        failure_rows += (
            f"<tr>"
            f"<td>{j['row_number']}</td>"
            f"<td>{j['job_title']}</td>"
            f"<td>{j['company']}</td>"
            f"<td><a href='{j['url']}'>{j['url']}</a></td>"
            f"<td style='color:#b91c1c'>{r['error']}</td>"
            f"</tr>"
        )

    failure_section = ""
    if failures:
        failure_section = f"""
        <h2 style="color:#b91c1c;margin-top:2rem">Failed URLs ({len(failures)})</h2>
        <table>
          <thead><tr><th>#</th><th>Job Title</th><th>Company</th><th>URL</th><th>Error</th></tr></thead>
          <tbody>{failure_rows}</tbody>
        </table>
        """

    total   = len(successes) + len(failures)
    summary = f"{len(successes)} of {total} screenshots captured successfully."

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
      body  {{ font-family: sans-serif; font-size: 14px; color: #1a1a1a; max-width: 900px; margin: auto; padding: 2rem; }}
      h1    {{ font-size: 1.3rem; margin-bottom: 0.25rem; }}
      p     {{ margin: 0.25rem 0 1.5rem; color: #555; }}
      table {{ border-collapse: collapse; width: 100%; margin-bottom: 1rem; }}
      th    {{ background: #f3f4f6; text-align: left; padding: 8px 12px; border-bottom: 2px solid #e5e7eb; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
      td    {{ padding: 8px 12px; border-bottom: 1px solid #e5e7eb; vertical-align: top; word-break: break-all; }}
      tr:hover td {{ background: #fafafa; }}
      a     {{ color: #1d4ed8; }}
    </style>
    </head>
    <body>
      <h1>Job Screenshot Agent — Results</h1>
      <p>{summary} Screenshots are attached to this email.</p>

      <h2 style="color:#166534">Successful screenshots ({len(successes)})</h2>
      <table>
        <thead><tr><th>#</th><th>Job Title</th><th>Company</th><th>URL</th><th>Status</th></tr></thead>
        <tbody>{success_rows if success_rows else "<tr><td colspan='5'>None</td></tr>"}</tbody>
      </table>

      {failure_section}
    </body>
    </html>
    """


def send_results_email(
    successes: list[dict[str, Any]],
    failures:  list[dict[str, Any]],
) -> None:
    """
    Build and send the results email with all screenshots attached.

    Raises on SMTP errors so the caller can decide how to handle them.
    """
    msg = MIMEMultipart("mixed")
    msg["Subject"] = (
        f"Job Screenshots: {len(successes)} captured, {len(failures)} failed"
    )
    msg["From"] = settings.EMAIL_FROM
    msg["To"]   = settings.EMAIL_TO

    # HTML body
    html_body = _build_html_body(successes, failures)
    msg.attach(MIMEText(html_body, "html"))

    # Attach each successful screenshot
    for result in successes:
        path = Path(result["screenshot"])
        if not path.exists():
            log.warning("Screenshot file not found, skipping attachment: %s", path)
            continue
        with open(path, "rb") as f:
            part = MIMEApplication(f.read(), Name=path.name)
        part["Content-Disposition"] = f'attachment; filename="{path.name}"'
        msg.attach(part)
        log.debug("Attached: %s", path.name)

    # Send via SSL
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, settings.EMAIL_TO, msg.as_string())
        log.info(
            "Email sent to %s (%d attachment(s)).",
            settings.EMAIL_TO,
            len(successes),
        )
    except smtplib.SMTPAuthenticationError:
        log.error(
            "SMTP authentication failed. For Gmail, ensure you are using an "
            "App Password (not your account password). See README for setup steps."
        )
        raise
    except smtplib.SMTPException as exc:
        log.error("Failed to send email: %s", exc)
        raise