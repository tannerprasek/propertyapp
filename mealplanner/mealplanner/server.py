"""Local web server: the phone UI, its JSON API, and the Sunday scheduler."""

import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import db, preferences, shopping, weekly
from .config import settings

log = logging.getLogger(__name__)
STATIC = Path(__file__).parent / "static"


def _scheduled_run() -> None:
    try:
        weekly.run_week(send_email=True)
    except Exception:
        log.exception("Weekly run failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    scheduler = BackgroundScheduler(timezone=settings.timezone)
    scheduler.add_job(
        _scheduled_run,
        CronTrigger(
            day_of_week=settings.send_day, hour=settings.send_hour,
            minute=settings.send_minute, timezone=settings.timezone,
        ),
        misfire_grace_time=6 * 3600,
        coalesce=True,
    )
    scheduler.start()
    if weekly.is_due():
        log.info("Missed this week's run; catching up now")
        threading.Thread(target=_scheduled_run, daemon=True).start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC), name="static")
app.mount("/images", StaticFiles(directory=settings.images_dir), name="images")


def _week_or_404(token: str) -> dict:
    week = db.get_week_by_token(token)
    if not week:
        raise HTTPException(404, "This link has expired or is invalid")
    return week


@app.get("/")
def home():
    week = db.latest_week()
    if not week:
        return PlainTextResponse("No recipes yet. Run `python -m mealplanner new-week` to create the first week.")
    return RedirectResponse(f"/w/{week['token']}")


@app.get("/w/{token}")
def week_page(token: str):
    _week_or_404(token)
    return FileResponse(STATIC / "index.html")


@app.get("/api/w/{token}")
def week_data(token: str):
    week = _week_or_404(token)
    latest = db.latest_week()
    newer = latest["token"] if latest and latest["id"] != week["id"] else None
    return {
        "week_of": week["week_of"],
        "newer_week": newer,
        "recipes": [
            {k: r[k] for k in (
                "id", "title", "url", "source", "description", "image", "total_time",
                "servings", "ingredients", "in_list", "starred", "comment",
            )}
            for r in week["recipes"]
        ],
    }


@app.patch("/api/w/{token}/recipes/{recipe_id}")
def update_recipe(token: str, recipe_id: int, changes: dict = Body(...)):
    recipe = db.update_recipe(token, recipe_id, changes)
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    preferences.rebuild()
    return {"ok": True, "in_list": recipe["in_list"], "starred": recipe["starred"], "comment": recipe["comment"]}


@app.get("/w/{token}/shopping-list.txt")
def shopping_list(token: str):
    week = _week_or_404(token)
    return PlainTextResponse(
        shopping.build(week["recipes"], week["week_of"]),
        headers={"Content-Disposition": f'attachment; filename="shopping-list-{week["week_of"]}.txt"'},
    )
