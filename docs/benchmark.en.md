# Run the IRODA benchmark

`IRODA / RUN GUIDE`

Set up the environment, run the starter cases, and inspect the resulting logs.

[Magyar](benchmark.hu.md) · [Project overview](../README.en.md)

## Install and check the environment

Use a POSIX shell from the project root. The benchmark needs Python 3.12 and SQLite 3.37 or newer in that interpreter. Install uv first. The CI workflow uses uv 0.7.12. The model mode needs no container runtime. The agent mode needs a running Docker Engine or Docker Desktop with Docker Compose v2. The first setup downloads Python packages, and the first agent run also builds the image. [uv installation](https://docs.astral.sh/uv/getting-started/installation/) · [Docker installation](https://docs.docker.com/get-docker/)

~~~sh
uv sync --locked
uv run --locked python -c 'import sqlite3, sys; print(sys.version.split()[0], sqlite3.sqlite_version)'
uv run --locked inspect list tasks benchmark.py
uv run --locked pytest -m 'not docker'
~~~

Task discovery should list `benchmark.py@model_benchmark` and `benchmark.py@agent_benchmark`. The test command verifies grading and runs the model mode with scripted responses and actual MCP calls. It needs no API key. For the same check in Docker, start Docker and run:

~~~sh
docker info
docker compose version
uv run --locked pytest -m docker
~~~

Use the bundled `data/seed.db` for the published cases. See [data provenance and rebuild instructions](../DATASET.md) if you need to verify or reconstruct it.

## Run your first evaluation

Pass the Inspect identifier of the model you want to test with `--model`. Both benchmark modes use Inspect to connect to the model from the host. You can use a local model server, a hosted model, or a gateway. If the endpoint requires credentials, configure them in the host environment. [Inspect model providers](https://inspect.aisi.org.uk/providers)

| Provider | Inspect model identifier | API key | Additional SDKs |
| --- | --- | --- | --- |
| OpenAI | `openai/<model>` | `OPENAI_API_KEY` | Included |
| Anthropic | `anthropic/<model>` | `ANTHROPIC_API_KEY` | Add `--extra providers` to `uv run` |
| Google Gemini | `google/<model>` | `GOOGLE_API_KEY` | Add `--extra providers` to `uv run` |

Use a model available to your account. The following example runs one starter case before evaluating the full dataset. A model-backed run can make billable requests under your provider's terms. [Inspect model configuration](https://inspect.aisi.org.uk/models.html)

~~~sh
uv run --locked inspect eval benchmark.py@model_benchmark \
  --model openai/gpt-4.1-mini --sample-id office-date --display plain
uv run --locked inspect eval benchmark.py@model_benchmark \
  --model openai/gpt-4.1-mini --log-dir logs/model
uv run --locked inspect eval benchmark.py@agent_benchmark \
  --model openai/gpt-4.1-mini --log-dir logs/agent
~~~

The first two commands use the fixed IRODA model loop. The third runs the bundled reference executable in a separate container for each trial. See the [agent integration guide](agent.en.md) to substitute your own executable.

### Local models and gateways

With Ollama running on its default port and `qwen3:4b` installed, run a starter case:

~~~sh
uv run --locked inspect eval benchmark.py@model_benchmark \
  --model ollama/qwen3:4b --sample-id office-date
~~~

For an OpenAI-compatible server such as vLLM or llama.cpp, use the model name served by the endpoint. In this example, `local` is the provider label, `my-model` is the served name, and `LOCAL_API_KEY` is the credential Inspect reads. Use a placeholder value for a server that accepts unauthenticated requests. [OpenAI-compatible endpoints](https://inspect.aisi.org.uk/providers#openai-compatible)

~~~sh
uv run --locked inspect eval benchmark.py@model_benchmark \
  --model openai-api/local/my-model --model-base-url http://127.0.0.1:8000/v1 \
  --sample-id office-date
~~~

For an existing LiteLLM proxy, use the deployment alias from its configuration. Set `LITELLM_PROXY_API_KEY` on the host and pass the proxy root URL. [LiteLLM Proxy in Inspect](https://inspect.aisi.org.uk/providers#litellm-proxy)

~~~sh
uv run --locked inspect eval benchmark.py@model_benchmark \
  --model litellm-proxy/my-model --model-base-url http://127.0.0.1:4000 \
  --sample-id office-date
~~~

Use the same model options with `benchmark.py@agent_benchmark`. The container reaches the model through Inspect's bridge, so a local endpoint can stay on the host's loopback interface. The tasks require tool calls. For a chat model whose endpoint lacks native tool calling, try `-M emulate_tools=true` with a compatible adapter such as `openai-api` or `ollama`. Record tool emulation when reporting results because it changes how the model receives tool definitions. [Inspect tool emulation](https://inspect.aisi.org.uk/providers#tool-emulation)

For other backends, use an Inspect provider or add an Inspect model API extension for the backend's interface. [Inspect model providers](https://inspect.aisi.org.uk/providers)

### Run options

The Makefile wraps the same Inspect commands. For example, with Ollama ready:

~~~sh
make eval-model MODEL=ollama/qwen3:4b SAMPLE=office-date
~~~

Use `make eval-agent` for agent mode. Omit `SAMPLE` for a full run. Set `BASE_URL` for a custom endpoint and `LOG_DIR` to override the log directory. Pass extra Inspect flags with `INSPECT_ARGS`, such as `INSPECT_ARGS='--epochs 3 --display plain'`. To load optional provider SDKs, pass `UV_RUN_ARGS='--extra providers'`. Run `make help` for the remaining targets.

| Option | When to use it |
| --- | --- |
| `--sample-id office-date` or `--sample-id quote-follow-up` | Check one case before a full run. |
| `--epochs 3` | Repeat each selected case three times from fresh state. Record the reducer when reporting results. |
| `--max-samples 1` | Run one sample at a time when debugging provider rate limits or Docker resource use. |
| `--turn-limit` and `--time-limit` | Override the 20 model turns and 120 seconds per sample. The external process has a separate 110-second timeout. |
| `--display plain` | Use a compact display in CI or a terminal. |

## Inspect the results

~~~sh
uv run --locked inspect view --log-dir logs --recursive
# Replace this path with the file printed by Inspect.
uv run --locked inspect log dump --header-only logs/model/your-run.eval
~~~

The default `.eval` logs contain run configuration, aggregate scores, sample transcripts, tool calls, timing and available usage information. In Inspect View, open a sample and check the score explanation alongside the tool results and final response. Record run errors and limit events separately from incorrect outcomes. A successful log can contain incorrect answers. See [measurement and reporting](methodology.en.md) for comparisons and what to publish. [Inspect logs](https://inspect.aisi.org.uk/eval-logs.html)

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `uv` is missing or Python is the wrong version | Install uv and run `uv python install 3.12`. Repeat the version check through `uv run`. |
| The lock check fails | Check that `pyproject.toml` and `uv.lock` come from the same revision. Use `uv sync --locked` for evaluations. |
| SQLite is too old | Use a Python 3.12 build linked to SQLite 3.37 or newer. The Python SQLite version matters independently of the `sqlite3` CLI. |
| An SDK or API key is missing | Check the provider prefix, credential and `--extra providers` where applicable. For a provider error, inspect the status and account access before increasing retries. |
| Tool-calling requests fail | Check tool support for the exact model and endpoint. The key-free tests distinguish local harness problems from provider behavior. |
| Docker is unreachable or the image fails to build | Check `docker info`, `docker compose version`, and `docker compose -f environment/compose.yaml build`. Build-time downloads require registry and package access. |
| The external agent exits, returns no result, or cannot discover tools | Check the sample error and stderr. Verify the command, stdin/stdout protocol, MCP URL and headers in the [integration guide](agent.en.md). |
| Write tools are missing or a write is rejected | The answer case is read-only. For manual tests use a seed copy and `--irhato`. Inspect business validation errors before retrying writes. [MCP reference](mcp.en.md) |
| The run finishes with a low score | Check JSON field names and types for read cases. For write cases check the persisted operation, exact fields and unintended side effects in the tool transcript. [Scoring rules](methodology.en.md) |
