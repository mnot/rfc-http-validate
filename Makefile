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
test:
	@echo "we need some tests."


include Makefile.pyproject
