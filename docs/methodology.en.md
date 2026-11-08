# Measurement and reporting

`IRODA / METHODOLOGY`

See what each mode measures, how trials are graded, and what to record for a reproducible comparison.

[Magyar](methodology.hu.md) · [Run guide](benchmark.en.md)

## What the two modes measure

| Mode | Held fixed | What can vary |
| --- | --- | --- |
| `model_benchmark` | Case, seed, Hungarian system prompt, MCP surface, and Inspect tool-call loop with parallel tool calls disabled | Model and its serving endpoint and generation settings |
| `agent_benchmark` | Case, seed, allowed office operations, grading rules and benchmark limits | Agent executable, prompts, memory, orchestration and tool handling. The Inspect model is selected independently. |

Compare models in the first mode under the same settings. To measure the effect of an agent harness, use the same exact model revision and the same cases in both modes. Record any differences in generation settings, transport and budgets. In agent mode, the executable can set its own generation options within the bridge's supported API. Report those options with the agent configuration.

## Trial lifecycle and isolation

1. The host loads and validates the case from `iroda_bench/tasks.jsonl`.
2. Each trial, including each epoch, starts with its own temporary copy of `data/seed.db`. The host starts a new stdio MCP session for that copy.
3. In model mode Inspect sends the fixed system prompt, Hungarian case prompt and discovered tools to the model. It feeds tool results back until the model stops or a limit applies.
4. In agent mode a Docker sandbox runs the selected executable. Inspect forwards calls to the selected model and office tools through local endpoints. The bundled image has no seed, answers or grader and the bundled Compose configuration disables external networking at runtime. A custom Compose file controls its own isolation.
5. The host grader reads the final response or the trial database. The runner removes the temporary database after scoring. Inspect retains the trace and score in the evaluation log. To inspect a live database after operations, use a manual MCP session on a separate copy.

The grading environment uses the office reference date from the seed. Current wall-clock time is relevant to performance and deadlines for execution only.

## Cases and grading

| ID | English description of the Hungarian prompt | Grading |
| --- | --- | --- |
| `office-date` | What are the IRODA reference date and currency? Return a JSON object with `fordulonap` (YYYY-MM-DD) and `penznem` (ISO currency code). | `answer` |
| `quote-follow-up` | Create exactly one open, high-priority follow-up for quote 20003, assigned to Szőke Lilla and due 12 November 2026. The title is “Decemberi ajánlat követése” (Follow up on December's quote). The description is “Egyeztesd a vevővel a decemberi készletpótlást.” (Coordinate December stock replenishment with the customer.) Leave other business records unchanged. | `task_insert` |

The exact prompts and expected values are versioned in [the JSONL dataset](../iroda_bench/tasks.jsonl). Both modes send the original Hungarian prompts. English descriptions are provided for readers.

- **`answer`** exposes read-only tools. The grader parses the final text as a JSON object after trimming surrounding whitespace. It also accepts one enclosing lowercase `json` code fence with line breaks. Expected keys must have matching values and types. Extra keys are accepted. An answer in prose, a missing key, or a number encoded as a string where an integer was expected fails.
- **`task_insert`** also exposes the write tools. The grader opens the seed and trial copy read-only. It requires exactly one row with an ID above the seed's maximum task ID, compares the requested fields, then compares all remaining rows of the seed's application tables, independent of row order. Existing task edits, a duplicate insert or changes in another business table fail. The grader uses the final state, so different valid tool sequences can pass. The final message and intermediate actions do not affect this score.

Scored trials produce `C` (correct) or `I` (incorrect). Inspect's accuracy metric maps these to 1 and 0. With repeated epochs the default reducer takes the mean per case before aggregation. Report which trials received a score, whether any limits were reached, and how errors or incomplete samples were handled. Do not present a partial run as coverage of the full dataset.

## Reproduce and report a run

Save the exact command and the evaluation log. The log's `eval.metadata` contains `seed_sha256` and `tasks_sha256`. These identify the input files byte for byte. They do not identify your checkout, container, or provider revision.

~~~sh
git rev-parse HEAD
uv --version
uv run --locked python -c 'import platform, sqlite3; print(platform.platform(), platform.python_version(), sqlite3.sqlite_version)'
docker version
uv run --locked inspect log export-config logs/model/your-run.eval > run.yaml
~~~

Use the Git command in a clone and the Docker command for container runs. Replace the log path with the one produced by Inspect. Inspect can load the exported configuration with `inspect eval --run-config run.yaml`. Use the original project revision, model access, and agent image or build context as well. Review logs and exported configurations for credentials or private data before sharing. [Inspect run configuration and logs](https://inspect.aisi.org.uk/eval-logs.html)

Include the following with any published comparison.

| Item | Record |
| --- | --- |
| Inputs | Commit or release, seed and task hashes, case IDs, and the number of scheduled trials per case |
| Configuration | Benchmark mode, exact model and provider, run date, sampling settings, epochs and reducer, concurrency and limits |
| Agent and environment | Agent source revision, command, image tag or digest, any custom Compose file, and host platform for performance claims |
| Outcomes | Correct and incorrect counts by case, run errors, limits reached, incomplete trials and any retry or exclusion policy |
| Performance | Runtime and available usage per trial or aggregate with a defined denominator. State the source for any cost estimate. |

The two cases are public starter cases with public expected results. They check the wiring and basic office operations. Their size and exposure limit conclusions about model quality or unseen workflows. A released result is an observation for a recorded configuration. Provider updates and model sampling can change results even when local inputs match. The test suite exercises the grading logic and real MCP paths using scripted model responses, including Docker. It establishes local integration behavior and leaves live provider performance to evaluation runs.
