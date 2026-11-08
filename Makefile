.DEFAULT_GOAL := help

UV_RUN_ARGS ?=
INSPECT_ARGS ?=
UV_RUN = uv run --locked $(UV_RUN_ARGS)
INSPECT = $(UV_RUN) inspect

# Quote values that are passed to the shell as single arguments.
quote = '$(subst ','"'"',$(1))'

.PHONY: help setup tasks lint format format-check test test-docker test-all check \
	docker-build eval-model eval-agent logs view log-header log-config require-log \
	mcp seed-preview

help:
	@printf '%s\n' \
	  'IRODA / MAKE TARGETS' \
	  '' \
	  'Setup and checks' \
	  '  setup        Install locked dependencies' \
	  '  tasks        List benchmark tasks' \
	  '  check        Run lint, formatting checks, and tests without Docker' \
	  '  lint         Run Ruff lint checks' \
	  '  format       Apply Ruff formatting' \
	  '  format-check Check Ruff formatting' \
	  '  test         Run tests without Docker' \
	  '  test-docker  Run Docker tests' \
	  '  test-all     Run the full test suite with Docker' \
	  '  docker-build Build the reference agent image' \
	  '' \
	  'Evaluations' \
	  '  eval-model   Run the fixed model loop' \
	  '  eval-agent   Run the Docker agent' \
	  '  Pass MODEL on the make command line. Optional variables are SAMPLE, BASE_URL, and LOG_DIR.' \
	  '  Use INSPECT_ARGS for extra Inspect options and UV_RUN_ARGS for uv options.' \
	  '  Example: make eval-model MODEL=ollama/qwen3:4b SAMPLE=office-date' \
	  '' \
	  'Logs and data' \
	  '  logs         List evaluation logs' \
	  '  view         Open Inspect View' \
	  '  log-header   Print a log header (pass LOG=path/to/run.eval)' \
	  '  log-config   Print the run configuration (pass LOG=path/to/run.eval)' \
	  '  mcp          Start the read-only MCP server over stdio' \
	  '  seed-preview Rebuild the seed in a temporary directory'

setup:
	uv sync --locked

tasks:
	$(INSPECT) list tasks benchmark.py

lint:
	$(UV_RUN) ruff check

format:
	$(UV_RUN) ruff format

format-check:
	$(UV_RUN) ruff format --check

test:
	$(UV_RUN) pytest -m 'not docker'

test-docker:
	$(UV_RUN) pytest -m docker

test-all:
	$(UV_RUN) pytest

check: lint format-check test

docker-build:
	docker compose -f environment/compose.yaml build

eval-model eval-agent: eval-%:
	@if [ '$(origin MODEL)' != 'command line' ] || [ -z $(call quote,$(strip $(MODEL))) ]; then \
	  printf '%s\n' 'Pass MODEL=<Inspect model identifier> on the make command line.' >&2; \
	  exit 2; \
	fi
	$(INSPECT) eval benchmark.py@$*_benchmark \
	  --model $(call quote,$(MODEL)) --log-dir $(call quote,$(or $(LOG_DIR),logs/$*)) \
	  $(if $(SAMPLE),--sample-id $(call quote,$(SAMPLE))) \
	  $(if $(BASE_URL),--model-base-url $(call quote,$(BASE_URL))) \
	  $(INSPECT_ARGS)

logs:
	$(INSPECT) log list --log-dir $(call quote,$(or $(LOG_DIR),logs))

view:
	$(INSPECT) view --log-dir $(call quote,$(or $(LOG_DIR),logs)) --recursive

require-log:
	@if [ -z $(call quote,$(strip $(LOG))) ]; then \
	  printf '%s\n' 'Pass LOG=path/to/run.eval on the make command line.' >&2; \
	  exit 2; \
	fi

log-header: require-log
	@$(INSPECT) log dump --header-only $(call quote,$(LOG))

log-config: require-log
	@$(INSPECT) log export-config $(call quote,$(LOG))

mcp:
	$(UV_RUN) python mcp_server.py

seed-preview:
	@out=$$(mktemp -d) && $(UV_RUN) python scripts/build_seed.py --output "$$out/seed.db"
