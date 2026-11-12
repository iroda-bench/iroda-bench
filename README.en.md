<img src="docs/design/mark.svg" width="40" height="40" alt="">

# IRODA

`BENCHMARK PREVIEW / v0.1.0`

**Can AI agents handle Hungarian business tasks?**

IRODA (*Intelligent Reasoning for Office Decisions and Actions*) is an open-source Hungarian enterprise benchmark for language models and agents working on Hungarian-language business tasks.

[![MIT license](https://img.shields.io/badge/license-MIT-193536)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-193536)](#quick-start)
[![SQLite 3.37 or newer](https://img.shields.io/badge/SQLite-3.37%2B-193536)](#quick-start)

[Magyar](README.md) · [Website](https://www.irodabench.hu/en/) · [Quick start](#quick-start) · [Documentation](#documentation) · [Contributing](CONTRIBUTING.md)

## Quick start

Run the commands from the repository root with Make, uv, and Python 3.12 with SQLite 3.37 or newer. Task discovery and local tests need no provider API key or Docker.

~~~sh
make setup
make tasks
make check
~~~

Run `make help` for evaluation and log commands. The container test requires Docker with Compose v2. For a model-backed evaluation, configure a provider and select a model with tool-calling support. [Run guide](docs/benchmark.en.md) · [Agent integration](docs/agent.en.md) · [CI configuration](.github/workflows/ci.yml)

## Project status

Two public starter cases exercise the harness end to end. Their prompts and expected results are available for smoke testing. [Starter cases](iroda_bench/tasks.jsonl)

> `CASE FILE / 02` · **Follow up on quote 20003**
>
> Create exactly one open, high-priority follow-up task for quote 20003, assigned to Szőke Lilla and due 12 November 2026.
>
> *English translation of the first sentence of the prompt.* [Original Hungarian prompt](iroda_bench/tasks.jsonl)

| Case | What the grader checks |
| --- | --- |
| `office-date` | The structured answer contains the office reference date and currency. |
| `quote-follow-up` | Exactly one task is added with the requested quote, assignee, deadline, title, description, priority, and status. All other business records stay intact. |

## How it works

IRODA measures whether models and agents can find the right business records, return accurate answers, and make precise changes through office tools. The setting is **Rézrigó Élelmiszer-nagykereskedelmi Kft.**, a fictional Hungarian food wholesaler with linked customer, quote, order, invoice, payment, email, and task records. The versioned SQLite dataset combines Northwind business relationships with Hungarian master data and synthetic workflows. [Dataset and provenance](DATASET.md)

Each trial starts from a fresh copy of the same SQLite snapshot. The system under evaluation receives a Hungarian task and uses business tools exposed through the Model Context Protocol (MCP). A deterministic grader checks the structured answer or the final database state. For the bundled write case, it also checks for unintended changes to existing records. [Measurement methodology](docs/methodology.en.md)

| Mode | What it measures |
| --- | --- |
| Model benchmark (`model_benchmark`) | A language model's performance in a fixed Inspect AI tool-calling loop. |
| Agent benchmark (`agent_benchmark`) | An agent's end-to-end performance with its own prompts and orchestration in a Docker container. Use the bundled reference agent or supply your own. |

Both modes share the same cases, business tools, and grading rules.

## Roadmap

1. **Expand workflow coverage.** Add multi-step cases that require searching across records, distinguishing similar records, and performing writes with checks for unintended changes.
2. **Publish reproducible comparisons.** Report model and agent results separately, with run settings, task versions, per-case outcomes, and how errors and incomplete trials were handled.

## Documentation

| Topic | English | Magyar |
| --- | --- | --- |
| Setup, evaluations, and logs | [Run guide](docs/benchmark.en.md) | [Futtatási útmutató](docs/benchmark.hu.md) |
| Scoring, reproducibility, and reporting | [Methodology](docs/methodology.en.md) | [Módszertan](docs/methodology.hu.md) |
| Running your own agent | [Agent integration](docs/agent.en.md) | [Agentintegráció](docs/agent.hu.md) |
| Business tools and standalone server | [MCP reference](docs/mcp.en.md) | [MCP-referencia](docs/mcp.hu.md) |
| Data provenance, schema, and seed rebuild | [Dataset](DATASET.md) | [Adatleírás](ADATLEIRAS.md) |
| Design system for UI and communications | [Design system](docs/design-system.en.md) | [Arculati és stílusútmutató](docs/design-system.hu.md) |

## Contributing

Contributions are welcome, including Hungarian business cases, grader improvements, and documentation fixes. The contributor guide covers case IDs, expected results, and verification in both modes. [Contributing](CONTRIBUTING.md) · [Repository agent instructions](AGENTS.md)

## License

IRODA's original code and documentation are MIT licensed. Retain the upstream notices when redistributing derived Northwind data. The seed also includes those notices in the `licenc_ertesites` table. [MIT license](LICENSE) · [Upstream notices](sources/)

## Citation

If you use IRODA in a publication or report, the citation metadata is in `CITATION.cff`. GitHub also generates BibTeX from it. [Citation metadata](CITATION.cff)
