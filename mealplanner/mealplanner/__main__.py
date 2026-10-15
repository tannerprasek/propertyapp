"""CLI: python -m mealplanner [serve|new-week|send-email|prefs]"""

import argparse
import logging
import sys

from . import db, mailer, preferences, weekly
from .config import settings


def main() -> None:
    if sys.stdout is None or sys.stderr is None:
        # Started without a console (pythonw.exe on Windows): log to a file instead
        log = open(settings.data_dir / "mealplanner.log", "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stderr = log
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="mealplanner")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("serve", help="Run the web UI + Sunday scheduler (default)")
    nw = sub.add_parser("new-week", help="Find recipes now and create a new week")
    nw.add_argument("--no-email", action="store_true", help="Skip sending the email")
    sub.add_parser("send-email", help="Re-send the email for the latest week")
    sub.add_parser("prefs", help="Rebuild and print preferences.md")
    args = parser.parse_args()

    db.init_db()
    if args.cmd == "new-week":
        week = weekly.run_week(send_email=not args.no_email)
        if week:
            print(mailer.week_url(week["token"]))
    elif args.cmd == "send-email":
        week = db.latest_week()
        if not week:
            raise SystemExit("No week exists yet. Run new-week first.")
        mailer.send_week_email(week)
        db.mark_emailed(week["id"])
        print(f"Sent {mailer.week_url(week['token'])}")
    elif args.cmd == "prefs":
        preferences.rebuild()
        print(settings.preferences_path.read_text(encoding="utf-8"))
    else:
        import uvicorn

        uvicorn.run("mealplanner.server:app", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
