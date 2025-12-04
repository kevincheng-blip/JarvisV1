.PHONY: help sync
help:
	@echo "Available targets:"
	@echo "  help - Show this help message"
	@echo "  sync - Auto git add/commit/push (J-GOD AutoSync)"

sync:
	@PYTHONPATH=. python3 scripts/git_auto_sync.py --msg "make sync"

