# Az IRODA benchmark futtatása

`IRODA / FUTTATÁSI ÚTMUTATÓ`

Készítsd elő a környezetet, futtasd a mintafeladatokat, és nézd meg a futtatási naplókat.

[English](benchmark.en.md) · [Projektáttekintés](../README.md)

## Telepítés és környezetellenőrzés

A parancsokat POSIX shellben, a projekt gyökerében futtasd. A benchmark Python 3.12-t igényel, amely SQLite 3.37-es vagy újabb verzióhoz kapcsolódik. Először telepítsd az uv-t. A CI az uv 0.7.12-es verzióját használja. A modellmód konténer nélkül fut. Az agentmódhoz futó Docker Engine vagy Docker Desktop és Docker Compose v2 kell. Az első telepítés Python-csomagokat tölt le, az első agentfutás pedig a Docker-image-et is megépíti. [uv telepítése](https://docs.astral.sh/uv/getting-started/installation/) · [Docker telepítése](https://docs.docker.com/get-docker/)

~~~sh
uv sync --locked
uv run --locked python -c 'import sqlite3, sys; print(sys.version.split()[0], sqlite3.sqlite_version)'
uv run --locked inspect list tasks benchmark.py
uv run --locked pytest -m 'not docker'
~~~

A feladatlista a `benchmark.py@model_benchmark` és a `benchmark.py@agent_benchmark` bejegyzéseket mutatja. A tesztparancs ellenőrzi a pontozást, és programozott modellválaszokkal, tényleges MCP-hívásokkal futtatja a modellmódot. Ehhez nem kell API-kulcs. A Dockeres ellenőrzéshez indítsd el a Dockert, majd futtasd:

~~~sh
docker info
docker compose version
uv run --locked pytest -m docker
~~~

A közzétett feladatokhoz a mellékelt `data/seed.db` fájlt használd. Az ellenőrzést és az újraépítést az [adatleírás](../ADATLEIRAS.md) ismerteti.

## Az első kiértékelés

A tesztelendő modell Inspect-azonosítóját a `--model` kapcsolóval add meg. Mindkét benchmarkmódban az Inspect kapcsolódik a modellhez a gazdagépről. Használhatsz helyi modellszervert, hosztolt modellt vagy átjárót. Ha a végpont hitelesítést igényel, állítsd be a gazdagép környezetében. [Az Inspect modellszolgáltatói](https://inspect.aisi.org.uk/providers)

| Szolgáltató | Inspect-modellazonosító | API-kulcs | Kiegészítő SDK-k |
| --- | --- | --- | --- |
| OpenAI | `openai/<modell>` | `OPENAI_API_KEY` | Az alaptelepítés része |
| Anthropic | `anthropic/<modell>` | `ANTHROPIC_API_KEY` | Az `uv run` kapcsolóihoz add hozzá a `--extra providers` opciót |
| Google Gemini | `google/<modell>` | `GOOGLE_API_KEY` | Az `uv run` kapcsolóihoz add hozzá a `--extra providers` opciót |

Olyan modellt adj meg, amely a fiókodban elérhető. A példa egyetlen mintafeladattal kezd, majd a teljes feladatkészletet futtatja. A szolgáltatói modellhívások díjkötelesek lehetnek. [Inspect modellkonfiguráció](https://inspect.aisi.org.uk/models.html)

~~~sh
uv run --locked inspect eval benchmark.py@model_benchmark \
  --model openai/gpt-4.1-mini --sample-id office-date --display plain
uv run --locked inspect eval benchmark.py@model_benchmark \
  --model openai/gpt-4.1-mini --log-dir logs/model
uv run --locked inspect eval benchmark.py@agent_benchmark \
  --model openai/gpt-4.1-mini --log-dir logs/agent
~~~

Az első két parancs az IRODA rögzített modellciklusát használja. A harmadik minden próbálkozásnál külön konténerben indítja a mellékelt referencia-agentet. Saját futtatható programhoz lásd az [agentintegrációs útmutatót](agent.hu.md).

### Helyi modellek és átjárók

Ha az Ollama az alapértelmezett porton fut, és a `qwen3:4b` modell telepítve van, próbáld ki az egyik mintafeladatot:

~~~sh
uv run --locked inspect eval benchmark.py@model_benchmark \
  --model ollama/qwen3:4b --sample-id office-date
~~~

OpenAI-kompatibilis szervernél, például vLLM vagy llama.cpp esetén a végponton elérhető modellnevet add meg. Ebben a példában a `local` a szolgáltató címkéje, a `my-model` a modell neve, a `LOCAL_API_KEY` pedig az Inspect által olvasott hitelesítési változó. Ha a szerver hitelesítés nélkül is fogad kéréseket, adj meg egy helyőrző értéket. [OpenAI-kompatibilis végpontok](https://inspect.aisi.org.uk/providers#openai-compatible)

~~~sh
uv run --locked inspect eval benchmark.py@model_benchmark \
  --model openai-api/local/my-model --model-base-url http://127.0.0.1:8000/v1 \
  --sample-id office-date
~~~

Meglévő LiteLLM proxyhoz a konfigurációban megadott modellálnevet használd. Állítsd be a `LITELLM_PROXY_API_KEY` változót a gazdagépen, és add meg a proxy alapcímét. [LiteLLM proxy az Inspectben](https://inspect.aisi.org.uk/providers#litellm-proxy)

~~~sh
uv run --locked inspect eval benchmark.py@model_benchmark \
  --model litellm-proxy/my-model --model-base-url http://127.0.0.1:4000 \
  --sample-id office-date
~~~

Ugyanezeket a modellbeállításokat használhatod a `benchmark.py@agent_benchmark` feladattal is. A konténer az Inspect hídján éri el a modellt, így a helyi végpont maradhat a gazdagép loopback interfészén. A feladatok eszközhívásokat igényelnek. Ha egy chatmodell végpontja nem támogatja ezeket natívan, próbáld ki az `-M emulate_tools=true` opciót olyan adapterrel, amely támogatja, például az `openai-api` vagy az `ollama` adapterrel. Az eredmények közlésekor jelöld az emulációt, mert megváltoztatja, hogyan kapja meg a modell az eszközök leírását. [Eszközhívások emulálása az Inspectben](https://inspect.aisi.org.uk/providers#tool-emulation)

Más háttérrendszerhez használj meglévő Inspect-adaptert, vagy adj hozzá Inspect Model API-bővítményt a háttérrendszer interfészéhez. [Az Inspect modellszolgáltatói](https://inspect.aisi.org.uk/providers)

### Futtatási kapcsolók

A Makefile ugyanezeket az Inspect-parancsokat futtatja. Ha az Ollama fut és a modell elérhető, próbáld ki az egyik mintafeladatot:

~~~sh
make eval-model MODEL=ollama/qwen3:4b SAMPLE=office-date
~~~

Agentmódhoz használd a `make eval-agent` parancsot. A teljes futtatáshoz hagyd el a `SAMPLE` változót. Egyedi végponthoz add meg a `BASE_URL` értékét, a naplómappa felülírásához a `LOG_DIR` értékét. További Inspect-kapcsolókat az `INSPECT_ARGS` változóval adhatsz meg, például `INSPECT_ARGS='--epochs 3 --display plain'`. Az opcionális szolgáltatói SDK-k betöltéséhez add meg az `UV_RUN_ARGS='--extra providers'` beállítást. A többi parancsot a `make help` listázza.

| Kapcsoló | Mire használható? |
| --- | --- |
| `--sample-id office-date` vagy `--sample-id quote-follow-up` | Egy eset kipróbálása a teljes futás előtt. |
| `--epochs 3` | Minden kiválasztott eset három ismétlése friss állapotból. Az eredmények közlésekor rögzítsd az összesítés módját. |
| `--max-samples 1` | Soros futtatás szolgáltatói limit vagy Docker-erőforrások vizsgálatához. |
| `--turn-limit` és `--time-limit` | A mintánkénti 20 modellforduló és 120 másodperc felülírása. A külső agentfolyamatnak külön 110 másodperces időkorlátja van. |
| `--display plain` | Egyszerű megjelenítés CI-ben vagy terminálban. |

## Az eredmények megtekintése

~~~sh
uv run --locked inspect view --log-dir logs --recursive
# Cseréld az útvonalat az Inspect által kiírt naplófájléra.
uv run --locked inspect log dump --header-only logs/model/your-run.eval
~~~

Az alapértelmezett `.eval` naplók tartalmazzák a futtatási konfigurációt, az összesített pontokat, a minták párbeszédét, az eszközhívásokat, az időadatokat és az elérhető használati adatokat. Az Inspect View-ban nyisd meg a mintát, majd a pontozás indoklása mellett nézd meg az eszközeredményeket és a végső választ. A futtatási hibákat és a limit elérését a helytelen eredményektől elkülönítve rögzítsd. A sikeresen befejezett futtatásban is lehetnek helytelen válaszok. Lásd a [mérési és közlési módszertant](methodology.hu.md). [Inspect naplók](https://inspect.aisi.org.uk/eval-logs.html)

## Hibakeresés

| Tünet | Ellenőrzés |
| --- | --- |
| Hiányzik az `uv`, vagy eltér a Python-verzió | Telepítsd az uv-t, futtasd az `uv python install 3.12` parancsot, majd ellenőrizd a verziót az `uv run` alatt. |
| A lockfájl ellenőrzése sikertelen | Ellenőrizd, hogy a `pyproject.toml` és az `uv.lock` ugyanabból a revízióból származik. Kiértékeléshez használd az `uv sync --locked` parancsot. |
| Túl régi az SQLite | Olyan Python 3.12-t használj, amely SQLite 3.37-hez vagy újabbhoz kapcsolódik. A Python SQLite-verziója eltérhet a `sqlite3` parancsétól. |
| Hiányzik az SDK vagy az API-kulcs | Ellenőrizd a szolgáltatói előtagot, a kulcsot és szükség esetén a `--extra providers` opciót. Szolgáltatói hibánál a státuszt és a hozzáférést ellenőrizd a további próbálkozások előtt. |
| Az eszközhívás sikertelen | Ellenőrizd az adott modell és végpont eszközhívási támogatását. Az API-kulcs nélküli tesztek elkülönítik a helyi hibát a szolgáltató viselkedésétől. |
| A Docker nem érhető el, vagy a build hibázik | Ellenőrizd a `docker info`, a `docker compose version` és a `docker compose -f environment/compose.yaml build` kimenetét. A buildhez el kell érni az image-regisztereket és a csomagtárat. |
| Az agent kilép, üres választ ad, vagy nem talál eszközt | Nézd meg a minta hibáját és a standard hibakimenetet. Ellenőrizd a parancsot, a bemeneti és kimeneti formátumot, az MCP URL-t és a fejléceket. [Agentintegráció](agent.hu.md) |
| Hiányzik az íróeszköz, vagy az írás hibázik | A válaszfeladat olvasási módú. Kézi tesztnél készíts seedmásolatot, és add meg az `--irhato` kapcsolót. Újrapróbálás előtt olvasd el az üzleti validációs hibát. [MCP-referencia](mcp.hu.md) |
| A futás befejeződik, de alacsony a pontszám | Olvasásnál ellenőrizd a JSON-mezők nevét és típusát. Írásnál nézd meg a mentett műveletet, a pontos mezőket és a mellékhatásokat az eszköznaplóban. [Pontozási szabályok](methodology.hu.md) |
