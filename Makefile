PROJECT = rfc_http_validate


.PHONY: clean
clean: clean_py

.PHONY: lint
lint: lint_py

.PHONY: typecheck
typecheck: typecheck_py

.PHONY: tidy
tidy: tidy_py

.PHONY: test
test: venv
	PYTHONPATH=. $(VENV)/python -m pytest


include Makefile.pyproject
