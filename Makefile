# Gate order matches docs/AI_CODE_QUALITY.md: lint, types, tests, security.
PY  := .venv/bin/python
SEC := .venv-security/bin
GH_VERSION := 2.100.0

.PHONY: venv lock lint types test test-model security check merge dev

venv:  ## dev toolchain on 3.14, security toolchain on 3.12 (AI_CODE_QUALITY 4)
	uv venv --python 3.14 .venv
	uv pip install --python .venv --require-hashes -r requirements-dev.txt
	uv venv --python 3.12 .venv-security
	uv pip install --python .venv-security --require-hashes -r requirements-security.txt

lock:  ## recompile every lock with hashes; the answer to a red audit is a recompile
	uv pip compile --generate-hashes --python-version 3.14 -o requirements.txt requirements.in
	uv pip compile --generate-hashes --python-version 3.14 -o requirements-dev.txt requirements-dev.in
	uv pip compile --generate-hashes --python-version 3.12 -o requirements-security.txt requirements-security.in

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .
	$(PY) scripts/check_vocabulary.py
	$(PY) scripts/check_tested.py

types:
	$(PY) -m mypy scripts tests server

test:
	$(PY) -m pytest
	$(PY) scripts/io_budget.py --assert

test-model:  ## needs soffice on PATH; a green model suite without it is vacuous
	soffice --version
	$(PY) -m pytest -m model_parity

security:  # the floor is checked first: a report that parsed nothing must fail
	$(SEC)/bandit -r scripts server -f json -o bandit.json || true
	$(PY) scripts/scan_floors.py bandit.json --min-files 1 --no-parse-errors
	$(SEC)/bandit -r scripts server
	$(SEC)/pip-audit --require-hashes -r requirements.txt -r requirements-dev.txt \
		-r requirements-security.txt
	gitleaks git --no-banner

check: lint types test security

merge:  ## refuse to merge a PR whose checks are not all green
	@case "$${PR-}" in ''|0*|*[!0-9]*) echo "usage: make merge PR=<number>"; exit 1;; esac; \
	gh="$$(command -v gh)" || { echo "error: gh $(GH_VERSION) is required"; exit 1; }; \
	gh_version="$$( "$$gh" --version | sed -n '1s/^gh version \([^ ]*\).*/\1/p' )"; \
	test "$$gh_version" = "$(GH_VERSION)" || { echo "error: gh $(GH_VERSION) is required (found $${gh_version:-unknown})"; exit 1; }; \
	head_oid="$$( "$$gh" pr view "$$PR" --json headRefOid --jq .headRefOid )" && \
	test -n "$$head_oid" && \
	"$$gh" pr checks "$$PR" && \
	"$$gh" pr merge "$$PR" --merge --match-head-commit "$$head_oid"

dev:
	@echo "no application code yet; the API and worker arrive in Phase 1" && exit 1
