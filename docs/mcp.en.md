# IRODA MCP reference

`IRODA / OFFICE TOOLS`

Run the office server, inspect its tool schemas, and look up the available read and write operations.

[Magyar](mcp.hu.md) · [Project overview](../README.en.md)

## Start or inspect the server

The benchmark starts and configures the server automatically. For standalone use, `uv run mcp_server.py` starts the local stdio server with the script's pinned MCP SDK. The script requires Python 3.11 or newer and SQLite 3.37 or newer. The benchmark environment uses Python 3.12. The default database is the bundled seed in read-only mode. Run the following after `uv sync --locked` to list the read-only schemas and query the office environment without an LLM. For write schemas, pass `--adatbazis` with a separate database copy and add `--irhato` to the script arguments. [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/v1/)

~~~sh
uv run --locked python - <<'PY'
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command=sys.executable, args=["mcp_server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for tool in (await session.list_tools()).tools:
                print(tool.name, json.dumps(tool.inputSchema, ensure_ascii=False))
            result = await session.call_tool("irodai_kornyezet", {})
            print(json.dumps(result.structuredContent, ensure_ascii=False))

asyncio.run(main())
PY
~~~

For an MCP client, replace the three example absolute paths with the paths on your machine. Run the shell commands first to create a fresh database for a writable session. For a read-only session, omit `--irhato` and optionally omit `--adatbazis` and its argument to open the seed.

~~~sh
run_dir=$(mktemp -d)
cp data/seed.db "$run_dir/run.db"
~~~

~~~json
{
  "mcpServers": {
    "iroda": {
      "command": "/absolute/path/to/uv",
      "args": [
        "run", "/absolute/path/to/Iroda/mcp_server.py",
        "--adatbazis", "/absolute/path/to/run.db", "--irhato"
      ]
    }
  }
}
~~~

For Codex CLI, register the copied database using the first command below, then verify the entry. The second block illustrates a per-tool approval override for a manually managed, unattended run. Replace its prompt with your actual task. Use a fresh copy for a new trial and remove or update the registered entry when it no longer points to the intended copy. The bundled benchmark configures its own server. [OpenAI Docs for Codex MCP](https://learn.chatgpt.com/docs/extend/mcp#other-configuration-options)

~~~sh
codex mcp add iroda -- "$(command -v uv)" run "$PWD/mcp_server.py" \
  --adatbazis "$run_dir/run.db" --irhato
codex mcp list
~~~

~~~sh
codex exec --skip-git-repo-check \
  -c 'mcp_servers.iroda.tools.feladat_letrehozas.approval_mode="approve"' \
  'Használd az IRODA MCP-eszközeit az itt megadott feladathoz.'
~~~

## Arguments and results

- Tool names, fields and enum values use the exact Hungarian strings exposed by the live MCP schema. Search by display number to resolve an internal ID when needed. For instance, `ajanlat_reszletek` expects the integer `ajanlat_id`.
- `ugy` references a case. Example: `{"tipus":"ajánlat","azonosito":20003}`. The other case types are `rendelés` and `számla`.
- Dates use `YYYY-MM-DD`. A date range is an object with `ettol`, `eddig` or both. Both bounds are inclusive. For dates relative to the office, read `fordulonap`. Overdue invoices have a due date before that date and an outstanding balance.
- Search filters combine with AND. Text filters are case-insensitive substring searches in the fields documented by the tool. Each search returns `talalatok` and `kovetkezo_eltolas`. Set `oldal` to `{"darab":20,"eltolas":0}` for the first page. The default size is 20 and the maximum is 100. On each next page, retain the filters and set `eltolas` to the returned offset. A null offset means the last page.
- Money values in HUF are whole forints. Discount values are basis points, where 500 means 5%. Where returned, email timestamps are Budapest local time.
- Prefer structured results when the client supports them. Check the MCP error flag and error text. A failing write rolls back that tool call. Successful writes persist in the run copy across server restarts. Each call has its own transaction, so later failures do not undo earlier writes.

## Read tools

All search tools accept `oldal` in addition to the arguments below. The live schema specifies types, optional fields and enums.

| Tool | Arguments | Purpose |
| --- | --- | --- |
| `irodai_kornyezet` | — | Snapshot date, timezone, currency, dataset name and write mode. |
| `partner_kereses` | `szoveg`, `tipus`, `partner_id`, `telepules` | Companies by name, code, email, type, ID or locality. |
| `kapcsolattarto_kereses` | `szoveg`, `partner_id`, `elsodleges` | Partner contacts, optionally only primary contacts. |
| `munkatars_kereses` | `szoveg`, `munkatars_id`, `vezeto_id` | Employees and their reporting relationships. |
| `termek_kereses` | `szoveg`, `kategoria`, `beszallito_id`, `kifutott`, `keszlet_legfeljebb` | Products by SKU, name, category, supplier or stock. |
| `szerzodes_kereses` | `szoveg`, `vevo_id`, `felelos_id`, `lejarat`, `ervenyes_ekkor` | Framework contracts, terms and text. |
| `ajanlat_kereses` | `szoveg`, `vevo_id`, `felelos_id`, `allapot`, `kelte`, `lejarat`, `rendezes` | Quotes by status, issue date or expiry. |
| `ajanlat_reszletek` | `ajanlat_id` | Quote header, contact and line items. |
| `rendeles_kereses` | `szoveg`, `vevo_id`, `felelos_id`, `ajanlat_id`, `fuvarozo_id`, `allapot`, `kelte`, `kert_szallitas` | Orders with quote, carrier and delivery filters. |
| `rendeles_reszletek` | `rendeles_id` | Order, delivery address, carrier, items and invoice reference if present. |
| `szamla_kereses` | `szoveg`, `vevo_id`, `rendeles_id`, `fizetesi_allapot`, `lejart`, `kelte`, `hatarido`, `rendezes` | Invoice balances, payment status and overdue flag. |
| `szamla_reszletek` | `szamla_id` | Invoice header, balance, items and recorded payments. |
| `email_kereses` | `szoveg`, `ugy`, `vevo_id`, `levelezes_id`, `irany`, `felado`, `cimzett`, `idoszak`, `rendezes` | Search subject and body, returning headers and case references. |
| `email_olvasas` | `email_id` | Full email body with header and case reference. |
| `feladat_kereses` | `szoveg`, `feladat_id`, `ugy`, `vevo_id`, `felelos_id`, `allapot`, `tipus`, `prioritas`, `hatarido` | Tasks sorted by earliest due date first. |

## Write tools

Write tools appear only when the server starts with `--irhato` on a separate database. The seed itself cannot be opened writable through IRODA. The live schema is authoritative for required and optional fields. Update tools apply supplied non-null fields from `valtozas`. The recipient of an outgoing email must match the case customer or a contact on that customer. Email and payments update the simulated office only.

| Tool | Arguments | Purpose |
| --- | --- | --- |
| `ajanlat_modositas` | `ajanlat_id`, `valtozas` | Update selected quote fields. A contact must belong to the quote's customer. Closing records the snapshot date. |
| `feladat_letrehozas` | `ugy`, `felelos_id`, `cim`, `leiras`, `hatarido`, `prioritas`, `allapot` | Create a follow-up. Case determines customer and task type. Initial status is open or in progress. |
| `feladat_modositas` | `feladat_id`, `valtozas` | Update selected task fields. Marking it done or cancelled records the snapshot date. |
| `email_kuldes` | `felado_id`, `cimzett`, `targy`, `uzenet`, `ugy`, `levelezes_id`, `valasz_erre_id` | Record simulated outbound email. Use exactly one of case or thread. A reply must reference the same thread. |
| `befizetes_rogzitese` | `szamla_id`, `tranzakcioszam`, `ertek_nap`, `osszeg_ft`, `kozlemeny` | Record a payment with a unique transaction number. Value date is between invoice issue date and snapshot date, inclusive. |

For a multi-step workflow, read the office date, search sent quotes expiring before it, then check the matching quote's existing tasks with `feladat_kereses`. Look up the owner and confirm the correct case ID. If the task calls for a write, create one follow-up and read it back using the returned ID. The business logic is in [iroda.py](../iroda.py) and the tool registration is in [mcp_server.py](../mcp_server.py).
