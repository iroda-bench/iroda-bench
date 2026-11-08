# Contributing to IRODA

`IRODA / CONTRIBUTOR GUIDE`

Set up the project, verify your changes, and contribute a Hungarian business workflow.

[Magyar](#magyar) · [Project overview](README.en.md)

## Develop and verify

Use the locked environment and run from the project root. The Ruff commands check the benchmark source and tests as configured in `pyproject.toml`. The full suite exercises both runners and needs Docker. The host-only subset is useful for working without Docker. Neither test mode needs a provider key.

~~~sh
uv sync --locked
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked pytest -m 'not docker'
uv run --locked pytest -m docker
~~~

To run the two subsets together, use `uv run --locked pytest`. GitHub Actions runs the locked install, Ruff checks and full suite on Ubuntu. Run an actual model separately when you need evidence about provider behavior. [CI configuration](.github/workflows/ci.yml)

## Add or change a case

1. Pick a stable, unique ID and write a Hungarian prompt with enough information to identify the records, required action, and output format. Avoid dependence on the real calendar.
2. Add one UTF-8 JSON object per line to [the dataset](iroda_bench/tasks.jsonl) with `id`, `prompt`, `kind` and `expected`. The loader rejects unknown fields, empty datasets and duplicate IDs. An `answer` case maps expected keys to strings or integers. A `task_insert` case uses the exact field schema defined by `TaskFields`.
3. Verify the expected result against the versioned seed and MCP surface. Add passing and failing grader tests when introducing a grading rule. Test a plausible wrong answer, duplicate operation or unintended change as applicable.
4. Run both modes against the case when changing shared behavior. Update the case inventory in both methodology guides. Document scoring changes and version or hash differences that affect comparisons. [Grader](iroda_bench/scoring.py) · [Methodology](docs/methodology.en.md)

When growing the dataset beyond the starter pair, update the unit tests to select their fixtures by case ID. They currently unpack the two bundled cases. The integration test's scripted read path expects a reference-date lookup, so add an appropriate scripted tool sequence for new read workflows. [Scoring tests](tests/test_scoring.py) · [Integration tests](tests/test_benchmark.py)

## Prepare a pull request

Use the IRODA design system for changes to the UI, documentation, reports, and communications. [Design system](docs/design-system.en.md)

Describe the behavior change, affected cases and checks run. Keep both language versions of affected documentation in sync. Include the reason for changes to prompts, expected values, grading or seed. For a seed change, keep the schema, generator, snapshot, data documentation and license notices consistent. Build to a separate path before replacing the checked-in copy. When sharing results, use the reporting checklist and remove any credentials or private data from artifacts. [Data documentation](DATASET.md) · [Reporting checklist](docs/methodology.en.md#reproduce-and-report-a-run)

## Magyar

`IRODA / HOZZÁJÁRULÁSI ÚTMUTATÓ`

Készítsd elő a projektet, ellenőrizd a módosításaidat, és adj hozzá magyar nyelvű üzleti feladatot.

[Projektáttekintés](README.md)

### Fejlesztés és ellenőrzés

A lockolt környezetet használd, és a projekt gyökeréből futtasd a parancsokat. A Ruff a `pyproject.toml` szerint a benchmark forrását és tesztjeit ellenőrzi. A teljes csomag mindkét futtatót teszteli, ezért Docker kell hozzá. Docker nélkül a gazdagépes részhalmaz használható. Egyik tesztmódhoz sem kell szolgáltatói kulcs.

~~~sh
uv sync --locked
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked pytest -m 'not docker'
uv run --locked pytest -m docker
~~~

A két részhalmazt együtt az `uv run --locked pytest` futtatja. A GitHub Actions Ubuntun telepíti a rögzített függőségeket, ellenőrzi a forrást Ruff-fal, és lefuttatja a teljes tesztcsomagot. A szolgáltató viselkedéséről külön, éles modellfutással gyűjts bizonyítékot. [CI-konfiguráció](.github/workflows/ci.yml)

### Új eset vagy esetmódosítás

1. Válassz stabil, egyedi azonosítót. A magyar promptból derüljön ki, mely rekordokra vonatkozik a feladat, mit kell tenni, és milyen kimenet kell. Az eset ne függjön a valódi naptártól.
2. Soronként egy UTF-8 kódolású JSON objektumot adj a [feladatfájlhoz](iroda_bench/tasks.jsonl). Mezők: `id`, `prompt`, `kind` és `expected`. A betöltő elutasítja az ismeretlen mezőket, az üres adatkészletet és az ismétlődő azonosítókat. Az `answer` eset kulcsaihoz szöveg vagy egész szám rendelhető. A `task_insert` mezőit a `TaskFields` sémája adja meg.
3. Ellenőrizd az elvárt eredményt a verziózott seeden és az MCP-felületen. Új pontozási szabályhoz adj sikeres és sikertelen teszteket. Az esettől függően próbálj ki hihető, de rossz választ, ismételt műveletet vagy nem kért változást.
4. A közös működés változásakor próbáld ki az esetet mindkét módban. Frissítsd az esetlistát mindkét módszertani útmutatóban. Rögzítsd az összehasonlítást befolyásoló pontozási változásokat, verziókat és lenyomatokat. [Pontozó](iroda_bench/scoring.py) · [Módszertan](docs/methodology.hu.md)

A két mintafeladat bővítésekor állítsd át az egységteszteket azonosító szerinti esetválasztásra. Jelenleg a mellékelt két esetet bontják ki. Az integrációs teszt programozott olvasási útvonala a fordulónapot kéri le, ezért új olvasási munkafolyamathoz adj hozzá megfelelő eszközhívási sort. [Pontozási tesztek](tests/test_scoring.py) · [Integrációs tesztek](tests/test_benchmark.py)

### Pull request előkészítése

Felület, dokumentáció, jelentés vagy kommunikációs anyag módosításakor kövesd az IRODA arculati szabályait. [Arculati és stílusútmutató](docs/design-system.hu.md)

Írd le a viselkedés változását, az érintett eseteket és az elvégzett ellenőrzéseket. Az érintett dokumentáció mindkét változatát frissítsd. Indokold a prompt, elvárt érték, pontozás vagy seed változását. Seedmódosításnál tartsd összhangban a sémát, generátort, adatbázist, adatleírást és licencértesítéseket. Először külön útvonalra építs, majd ellenőrzés után cseréld a verziózott másolatot. Eredménymegosztáskor használd a közlési ellenőrzőlistát, és távolítsd el a hitelesítő és bizalmas adatokat a megosztott fájlokból. [Adatleírás](ADATLEIRAS.md) · [Közlési ellenőrzőlista](docs/methodology.hu.md#futás-reprodukálása-és-közlése)
