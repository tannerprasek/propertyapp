"""SQLite storage for weeks and their recipes."""

import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS weeks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    week_of TEXT NOT NULL,
    created_at TEXT NOT NULL,
    emailed_at TEXT
);
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_id INTEGER NOT NULL REFERENCES weeks(id),
    position INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    image TEXT NOT NULL DEFAULT '',
    total_time TEXT NOT NULL DEFAULT '',
    servings TEXT NOT NULL DEFAULT '',
    ingredients TEXT NOT NULL DEFAULT '[]',
    in_list INTEGER NOT NULL DEFAULT 0,
    starred INTEGER NOT NULL DEFAULT 0,
    comment TEXT NOT NULL DEFAULT '',
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_recipes_week ON recipes(week_id);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect():
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def _recipe_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["ingredients"] = json.loads(d["ingredients"])
    d["in_list"] = bool(d["in_list"])
    d["starred"] = bool(d["starred"])
    return d


def create_week(week_of: str, recipes: list[dict]) -> dict:
    token = secrets.token_urlsafe(16)
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO weeks (token, week_of, created_at) VALUES (?, ?, ?)",
            (token, week_of, now_iso()),
        )
        week_id = cur.lastrowid
        for pos, r in enumerate(recipes):
            conn.execute(
                """INSERT INTO recipes (week_id, position, title, url, source, description,
                   image, total_time, servings, ingredients)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    week_id, pos, r["title"], r["url"], r.get("source", ""),
                    r.get("description", ""), r.get("image", ""), r.get("total_time", ""),
                    r.get("servings", ""), json.dumps(r.get("ingredients", [])),
                ),
            )
    return get_week_by_token(token)


def get_week_by_token(token: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM weeks WHERE token = ?", (token,)).fetchone()
        if not row:
            return None
        week = dict(row)
        week["recipes"] = [
            _recipe_dict(r)
            for r in conn.execute(
                "SELECT * FROM recipes WHERE week_id = ? ORDER BY position", (week["id"],)
            )
        ]
        return week


def latest_week() -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT token FROM weeks ORDER BY id DESC LIMIT 1").fetchone()
    return get_week_by_token(row["token"]) if row else None


def mark_emailed(week_id: int) -> None:
    with connect() as conn:
        conn.execute("UPDATE weeks SET emailed_at = ? WHERE id = ?", (now_iso(), week_id))


def update_recipe(token: str, recipe_id: int, fields: dict) -> dict | None:
    allowed = {"in_list", "starred", "comment"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if "in_list" in fields:
        fields["in_list"] = int(bool(fields["in_list"]))
    if "starred" in fields:
        fields["starred"] = int(bool(fields["starred"]))
    if "comment" in fields:
        fields["comment"] = str(fields["comment"])[:2000]
    with connect() as conn:
        row = conn.execute(
            """SELECT r.id FROM recipes r JOIN weeks w ON w.id = r.week_id
               WHERE w.token = ? AND r.id = ?""",
            (token, recipe_id),
        ).fetchone()
        if not row:
            return None
        if fields:
            sets = ", ".join(f"{k} = ?" for k in fields)
            conn.execute(
                f"UPDATE recipes SET {sets}, updated_at = ? WHERE id = ?",
                (*fields.values(), now_iso(), recipe_id),
            )
        return _recipe_dict(conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone())


def all_recipes_with_week() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT r.*, w.week_of FROM recipes r JOIN weeks w ON w.id = r.week_id
               ORDER BY w.id DESC, r.position"""
        ).fetchall()
    return [_recipe_dict(r) for r in rows]
