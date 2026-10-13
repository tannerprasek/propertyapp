"""Settings loaded from environment / .env."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

APP_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(APP_ROOT / ".env")


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    base_url: str
    host: str
    port: int
    timezone: str
    send_day: str
    send_hour: int
    send_minute: int
    recipes_per_week: int
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email_from: str
    email_to: list[str]
    model: str

    @property
    def db_path(self) -> Path:
        return self.data_dir / "mealplanner.db"

    @property
    def images_dir(self) -> Path:
        return self.data_dir / "images"

    @property
    def preferences_path(self) -> Path:
        return self.data_dir / "preferences.md"


def load_settings() -> Settings:
    data_dir = Path(_env("MEALPLANNER_DATA_DIR") or APP_ROOT / "data").expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "images").mkdir(exist_ok=True)
    port = int(_env("PORT", "8765"))
    return Settings(
        data_dir=data_dir,
        base_url=(_env("BASE_URL") or f"http://localhost:{port}").rstrip("/"),
        host=_env("HOST", "0.0.0.0"),
        port=port,
        timezone=_env("TIMEZONE", "America/Chicago"),
        send_day=_env("SEND_DAY", "sun"),
        send_hour=int(_env("SEND_HOUR", "7")),
        send_minute=int(_env("SEND_MINUTE", "0")),
        recipes_per_week=int(_env("RECIPES_PER_WEEK", "10")),
        smtp_host=_env("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(_env("SMTP_PORT", "587")),
        smtp_user=_env("SMTP_USER"),
        smtp_password=_env("SMTP_PASSWORD"),
        email_from=_env("EMAIL_FROM") or _env("SMTP_USER"),
        email_to=[e.strip() for e in _env("EMAIL_TO").split(",") if e.strip()],
        model=_env("CLAUDE_MODEL", "claude-opus-5-5"),
    )


settings = load_settings()
