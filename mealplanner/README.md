# Meal Planner

Runs locally on your Mac. Every Sunday morning it:

1. Has Claude search the web (recipe sites, NYT Cooking, Reddit, blogs) for 10 new, easy, non-exotic dinners, steered by `data/preferences.md`.
2. Opens each recipe page to pull the real ingredient list, cook time, and a thumbnail.
3. Emails a link to the week's page.

On her phone, the page shows 10 recipe cards:

- **+ Add to list**: adds that recipe's ingredients to the shopping list.
- **☆**: stars the recipe.
- **Tap the card**: shows the description, ingredients, a link to the full recipe, and a notes box.
- **Export list** (top of page): a `.txt` shopping list grouped by aisle. On iPhone it opens the share sheet so she can send it to Notes (that needs HTTPS, see below). Otherwise it downloads the file.

Picks, stars and notes are saved on the server, so the link keeps working all week. Old links still open and show a banner pointing to the newest week.

## Preferences file (`data/preferences.md`)

- **Top section (Household notes)**: edit this by hand ("no mushrooms", "kids won't eat spicy", "slow cooker on Tuesdays"). It's kept as-is.
- **Below the marker**: rewritten automatically every time she stars, comments, or adds a recipe to the list. It covers starred recipes, comments, picked recipes, and recipes she skipped.

Each Sunday the whole file goes to Claude along with every URL already suggested, so recipes don't repeat and picks improve over time.

## Install on your Mac

Needs Homebrew Python 3.10+ (`brew install python`) and Claude Code logged in with your Claude Max account (`claude` once, then `/login`).

```bash
git clone https://github.com/tannerprasek/propertyapp.git
cd propertyapp && git checkout claude/weekly-meal-planner && cd mealplanner
make setup          # creates .venv, installs deps, copies .env.example -> .env
open -e .env        # fill in SMTP_USER, SMTP_PASSWORD (Gmail app password), EMAIL_TO, BASE_URL
make preview        # finds recipes now (takes a few minutes), no email; prints the link
make install-mac    # runs in the background from now on, starts at login
```

Recipes are found by running Claude Code headless (`claude -p`) on your Max login, so there's no API key or per-call bill. To use an API key instead, set `CLAUDE_BACKEND=api` and `ANTHROPIC_API_KEY` in `.env`.

Other commands:

```bash
make new-week       # find recipes + send the email right now
make send-email     # re-send the latest week's email
make uninstall-mac  # stop the background service
tail -f data/mealplanner.log
```

If the Mac was asleep on Sunday morning, the app catches up and sends the week the next time it starts. Set the Mac to not sleep while plugged in (System Settings → Battery/Energy) if you want it on time.

## Install on Windows

Needs about 10 GB free disk space. In PowerShell:

```powershell
winget install -e --id Git.Git
winget install -e --id Python.Python.3.12
irm https://claude.ai/install.ps1 | iex
```

Open a new PowerShell window, run `claude`, type `/login` and sign in with your Max account, then `/exit`. Then:

```powershell
git clone https://github.com/tannerprasek/propertyapp.git
cd propertyapp\mealplanner
git checkout claude/weekly-meal-planner
.\mealplanner setup
notepad .env
.\mealplanner preview
.\mealplanner install
```

`install` starts it hidden in the background and adds it to your Startup folder so it runs at every login. Other commands: `.\mealplanner status`, `new-week`, `send-email`, `uninstall`. If Windows Firewall asks about Python, allow it on Private networks so her phone can connect.

## Reaching it from her phone

`BASE_URL` in `.env` is the address the email links to.

- **Home Wi-Fi only**: `BASE_URL=http://<your-mac-name>.local:8765` on a Mac, or `http://<pc-ip-address>:8765` on Windows (`setup` fills this in)
- **Anywhere** (recommended): [Tailscale](https://tailscale.com) on the Mac and her phone, then `tailscale serve --bg 8765` and set `BASE_URL` to the `https://<mac>.<tailnet>.ts.net` address it prints. HTTPS also turns on the iPhone share sheet, so "Export list" can go straight to Notes.

## Layout

```
mealplanner/
  finder.py       Claude web search + recipe page parsing (schema.org JSON-LD)
  weekly.py       the Sunday job
  server.py       FastAPI app + APScheduler
  db.py           SQLite (data/mealplanner.db)
  preferences.py  data/preferences.md
  shopping.py     shopping list text
  mailer.py       SMTP email
  static/index.html  phone UI
```
