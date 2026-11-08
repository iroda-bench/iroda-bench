# Agent integrálása

`IRODA / AGENTINTEGRÁCIÓ`

Ez az útmutató az `agent_benchmark` módban értékelt futtatható agentekhez szól. A repót módosító agentek az [AGENTS.md](../AGENTS.md#magyar) fájllal kezdjenek.

[English](agent.en.md) · [Futtatási útmutató](benchmark.hu.md) · [MCP-referencia](mcp.hu.md)

## Build és futtatás

1. Telepítsd a gazdagép függőségeit, majd az `uv run --locked pytest -m docker` paranccsal ellenőrizd a mellékelt Docker-agentet.
2. Építsd a futtatható programot, függőségeit és statikus fájljait Linux-image-be. Kiindulásként használd a [Dockerfile-t](../environment/Dockerfile) és a [Compose-fájlt](../environment/compose.yaml). Ha bővíted a mellékelt buildkörnyezetet, engedélyezd az új forrásfájlokat a [`.dockerignore`](../.dockerignore) fájlban, vagy használj külön buildkörnyezetet. A benchmarkadatok, elvárt válaszok és kulcsok maradjanak az agent image-én és fájlrendszer-csatolásain kívül.
3. A Compose-fájlban adj meg egy futó `default` szolgáltatást tartós paranccsal, például `sleep infinity`-vel. Összehasonlítható izolált futáshoz tartsd meg a `network_mode: none` beállítást. A modellproxy és az MCP-proxy a konténer loopback felületén elérhető marad.
4. Add meg a modellt a `--model` kapcsolóval a [futtatási útmutató](benchmark.hu.md) szerint. Először az olvasási esetet, majd az írási esetet és a teljes benchmarkot futtasd.

~~~sh
uv run --locked inspect eval benchmark.py@agent_benchmark \
  --model openai/gpt-4.1-mini --sample-id office-date \
  --sandbox docker:/abszolut/utvonal/compose.yaml \
  -T 'command=python /app/my_agent.py'
~~~

A futtató argumentumokra bontja a parancsot, és közvetlenül indítja el. Shellszkriptet vagy CLI-adaptert az image-be telepíts. Teljes példát a [referencia-agent](../environment/example_agent.py) ad.

## A futtatható program szerződése

| Felület | Szerződés |
| --- | --- |
| stdin | Egy magyar feladatprompt UTF-8 kódolással, a végén EOF. |
| stdout | A végső válasz UTF-8 kódolással. A futtató levágja a szélső szóközöket és sortöréseket. Ha a feladat JSON objektumot kér, egyetlen objektumot írj ki. |
| stderr és kilépési állapot | A diagnosztikát az stderr-re írd. A nem nulla kilépés futtatási hiba, amelynek üzenetébe az stderr vége is bekerül. |
| `IRODA_MCP_CONFIG` | JSON objektum a helyi Streamable HTTP MCP-szerverhez. Kapcsolódáskor használd a `url` értékét és a megadott `headers` mezőt. Inicializáld a munkamenetet, majd a `tools/list` hívással kérd le az eszközöket. A konfiguráció próbálkozásonként eltérhet. |
| `IRODA_MODEL` | A modell `inspect` aliasa. Ezt add meg a proxynak küldött kérésekben. A tényleges szolgáltatói modellt a gazdagép futtatója választja ki. |
| `OPENAI_BASE_URL` | A helyi modellproxy alap URL-je, `/v1` végződéssel. |
| `ANTHROPIC_BASE_URL` | A helyi Anthropic-kompatibilis proxy alap URL-je. |
| `GOOGLE_GEMINI_BASE_URL` | A helyi Google-kompatibilis proxy alap URL-je, `/v1beta` végződéssel. |

Ha az SDK kulcsot kér a helyi proxyhoz, adj meg helyőrzőt. A szolgáltatói kulcsok a mellékelt konfigurációban a gazdagépen maradnak. A referencia-agent a Chat Completions felületet és az MCP Python-klienst használja. Más kliensnél használd a futtató által megadott végpontokat, és vedd figyelembe a híd korlátait. A saját bejelentkezést vagy közvetlen külső szolgáltatásokat igénylő CLI-hez adapter kellhet. [Inspect Agent Bridge](https://inspect.aisi.org.uk/agent-bridge.html)

## Az irodai eszközök használata

- Olvasd el a feladatot, és az élő MCP-munkamenetben derítsd fel az eszközöket. Íróeszközök csak az írási esetekben jelennek meg. A magyar eszköz- és enumneveket pontosan add meg.
- A szimulált dátumot az `irodai_kornyezet` adja meg. További hívásokhoz használd a visszaadott azonosítókat, lapozáshoz a `kovetkezo_eltolas` mezőt. Összegek vagy kapcsolatok ellenőrzéséhez olvasd be a részleteket.
- Csak a kért műveletet végezd el. Elveszett válasz után írási újrapróbálás előtt olvasd vissza az állapotot. A megismételt létrehozás két rekordot hagyhat, és helytelen eredményt adhat.
- A futás közbeni napló az stderr-re kerüljön. A kért végső választ az stdout-ra írd akkor is, ha a pontszámot az adatbázis állapota adja.

A híd az agentprogram közvetlen MCP-hívásait is átengedi. A fordulólimit a modellkérésekre vonatkozik. Az eszközhívások a futási időt terhelik. A gazdagép pontozza az esetet az adatbázismásolat törlése előtt. A pontozó, az elvárt értékek és ez az útmutató a futási prompton kívül maradnak. További instrukciók vagy feladatspecifikus válaszok beillesztése megváltoztatja a mért konfigurációt. Eredményközléskor rögzítsd az egyedi promptokat és eszközöket.
