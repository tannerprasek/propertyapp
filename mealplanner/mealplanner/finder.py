"""Finds new recipes on the web with Claude, then enriches them from each page's schema.org data."""

import hashlib
import html
import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

import anthropic
import httpx

from . import preferences
from .config import settings

log = logging.getLogger(__name__)

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

SYSTEM_PROMPT = """You find dinner recipes for a busy household's weekly meal plan.

Search the web broadly - recipe sites (Allrecipes, Serious Eats, Bon Appétit, Budget Bytes, \
Food52, Simply Recipes, Smitten Kitchen, NYT Cooking, BBC Good Food, Delish, etc.), food blogs, \
and Reddit (r/recipes, r/EatCheapAndHealthy, r/MealPrepSunday, r/Cooking). Spread picks across \
several different sources.

Every recipe must be:
- Approachable: familiar flavors, nothing too exotic, no hard-to-find ingredients or special equipment.
- Easy: realistic for a weeknight, mostly under about an hour of total time.
- A real page you have actually opened that contains the full ingredient list.
- Varied across the set: mix proteins (chicken, beef, pork, fish, vegetarian), cuisines, and methods \
(sheet pan, one pot, skillet, slow cooker, grill).

Use the household's preferences file to steer choices: lean toward what was starred or praised, \
away from what got negative comments or was repeatedly skipped. Never repeat a URL from the \
already-suggested list.

When you are done researching, reply with ONLY a JSON array (no prose before or after) where each \
item has these keys:
  "title": recipe name,
  "url": the recipe page URL,
  "source": site or subreddit name,
  "description": 2-3 friendly sentences on what it is and why it's a good pick,
  "ingredients": list of ingredient lines exactly as the page writes them (with quantities),
  "total_time": e.g. "35 min" or "" if unknown,
  "servings": e.g. "4" or "" if unknown,
  "image_url": a photo URL from the page if you saw one, else ""
"""


def _week_prompt(count: int) -> str:
    seen = preferences.previously_suggested_urls()[:200]
    return (
        f"Find {count} new dinner recipes for this week.\n\n"
        f"<preferences_file>\n{preferences.read()}\n</preferences_file>\n\n"
        "<already_suggested_urls>\n" + ("\n".join(seen) or "(none)") + "\n</already_suggested_urls>"
    )


def _ask_claude(count: int) -> list[dict]:
    if settings.claude_backend == "api":
        return _ask_claude_api(count)
    return _ask_claude_cli(count)


def _claude_cli_path() -> str:
    if settings.claude_cli:
        return settings.claude_cli
    found = shutil.which("claude")
    if found:
        return found
    # launchd / Windows startup items may not have the user's full PATH, so check the usual install locations too
    home = Path.home()
    appdata = Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
    for candidate in (
        home / ".local/bin/claude",
        home / ".local/bin/claude.exe",
        home / ".claude/local/claude",
        appdata / "npm/claude.cmd",
        Path("/opt/homebrew/bin/claude"),
        Path("/usr/local/bin/claude"),
    ):
        if candidate.exists():
            return str(candidate)
    raise RuntimeError("Claude Code CLI not found. Install it, run `claude` once to log in, or set CLAUDE_CLI.")


def _ask_claude_cli(count: int) -> list[dict]:
    """Runs Claude Code headless so the search bills to the logged-in Claude subscription."""
    env = dict(os.environ)
    # An API key in the environment would take precedence over the subscription login
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    prompt_file = settings.data_dir / "system_prompt.txt"
    prompt_file.write_text(SYSTEM_PROMPT, encoding="utf-8")
    cmd = [
        _claude_cli_path(), "-p",
        "--output-format", "json",
        "--model", settings.cli_model,
        # A file avoids multi-line arguments, which Windows .cmd shims mangle
        "--system-prompt-file", str(prompt_file),
        "--tools", "WebSearch,WebFetch",
        "--allowedTools", "WebSearch,WebFetch",
        "--strict-mcp-config",
        "--no-session-persistence",
    ]
    proc = subprocess.run(
        cmd, input=_week_prompt(count), capture_output=True, text=True, encoding="utf-8",
        env=env, cwd=settings.data_dir, timeout=45 * 60,
        # Don't flash a console window when running as a hidden Windows startup item
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"Claude Code failed (exit {proc.returncode}): {proc.stderr.strip() or proc.stdout[:500]}")
    if result.get("is_error"):
        raise RuntimeError(f"Claude Code error: {result.get('result') or result.get('subtype')}")
    return _parse_json_array(result.get("result", ""))


