# Instructions for repository agents

`IRODA / REPOSITORY GUIDE`

These instructions apply to work in this repository. Executables being evaluated use the [agent integration contract](docs/agent.en.md).

[Magyar](#magyar)

## Start here

- Read the [IRODA design system](docs/design-system.en.md) before creating or changing project UI, documentation, reports or communications.
- Read the [run guide](docs/benchmark.en.md) and the [measurement methodology](docs/methodology.en.md) before changing the harness.
- `benchmark.py` registers the two Inspect tasks. `iroda_bench/runner.py` owns trial setup, execution and cleanup. `iroda_bench/scoring.py` owns dataset validation and deterministic grading.
- `mcp_server.py` registers tools. `iroda.py` owns business behavior and transactions. `schema.sql` and `scripts/build_seed.py` define the starting dataset.
- `environment/` defines the reference external agent. `tests/` covers scoring, real MCP calls with a scripted model, and the automatable design-system rules.

## Working rules

- Run commands from the project root. Install with `uv sync --locked`. Use `uv run --locked` for repository commands. Update the lockfile only when changing dependencies.
- Keep the benchmark prompts and MCP identifiers in Hungarian. Keep both language versions of affected documentation in sync. Stable case IDs and unchanged tool contracts are important for comparing releases.
- Use a temporary copy for any write test. Keep trial databases, expected results and provider credentials outside the agent container. Preserve the upstream license notices. Rebuild the seed to a separate path when checking the generator.
- The model and agent modes share cases and scoring. Validate both when changing shared setup, tool exposure, grading or the bridge. The public starter cases should never become hard-coded behavior in the reference agent.
- Keep local secrets, logs and trial files out of commits. Describe the exact checks run and any verification gaps in the change summary.

~~~sh
uv sync --locked
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked pytest -m 'not docker'
uv run --locked pytest -m docker
~~~

The final command requires Docker. These checks use no provider credentials. See [Contributing](CONTRIBUTING.md) for adding cases or preparing a change.

## Magyar

`IRODA / ÚTMUTATÓ A REPÓHOZ`

Ezek az instrukciók a repóban végzett munkára vonatkoznak. A benchmarkban értékelt programokra az [agentintegrációs szerződés](docs/agent.hu.md) érvényes.

### Kiindulópont

- Felület, dokumentáció, jelentés vagy kommunikációs anyag készítése vagy módosítása előtt olvasd el az [IRODA arculati és stílusútmutatóját](docs/design-system.hu.md).
- A futtató módosítása előtt olvasd el a [futtatási útmutatót](docs/benchmark.hu.md) és a [mérési módszertant](docs/methodology.hu.md).
- A `benchmark.py` regisztrálja a két Inspect-feladatot. Az `iroda_bench/runner.py` kezeli a próbálkozás előkészítését, futtatását és takarítását. Az `iroda_bench/scoring.py` validálja a feladatokat és végzi a determinisztikus pontozást.
- A `mcp_server.py` regisztrálja az eszközöket. Az `iroda.py` kezeli az üzleti műveleteket és a tranzakciókat. A kiinduló adatbázist a `schema.sql` és a `scripts/build_seed.py` határozza meg.
- Az `environment/` tartalmazza a külső referencia-agentet és környezetét. A `tests/` ellenőrzi a pontozást, a valódi MCP-hívásokat programozott modellel és az automatizálható arculati szabályokat.

### Munkaszabályok

- A projekt gyökeréből futtasd a parancsokat. Telepítéshez használd az `uv sync --locked`, a projektparancsokhoz az `uv run --locked` előtagot. A lockfájlt függőségváltoztatáskor frissítsd.
- A benchmarkpromptok és az MCP-azonosítók magyarul maradnak. Az érintett dokumentáció mindkét nyelvű változatát frissítsd. A stabil feladatazonosítók és a változatlan eszközszerződések szükségesek a kiadások összevetéséhez.
- Írási teszthez ideiglenes másolatot használj. A futási adatbázis, az elvárt eredmények és a szolgáltatói kulcsok maradjanak az agentkonténeren kívül. Őrizd meg az upstream licencértesítéseket. A generátor ellenőrzésekor külön útvonalra építsd a seedet.
- A két futtatási mód feladatai és pontozása közös. A közös előkészítés, eszközök, pontozás vagy híd módosításakor ellenőrizd mindkét módot. A referencia-agentbe ne kódold bele a nyilvános mintafeladatok megoldását.
- A helyi kulcsok, naplók és futási fájlok maradjanak ki a commitokból. A változtatás összefoglalójában add meg, milyen ellenőrzéseket futtattál, és mi maradt ellenőrizetlen.

~~~sh
uv sync --locked
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked pytest -m 'not docker'
uv run --locked pytest -m docker
~~~

Ezek a parancsok API-kulcs nélkül futnak. Az utolsó parancshoz Docker kell. Új esethez vagy módosításhoz lásd a [hozzájárulási útmutatót](CONTRIBUTING.md#magyar).
