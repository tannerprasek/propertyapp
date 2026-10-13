PY := .venv/bin/python
PLIST := $(HOME)/Library/LaunchAgents/com.mealplanner.plist

setup:
	python3 -m venv .venv
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
	sed "s#__DIR__#$(CURDIR)#g" deploy/com.mealplanner.plist > $(PLIST)
	launchctl unload $(PLIST) 2>/dev/null || true
	launchctl load $(PLIST)
	@echo "Running in the background. Logs: data/mealplanner.log"

uninstall-mac:
	launchctl unload $(PLIST) 2>/dev/null || true
	rm -f $(PLIST)

.PHONY: setup serve new-week preview send-email install-mac uninstall-mac
