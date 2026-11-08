# Integrate an agent

`IRODA / AGENT INTEGRATION`

This guide is for executable agents evaluated by `agent_benchmark`. Agents modifying the repository should start with [AGENTS.md](../AGENTS.md).

[Magyar](agent.hu.md) · [Run guide](benchmark.en.md) · [MCP reference](mcp.en.md)

## Build and run

1. Install the host dependencies and verify the bundled Docker agent with `uv run --locked pytest -m docker`.
2. Build your executable, dependencies, and any static assets into a Linux image. Start with the [bundled Dockerfile](../environment/Dockerfile) and [Compose file](../environment/compose.yaml). If you extend the bundled build context, allow the new source files in [`.dockerignore`](../.dockerignore) or use a dedicated context. Keep benchmark data, expected answers and credentials outside the agent image and filesystem mounts.
3. In your Compose file, provide a running `default` service with a long-lived command such as `sleep infinity`. Keep the bundled `network_mode: none` for a comparable isolated run. The model and MCP proxies remain reachable on container loopback.
4. Select the model with `--model` as described in the [run guide](benchmark.en.md). Start with a single read case, then try the write case and the complete run.

~~~sh
uv run --locked inspect eval benchmark.py@agent_benchmark \
  --model openai/gpt-4.1-mini --sample-id office-date \
  --sandbox docker:/absolute/path/compose.yaml \
  -T 'command=python /app/my_agent.py'
~~~

The runner splits the command into arguments and executes it without a shell. Install wrappers into the image if you need a shell script or a CLI-specific adapter. Review the [reference executable](../environment/example_agent.py) for a complete example.

## Executable contract

| Interface | Contract |
| --- | --- |
| stdin | One Hungarian task prompt in UTF-8, followed by EOF. |
| stdout | Final answer in UTF-8. The runner trims surrounding whitespace. Emit a single JSON object for tasks that request one. |
| stderr and exit status | Use stderr for diagnostics. A nonzero exit is a run error, with the end of stderr included in the error message. |
| `IRODA_MCP_CONFIG` | JSON object for the local Streamable HTTP MCP server. Use `url` and pass any `headers` when connecting. Initialize a session and discover the tools with `tools/list`. The configuration can differ per attempt. |
| `IRODA_MODEL` | The model alias `inspect`. Use it in requests to the model proxy. The host runner selects the real provider model. |
| `OPENAI_BASE_URL` | Local model proxy base URL, including `/v1`. |
| `ANTHROPIC_BASE_URL` | Local Anthropic-compatible proxy base URL. |
| `GOOGLE_GEMINI_BASE_URL` | Local Google-compatible proxy base URL, including `/v1beta`. |

Use a placeholder if your SDK requires a key for the loopback proxy. Provider credentials stay on the host in the bundled setup. The reference agent uses the Chat Completions interface and the MCP Python client. Other clients should honor the endpoints supplied by the runner and any limitations of the bridge. A CLI that requires its own login or direct external services may need an adapter. [Inspect Agent Bridge](https://inspect.aisi.org.uk/agent-bridge.html)

## Use the office tools

- Read the case prompt and discover the available tools from the live MCP session. The write tools only appear for write cases. Preserve the exact Hungarian tool and enum names.
- Use `irodai_kornyezet` for the simulated date, returned IDs for subsequent calls, and `kovetkezo_eltolas` to traverse search pages. Check detailed records before relying on amounts or relationships.
- Limit writes to the requested operation. If a response is lost, read the state before repeating a write. A repeated creation can leave two records and fail grading.
- Keep progress logs on stderr. Use stdout for the requested final result even if the score is based on database state.

The bridge allows direct programmatic MCP calls by the executable. The model-turn limit covers model requests. Tool requests still consume trial time. The host grades the trial before removing its database copy. The grader, expected values, and this guide are outside the runtime prompt. Injecting extra instructions or case-specific answers into an agent changes the configuration being evaluated. Record custom prompts and tools when publishing a result.
