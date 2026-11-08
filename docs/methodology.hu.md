# Mérési és közlési módszertan

`IRODA / MÓDSZERTAN`

Itt találod, mit mér a két mód, hogyan zajlik a pontozás, és mit kell rögzíteni egy reprodukálható összehasonlításhoz.

[English](methodology.en.md) · [Futtatási útmutató](benchmark.hu.md)

## Mit mér a két mód?

| Mód | Rögzített elemek | Változó elemek |
| --- | --- | --- |
| `model_benchmark` | Feladat, seed, magyar rendszerprompt, MCP-felület és az Inspect eszközhívási ciklusa kikapcsolt párhuzamos eszközhívással | Modell, szolgáltatói végpont és generálási beállítások |
| `agent_benchmark` | Feladat, seed, megengedett irodai műveletek, pontozás és benchmarklimitek | Agentprogram, promptok, memória, vezérlés és eszközkezelés. Az Inspect-modell külön választható. |

Az első módban azonos beállításokkal hasonlítsd össze a modelleket. Az agent vezérlésének hatását ugyanazzal a pontos modellverzióval és ugyanazokkal a feladatokkal mérd mindkét módban. Rögzítsd az eltérő generálási beállításokat, átviteli módokat és limiteket. Az agentmódban a program a híd által támogatott API keretein belül saját generálási opciókat adhat meg. Ezeket az agent konfigurációjával együtt közöld.

## A próbálkozás életciklusa és elkülönítése

1. A gazdagép beolvassa és validálja az esetet az `iroda_bench/tasks.jsonl` fájlból.
2. Minden próbálkozás és ismétlés a `data/seed.db` saját ideiglenes másolatából indul. A gazdagép ehhez a másolathoz új stdio MCP-munkamenetet indít.
3. Modellmódban az Inspect a rögzített rendszerpromptot, a magyar feladatszöveget és a felderített eszközöket adja át a modellnek. Az eszközeredményeket visszaküldi, amíg a modell megáll vagy eléri valamelyik limitet.
4. Agentmódban a kiválasztott program Docker-sandboxban fut. Az Inspect helyi végpontokon továbbítja a hívásokat a kiválasztott modellhez és az irodai eszközökhöz. A mellékelt image nem tartalmazza a seedet, a válaszokat vagy a pontozót. A mellékelt Compose-konfiguráció futás közben letiltja a külső hálózatot. Az egyedi Compose-fájl maga határozza meg az elkülönítést.
5. A gazdagépen futó pontozó a végső választ vagy a futási adatbázist olvassa. A futtató a pontozás után eltávolítja az ideiglenes adatbázist. Az Inspect a naplóban őrzi a futás nyomvonalát és pontszámát. Ha művelet után adatbázist szeretnél vizsgálni, indíts kézi MCP-munkamenetet külön másolaton.

A pontozás alapja a seedben rögzített irodai fordulónap. A tényleges idő a futási teljesítmény és a végrehajtási limitek méréséhez számít.

## Feladatok és pontozás

| Azonosító | A feladat röviden | Pontozás |
| --- | --- | --- |
| `office-date` | Add vissza az iroda fordulónapját és pénznemét JSON objektumban. | `answer` |
| `quote-follow-up` | Hozz létre pontosan egy nyitott, magas prioritású követési feladatot a 20003-as ajánlathoz Szőke Lilla számára, 2026. november 12-i határidővel, a megadott címmel és leírással. A többi üzleti rekord maradjon változatlan. | `task_insert` |

A pontos promptok és az elvárt értékek a verziózott [JSONL fájlban](../iroda_bench/tasks.jsonl) vannak. Mindkét mód az eredeti magyar promptokat küldi. Az angol összefoglaló az olvasóknak szól.