def _ask_claude_api(count: int) -> list[dict]:
    client = anthropic.Anthropic()
    tools = [
        {"type": "web_search_20260209", "name": "web_search", "max_uses": 20},
        {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 30},
    ]
    messages: list[dict] = [{"role": "user", "content": _week_prompt(count)}]

    for _ in range(8):
        with client.beta.messages.stream(
            model=settings.model,
            max_tokens=64000,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
            output_config={"effort": "high"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            response = stream.get_final_message()

        if response.stop_reason == "refusal":
            raise RuntimeError(f"Claude declined the request: {response.stop_details}")
        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue
        text = "".join(b.text for b in response.content if b.type == "text")
        return _parse_json_array(text)

    raise RuntimeError("Recipe search did not finish after repeated continuations")


def _parse_json_array(text: str) -> list[dict]:
    fenced = re.search(r"```(?:json)?\s*(\[.*\])\s*```", text, re.S)
    candidate = fenced.group(1) if fenced else text[text.find("[") : text.rfind("]") + 1]
    data = json.loads(candidate)
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array of recipes")
    return [d for d in data if isinstance(d, dict) and d.get("title") and d.get("url")]


# ---------- page enrichment ----------

def _iter_jsonld(page: str):
    for block in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', page, re.S | re.I
    ):
        try:
            data = json.loads(html.unescape(block.strip()))
        except json.JSONDecodeError:
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                yield node
                if "@graph" in node:
                    stack.append(node["@graph"])


def _find_recipe_ld(page: str) -> dict | None:
    for node in _iter_jsonld(page):
        types = node.get("@type")
        types = types if isinstance(types, list) else [types]
        if "Recipe" in types:
            return node
    return None


def _first_image(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list) and value:
        return _first_image(value[0])
    if isinstance(value, dict):
        return value.get("url") or value.get("contentUrl") or ""
    return ""


def _iso_duration(value: str) -> str:
    m = re.fullmatch(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:\d+S)?", (value or "").strip())
    if not m or not (m.group(1) or m.group(2)):
        return ""
    hours, mins = int(m.group(1) or 0), int(m.group(2) or 0)
    hours, mins = hours + mins // 60, mins % 60
    parts = ([f"{hours} hr"] if hours else []) + ([f"{mins} min"] if mins else [])
    return " ".join(parts)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", str(text)))).strip()


def _download_image(client: httpx.Client, url: str) -> str:
    if not url.startswith("http"):
        return ""
    try:
        resp = client.get(url)
        resp.raise_for_status()
        ctype = resp.headers.get("content-type", "")
        if not ctype.startswith("image/") or len(resp.content) < 2000:
            return ""
        ext = {"image/png": "png", "image/webp": "webp", "image/gif": "gif"}.get(ctype.split(";")[0], "jpg")
        name = hashlib.sha1(url.encode()).hexdigest()[:16] + "." + ext
        (settings.images_dir / name).write_bytes(resp.content)
        return f"/images/{name}"
    except httpx.HTTPError as exc:
        log.info("image download failed for %s: %s", url, exc)
        return ""


def enrich(client: httpx.Client, item: dict) -> dict:
    recipe = {
        "title": _clean(item["title"]),
        "url": item["url"],
        "source": _clean(item.get("source", "")),
        "description": _clean(item.get("description", "")),
        "ingredients": [_clean(i) for i in item.get("ingredients") or [] if str(i).strip()],
        "total_time": _clean(item.get("total_time", "")),
        "servings": _clean(item.get("servings", "")),
    }
    image_url = item.get("image_url") or ""

    try:
        resp = client.get(item["url"])
        resp.raise_for_status()
        page = resp.text
    except httpx.HTTPError as exc:
        log.info("page fetch failed for %s: %s", item["url"], exc)
        page = ""

    ld = _find_recipe_ld(page) if page else None
    if ld:
        ingredients = [_clean(i) for i in ld.get("recipeIngredient") or [] if str(i).strip()]
        if ingredients:
            recipe["ingredients"] = ingredients
        recipe["total_time"] = _iso_duration(ld.get("totalTime", "")) or recipe["total_time"]
        y = ld.get("recipeYield")
        y = y[0] if isinstance(y, list) and y else y
        recipe["servings"] = recipe["servings"] or (_clean(y) if y else "")
        image_url = _first_image(ld.get("image")) or image_url
        if not recipe["description"] and ld.get("description"):
            recipe["description"] = _clean(ld["description"])[:400]
    if not image_url and page:
        m = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', page, re.I
        ) or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', page, re.I)
        image_url = html.unescape(m.group(1)) if m else ""

    recipe["image"] = _download_image(client, image_url)
    return recipe


def find_recipes() -> list[dict]:
    wanted = settings.recipes_per_week
    candidates = _ask_claude(wanted + 3)
    log.info("Claude returned %d candidates", len(candidates))

    seen = set(preferences.previously_suggested_urls())
    results: list[dict] = []
    with httpx.Client(headers=BROWSER_HEADERS, follow_redirects=True, timeout=20) as client:
        for item in candidates:
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            recipe = enrich(client, item)
            if recipe["ingredients"]:
                results.append(recipe)
            if len(results) == wanted:
                break
    if not results:
        raise RuntimeError("No usable recipes were found this week")
    return results
