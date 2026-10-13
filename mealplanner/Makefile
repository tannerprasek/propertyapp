PY := .venv/bin/python
PYTHON ?= $(shell for p in python3.13 python3.12 python3.11 python3.10 python3; do command -v $$p >/dev/null && $$p -c 'import sys; sys.exit(sys.version_info < (3, 10))' && echo $$p && break; done)
PLIST := $(HOME)/Library/LaunchAgents/com.mealplanner.plist

setup:
	@test -n "$(PYTHON)" || { echo "Python 3.10+ is required. Install it with: brew install python"; exit 1; }
	$(PYTHON) -m venv .venv
	$(PY) -m pip install -r requirements.txt
	@test -f .env || cp .env.example .env
	@mkdir -p data

serve:
	$(PY) -m mealplanner serve

new-week:
	$(PY) -m mealplanner new-week

preview:
	$(PY) -m mealplanner new-week --no-email

send-email:
	$(PY) -m mealplanner send-email

install-mac:
	@mkdir -p data
	sed -e "s#__DIR__#$(CURDIR)#g" -e "s#__HOME__#$(HOME)#g" deploy/com.mealplanner.plist > $(PLIST)
	launchctl unload $(PLIST) 2>/dev/null || true
	launchctl load $(PLIST)
	@echo "Running in the background. Logs: data/mealplanner.log"

uninstall-mac:
	launchctl unload $(PLIST) 2>/dev/null || true
	rm -f $(PLIST)

.PHONY: setup serve new-week preview send-email install-mac uninstall-mac