- **`answer`**. Csak olvasási eszközök érhetők el. A pontozó a szélső szóközök és sortörések levágása után JSON objektumként értelmezi a végső szöveget. Egyetlen, kisbetűs `json` jelölésű, sortörésekkel határolt kódblokk is elfogadott. Az elvárt kulcsok értékének és típusának egyeznie kell. További kulcsok szerepelhetnek. A prózai válasz, a hiányzó kulcs vagy az egész szám helyett szövegként kódolt szám helytelen eredményt ad.
- **`task_insert`**. Az íróeszközök is elérhetők. A pontozó olvasási módban nyitja meg a seedet és a futási másolatot. Pontosan egy, a seed legnagyobb feladatazonosítójánál nagyobb azonosítójú sort vár. Ellenőrzi a kért mezőket, majd sorrendtől függetlenül összehasonlítja a seed üzleti tábláinak összes többi sorát. Egy meglévő feladat módosítása, a dupla beszúrás vagy más üzleti tábla változása helytelen eredményt ad. Több helyes eszközsorrend is sikerhez vezethet. A végső szöveg és a köztes műveletek nem számítanak bele ebbe a pontba.

A pontozott próbálkozás `C` (helyes) vagy `I` (helytelen) eredményt ad. Az Inspect pontossági mutatója ezeket 1-re és 0-ra képezi le. Ismétlésnél az alapértelmezett összesítés feladatonként átlagol, majd összesíti a feladatok pontjait. Közöld, hány próbálkozás kapott pontot, volt-e limitelérés, és hogyan kezelted a hibákat vagy a befejezetlen mintákat. Részleges futásnál jelöld a tényleges lefedettséget.

## Futás reprodukálása és közlése

Őrizd meg a pontos parancsot és a futtatási naplót. A napló `eval.metadata` mezőjében a `seed_sha256` és a `tasks_sha256` bájtszinten azonosítja a bemeneti fájlokat. A projektverziót, a konténert és a szolgáltatói modellverziót külön rögzítsd.

~~~sh
git rev-parse HEAD
uv --version
uv run --locked python -c 'import platform, sqlite3; print(platform.platform(), platform.python_version(), sqlite3.sqlite_version)'
docker version
uv run --locked inspect log export-config logs/model/your-run.eval > run.yaml
~~~

A Git-parancsot klónozott repóban, a Docker-parancsot konténeres futásnál használd. A napló elérési útját cseréld ki az Inspect által kiírtra. Az exportált konfiguráció az `inspect eval --run-config run.yaml` paranccsal tölthető be. Ehhez az eredeti projektrevízióra, modellhozzáférésre és az agent image-ére vagy buildkörnyezetére is szükség van. Megosztás előtt ellenőrizd a naplókat és az exportot, hogy nem tartalmaznak-e hitelesítő adatokat vagy bizalmas információt. [Inspect futtatási konfiguráció és naplók](https://inspect.aisi.org.uk/eval-logs.html)

Közzétett összehasonlítás mellé add meg az alábbi adatokat.

| Tétel | Rögzítendő adatok |
| --- | --- |
| Bemenet | Commit vagy kiadás, seed- és feladatlenyomat, esetazonosítók és a tervezett ismétlések száma feladatonként |
| Konfiguráció | Benchmarkmód, pontos modell és szolgáltató, a futtatás dátuma, mintavételezés, ismétlésszám és összesítés, párhuzamosság és limitek |
| Agent és környezet | Az agent forrásrevíziója, parancsa, az image címkéje vagy lenyomata, egyedi Compose-fájl és teljesítménymérésnél a gazdagép platformja |
| Eredmények | Helyes és helytelen próbálkozások száma feladatonként, futtatási hibák, elért limitek, befejezetlen próbálkozások, valamint az újrapróbálás és kizárás szabálya |
| Teljesítmény | Futási idő és elérhető használati adatok próbálkozásonként vagy megadott nevezővel összesítve. Költségbecslésnél a díjadat forrása. |

A két eset nyilvános mintafeladat, közzétett elvárt eredményekkel. A futtató és az alapvető irodai műveletek ellenőrzésére szolgálnak. A kis és nyilvános minta korlátozza, hogy mit lehet belőle a modellek minőségére vagy ismeretlen feladatokra következtetni. A szolgáltatói frissítések és a modell mintavételezése azonos helyi bemenet mellett is eltérő eredményhez vezethet. A tesztcsomag programozott modellválaszokkal ellenőrzi a pontozást és a tényleges MCP-hívásokat, Dockerben is. Éles szolgáltatói teljesítményt a kiértékelések mérnek.
