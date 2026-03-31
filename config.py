"""
config.py — All settings loaded from environment variables.

Copy .env.example to .env and fill in your values before running.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # ── Email ─────────────────────────────────────────────────────────────────
    SMTP_HOST: str       = field(default_factory=lambda: os.getenv("SMTP_HOST", "smtp.gmail.com"))
    SMTP_PORT: int       = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "465")))
    EMAIL_USER: str      = field(default_factory=lambda: os.getenv("EMAIL_USER", ""))
    EMAIL_PASSWORD: str  = field(default_factory=lambda: os.getenv("EMAIL_PASSWORD", ""))
    EMAIL_FROM: str      = field(default_factory=lambda: os.getenv("EMAIL_FROM", ""))
    EMAIL_TO: str        = field(default_factory=lambda: os.getenv("EMAIL_TO", ""))

    # ── Browser ───────────────────────────────────────────────────────────────
    PAGE_TIMEOUT_MS: int      = field(default_factory=lambda: int(os.getenv("PAGE_TIMEOUT_MS", "15000")))
    SCREENSHOT_WAIT_MS: int   = field(default_factory=lambda: int(os.getenv("SCREENSHOT_WAIT_MS", "2000")))

    # ── Output ────────────────────────────────────────────────────────────────
    SCREENSHOTS_DIR: str = field(default_factory=lambda: os.getenv("SCREENSHOTS_DIR", "screenshots"))

    def validate(self) -> None:
        """Raise early with a clear message if required vars are missing."""
        required = {
            "EMAIL_USER":     self.EMAIL_USER,
            "EMAIL_PASSWORD": self.EMAIL_PASSWORD,
            "EMAIL_FROM":     self.EMAIL_FROM,
            "EMAIL_TO":       self.EMAIL_TO,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Copy .env.example → .env and fill in your values."
            )


settings = Settings()
settings.validate()