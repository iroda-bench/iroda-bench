<img src="docs/design/mark.svg" width="40" height="40" alt="">

# IRODA

`A BENCHMARK ELŐZETESE / v0.1.0`

**Boldogulnak az AI-agentek a magyar üzleti feladatokkal?**

Az IRODA (*Intelligent Reasoning for Office Decisions and Actions*) nyílt forráskódú magyar nagyvállalati benchmark nyelvi modellek és agentek mérésére magyar nyelvű üzleti feladatokon.

[![MIT-licenc](https://img.shields.io/badge/licenc-MIT-193536)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-193536)](#gyors-kezdés)
[![SQLite 3.37 vagy újabb](https://img.shields.io/badge/SQLite-3.37%2B-193536)](#gyors-kezdés)

[English](README.en.md) · [Gyors kezdés](#gyors-kezdés) · [Dokumentáció](#dokumentáció) · [Hozzájárulás](CONTRIBUTING.md#magyar)

## Gyors kezdés

A parancsokat a repó gyökeréből futtasd. Make, uv és legalább SQLite 3.37-tel működő Python 3.12 szükséges. A feladatok listázásához és a helyi tesztekhez nem kell szolgáltatói API-kulcs vagy Docker.

~~~sh
make setup
make tasks
make check
~~~

A kiértékelési és naplóparancsokat a `make help` listázza. A konténeres teszthez Docker és Compose v2 szükséges. Modellalapú értékeléshez állítsd be a szolgáltatót, és válassz eszközhívást támogató modellt. [Futtatási útmutató](docs/benchmark.hu.md) · [Agentintegráció](docs/agent.hu.md) · [CI-konfiguráció](.github/workflows/ci.yml)

## Jelenlegi állapot

Két nyilvános mintafeladat ellenőrzi a futtatás teljes folyamatát. A feladatleírások és az elvárt eredmények az alaptesztekhez is elérhetők. [Mintafeladatok](iroda_bench/tasks.jsonl)

> `ÜGYIRAT / 02` · **A 20003-as ajánlat nyomon követése**
>
> Hozz létre pontosan egy nyitott, magas prioritású követési feladatot a 20003-as ajánlathoz Szőke Lilla számára, 2026. november 12-i határidővel.
>
> *A feladatleírás első mondata.* [Teljes feladatleírás](iroda_bench/tasks.jsonl)

| Feladat | Mit ellenőriz a pontozó? |
| --- | --- |
| `office-date` | A strukturált válasz az iroda fordulónapját és pénznemét tartalmazza. |
| `quote-follow-up` | Pontosan egy új feladat jön létre a kért ajánlattal, felelőssel, határidővel, címmel, leírással, prioritással és állapottal. Minden más üzleti rekord változatlan. |

## Hogyan működik?

Az IRODA azt méri, hogy a modellek és agentek megtalálják-e a megfelelő üzleti rekordokat, pontos választ adnak-e, és a kért módosításokat végzik-e el az irodai eszközökkel. A feladatok a fiktív **Rézrigó Élelmiszer-nagykereskedelmi Kft.** adataira épülnek. Az adatkészletben vevők, ajánlatok, rendelések, számlák, befizetések, e-mailek és feladatok kapcsolódnak egymáshoz. A verziózott SQLite-adatbázis a Northwind üzleti kapcsolatait magyar törzsadatokkal és szintetikus munkafolyamatokkal egészíti ki. [Adatleírás és források](ADATLEIRAS.md)

Minden próbálkozás ugyanannak az SQLite-adatbázisnak egy friss másolatából indul. A vizsgált rendszer magyar nyelvű feladatot kap, és a Model Context Protocol (MCP) felületén éri el az üzleti eszközöket. A determinisztikus pontozó a strukturált választ vagy az adatbázis végállapotát ellenőrzi. Az írási mintafeladatnál azt is vizsgálja, hogy történt-e nem kért módosítás a meglévő rekordokban. [Mérési módszertan](docs/methodology.hu.md)

| Mód | Mit mér? |
| --- | --- |
| Modellbenchmark (`model_benchmark`) | A nyelvi modell teljesítményét az Inspect AI rögzített eszközhívási ciklusában. |
| Agentbenchmark (`agent_benchmark`) | Az agent teljesítményét a teljes feladat során. Az agent saját promptokkal és vezérléssel fut egy Docker-konténerben. A mellékelt referencia-agent mellett saját agent is futtatható. |

A két mód ugyanazokat a feladatokat, üzleti eszközöket és pontozási szabályokat használja.

## Ütemterv

1. **További üzleti munkafolyamatok.** Többlépéses feladatok több rekordot érintő kereséssel, hasonló rekordok megkülönböztetésével és az írási műveletek mellékhatásainak ellenőrzésével.
2. **Reprodukálható összehasonlítások közzététele.** Külön modell- és agenteredmények a futtatási beállításokkal, a feladatverziókkal, az esetenkénti eredményekkel, valamint a hibák és a befejezetlen próbálkozások kezelésének leírásával.

## Dokumentáció

| Téma | Magyar | English |
| --- | --- | --- |
| Telepítés, futtatás és naplók | [Futtatási útmutató](docs/benchmark.hu.md) | [Run guide](docs/benchmark.en.md) |
| Pontozás, reprodukálhatóság és eredményközlés | [Módszertan](docs/methodology.hu.md) | [Methodology](docs/methodology.en.md) |
| Saját agent futtatása | [Agentintegráció](docs/agent.hu.md) | [Agent integration](docs/agent.en.md) |
| Üzleti eszközök és önálló MCP-szerver | [MCP-referencia](docs/mcp.hu.md) | [MCP reference](docs/mcp.en.md) |
| Adatforrások, séma és a kiinduló adatbázis újraépítése | [Adatleírás](ADATLEIRAS.md) | [Dataset](DATASET.md) |
| Felületek és kommunikáció arculata | [Arculati és stílusútmutató](docs/design-system.hu.md) | [Design system](docs/design-system.en.md) |

## Hozzájárulás

Szívesen fogadunk új magyar nyelvű üzleti feladatokat, pontozási fejlesztéseket és dokumentációs javításokat. A hozzájárulási útmutató ismerteti a feladatazonosítók és az elvárt eredmények megadását, valamint a két futtatási mód ellenőrzését. [Hozzájárulási útmutató](CONTRIBUTING.md#magyar) · [Útmutató a repóban dolgozó agenteknek](AGENTS.md#magyar)

## Licenc

Az IRODA saját kódja és dokumentációja MIT-licencű. A Northwindből származó adatok terjesztésekor őrizd meg az eredeti licencértesítéseket. Ezeket a kiinduló adatbázis `licenc_ertesites` táblája is tartalmazza. [MIT-licenc](LICENSE) · [Eredeti licencértesítések](sources/)
