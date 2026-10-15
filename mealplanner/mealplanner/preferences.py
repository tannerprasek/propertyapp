"""The central preferences.md file that feeds back into recipe recommendations.

Everything above AUTO_MARKER is hand-editable household notes and is preserved.
Everything below it is regenerated from stars, comments, and list picks.
"""

from collections import defaultdict

from . import db
from .config import settings

AUTO_MARKER = "<!-- AUTO-GENERATED BELOW: edits under this line are overwritten -->"

DEFAULT_NOTES = """# Meal Preferences

## Household notes
<!-- Edit freely. These notes are given to the recipe finder every week. -->
- Family-friendly weeknight dinners.
- Ingredients available at a normal grocery store.

"""


def _household_notes() -> str:
    path = settings.preferences_path
    if not path.exists():
        return DEFAULT_NOTES
    text = path.read_text(encoding="utf-8")
    return text.split(AUTO_MARKER, 1)[0] if AUTO_MARKER in text else text


def rebuild() -> None:
    recipes = db.all_recipes_with_week()
    loved = [r for r in recipes if r["starred"]]
    commented = [r for r in recipes if r["comment"].strip()]
    picked = [r for r in recipes if r["in_list"]]

    lines = [AUTO_MARKER, "", "## Starred recipes (she loved these)"]
    lines += [f"- {r['title']} ({r['source']}) - {r['url']}" for r in loved] or ["- (none yet)"]

    lines += ["", "## Comments"]
    lines += [
        f"- {r['title']}{' ★' if r['starred'] else ''}: \"{r['comment'].strip()}\""
        for r in commented
    ] or ["- (none yet)"]

    lines += ["", "## Picked for the shopping list"]
    lines += [f"- {r['title']} (week of {r['week_of']})" for r in picked] or ["- (none yet)"]

    by_week: dict[str, list[str]] = defaultdict(list)
    for r in recipes:
        if not r["in_list"] and not r["starred"]:
            by_week[r["week_of"]].append(r["title"])
    lines += ["", "## Suggested but not picked"]
    lines += [f"- Week of {w}: {', '.join(t)}" for w, t in list(by_week.items())[:8]] or [
        "- (none yet)"
    ]

    settings.preferences_path.write_text(_household_notes().rstrip() + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def read() -> str:
    if not settings.preferences_path.exists():
        rebuild()
    return settings.preferences_path.read_text(encoding="utf-8")


def previously_suggested_urls() -> list[str]:
    return [r["url"] for r in db.all_recipes_with_week()]
