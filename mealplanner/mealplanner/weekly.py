"""The Sunday job: find recipes, store the week, email the link."""

import logging
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import db, finder, mailer, preferences
from .config import settings

log = logging.getLogger(__name__)
_lock = threading.Lock()

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _now() -> datetime:
    return datetime.now(ZoneInfo(settings.timezone))


def last_scheduled_time() -> datetime:
    now = _now()
    target = DAYS.index(settings.send_day.lower()[:3])
    run = now.replace(hour=settings.send_hour, minute=settings.send_minute, second=0, microsecond=0)
    run -= timedelta(days=(now.weekday() - target) % 7)
    if run > now:
        run -= timedelta(days=7)
    return run


def is_due() -> bool:
    """True if the most recent scheduled run was missed (e.g. the machine was asleep)."""
    week = db.latest_week()
    if not week:
        return False
    created = datetime.fromisoformat(week["created_at"])
    return created < last_scheduled_time()


def run_week(send_email: bool = True) -> dict | None:
    if not _lock.acquire(blocking=False):
        log.info("A weekly run is already in progress")
        return None
    try:
        log.info("Finding this week's recipes...")
        recipes = finder.find_recipes()
        week_of = _now().date().isoformat()
        week = db.create_week(week_of, recipes)
        preferences.rebuild()
        log.info("Week %s created with %d recipes: %s", week_of, len(recipes), mailer.week_url(week["token"]))
        if send_email:
            mailer.send_week_email(week)
            db.mark_emailed(week["id"])
            log.info("Email sent to %s", ", ".join(settings.email_to))
        return week
    finally:
        _lock.release()
