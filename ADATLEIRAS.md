# IRODA 0.1.0 adatleírás

`IRODA / ADATKÉSZLET / v0.1.0`

Nézd meg, honnan származnak az adatok, mit tartalmaz a séma, és hogyan építhető újra a kiinduló adatbázis (seed).

[English](DATASET.md) · [Projektáttekintés](README.md)

A 2026. november 8-i pillanatkép egy magyar belföldi B2B élelmiszer-nagykereskedést modellez. Egy szintetikus cégnév, utcanév vagy személynév esetleges valós egyezése véletlen. Az adószámmezők szándékosan érvénytelen tesztértékek. Az e-mail-címek a tesztelésre fenntartott `.invalid` tartományban vannak. [RFC 2606](https://datatracker.ietf.org/doc/html/rfc2606)

## Források és licencek

| Forrás | Szerep és licenc |
| --- | --- |
| [Northwind SQLite3, rögzített verzió](https://github.com/jpwhite3/northwind-SQLite3/tree/4f56e7f5906dfd23b25244c5bfe8fb5da6402efd) | Tényleges adatforrás. A klasszikus mintát a `src/create.sql`, majd a `src/update.sql` futtatásával építjük fel memóriában. Az MIT-licenc és a © 2016 JP White értesítés változtatás nélkül szerepel a [licencmásolatban](sources/LICENSE-Northwind-SQLite3.txt). |
| [Microsoft SQL Server Northwind](https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/northwind-pubs) | Kiegészítő eredetjelölés. Az upstream saját leírása szerint az Access 2000-es mintát alakította át. A Microsoft külön közzétett, MIT-licencű SQL Server-változatából közvetlen import nem történt. A Microsoft-értesítés a [licencmásolatban](sources/LICENSE-Microsoft-SQL-Samples.txt) szerepel. |
| [DemoDB Northwind](https://northwind.demodb.dev/about/) | Ellenőrzési referencia a klasszikus állomány és a véletlenszerű rendelésekkel bővített `dist/northwind.db` megkülönböztetéséhez. A generátor közvetlenül az upstream SQL-fájlokat használja. |
| IRODA | Saját magyar megfeleltetések, szintetikus rekordok, üzleti szabályok, generátor, séma és dokumentáció. Az új hozzájárulások MIT-licencét a [LICENSE](LICENSE) tartalmazza. A Northwindből származó részekkel az upstream értesítést is tovább kell adni. |
| [NAV Online Számla](https://github.com/nav-gov-hu/Online-Invoice) | Szerkezeti referencia a számla kelte, teljesítési napja, fizetési határideje és a nettó, áfa- és bruttó összegek elkülönítéséhez. A repó [MIT-licencű](https://github.com/nav-gov-hu/Online-Invoice/blob/master/LICENCE.md). XSD, XML, mintaszámla, szöveg és kód nincs átvéve. |
| [Hungarian Invoice Catalog Decisions](https://huggingface.co/datasets/k3dani/hu-invoice-catalog-decisions) | Áttekintett, CC BY 4.0-ként jelölt tételazonosítási adatkészlet. A kiadás számlái saját rendelésekből képződnek, ezért innen nem importáltunk rekordot. |
| [Synthetic Hungarian Document OCR Dataset](https://huggingface.co/datasets/GaborMadarasz/synthetic_OCR_dataset) | Áttekintett, Apache-2.0-ként jelölt adatkészlet. A kiadásba nem került kép vagy szöveg. |

A települések, vármegyék és a példaként választott irányítószámok kézzel összeállított földrajzi adatok. A kiadás nem tartalmaz cégjegyzékből, beszámolókból vagy irányítószám-adatbázisból letöltött rekordokat. A termékenkénti áfabesorolás szimulált. [Magyar Posta irányítószám-formátumok](https://www.posta.hu/ugyfelszolgalat/nemzetkozi_iranyitoszam_formatumok), [Áfa tv.](https://njt.hu/jogszabaly/2007-127-00-00.82)

A forrásokat és a licencjelöléseket 2026. november 8-án ellenőriztük. A rögzített fájlok lenyomatai az adatbázis `adatforras` táblájában is elérhetők.

| Bemenet | SHA-256 |
| --- | --- |
| [create.sql](https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/4f56e7f5906dfd23b25244c5bfe8fb5da6402efd/src/create.sql) | `5854b536dea3fe8c586223bf7b47a793727dd44c34fc32537a68a97fec8e2f4b` |
| [update.sql](https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/4f56e7f5906dfd23b25244c5bfe8fb5da6402efd/src/update.sql) | `59df0f3c88b1878946b712cc6e8a7f37c971c802ff2ed611c59feb72acb39ea6` |
| [Upstream MIT-értesítés](https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/4f56e7f5906dfd23b25244c5bfe8fb5da6402efd/LICENSE) | `c28e204be6418b87ae1c83127096aad9c9e1a218c365f8f4d630e84d8ba96c47` |
| [Microsoft MIT-értesítés](https://raw.githubusercontent.com/microsoft/sql-server-samples/4693087abebd7e835f9ee46d005dcdaa03092a40/license.txt) | `201f3705979e932c92cd3c6ddbddf4dc3c71dcc5a82089a1e4018227cfe1cf09` |

## Magyarítás és transzformációk

| Terület | Megőrzött forráselemek és változtatások |
| --- | --- |
| Cégek, címek és kapcsolattartók | A `Customers`, `Suppliers` és `Shippers` egy közös partnertörzsbe került. Vevőazonosító az eredeti kulcs szerint rendezett 1-től induló sorszám, beszállítóazonosító az eredeti azonosító +100, fuvarozóazonosító +200. A cégnevek, magyar jogi formák, beosztások, kapcsolattartók, utcák, házszámok és elérhetőségek szintetikusak. Egyes vevők külön pénzügyi kapcsolattartót vagy a székhelytől eltérő szállítási címet kaptak. |
| Munkatársak | Az azonosítók és a közvetlen vezetői kapcsolatok megmaradtak. A családnév–utónév sorrend, az új nevek, munkakörök és elérhetőségek magyar irodai környezethez készültek. |
| Termékek | A termék–kategória–beszállító kapcsolatok, készletszámok, utánrendelési küszöb és kifutott jelölés megmaradtak. A [77 soros megfeleltetés](scripts/termekek.txt) rögzíti a magyar terméknevet, a metrikus vagy darabos kiszerelést és a szimulált áfakulcsot. A készlet a forrás pillanatképe, készletmozgás-napló nem képződik a rendelésekből. |
| Rendelések | Megmaradt a rendelésazonosító és a vevő, felelős, fuvarozó, termék, mennyiség és kedvezmény kapcsolata. A tételsorszám a termékazonosító sorrendjét követi. A rendelés, kért szállítás és feladás dátuma azonos eltolást kapott. A legkésőbbi rendelés dátuma 2026. november 6. A feladást 1–3 nap múlva követi a szintetikus teljesítés. Ha ez a fordulónapon túlra esik, a rendelés feladott marad. A feladás nélküli rendelések között lemondott és feldolgozás alatt álló rekordok is vannak. |
| Pénzösszegek | A forrás egységárait és fuvardíjait 400-as szorzóval, fél felfelé egész forintra kerekítve skáláztuk. A szorzó generálási paraméter. A kedvezmény egész bázispont, 500 bp = 5%. A kedvezmény utáni nettót, majd az ebből számított áfát külön, tételenként egész forintra kerekítjük. A bruttó a nettó és az áfa összege. |
| Ajánlatok és szerződések | Az elfogadott ajánlatok a kapcsolt rendelés tételeit tükrözik. A többi ajánlat saját dátumot, tételt és állapotot kapott, köztük fordulónapon lejáró, korábban lejárt, egyeztetett és piszkozat rekordokat. Egyes vevőknek rövid, szintetikus keretszerződésük van. Az ajánlat és rendelés a saját napján érvényes vevői szerződésre hivatkozik. |
| Számlák és befizetések | A teljesített rendeléshez egy számla tartozik. A pozitív fuvardíj külön számlasor. A fizetési határidő a számla keltétől számított naptári nap. A vevő és a keretszerződés feltételei egyeznek. A fizetési minta egyösszegű kiegyenlítést, több jóváírást, részfizetést és nyitott tartozást tartalmaz. A számlák benchmarkrekordok, a NAV-adatszolgáltatás és a könyvelés kívül esik a modellen. |
| Levelezés és feladatok | A magyar szövegek saját sablonokból készültek, a konkrét ügy azonosítóival, neveivel és határidejével. Az ajánlathoz, szállításhoz és fizetési emlékeztetőhöz tartozó szálakban lehet bejövő válasz. A feladatokhoz felelős, prioritás, határidő és állapot tartozik. |
| Elhagyott elemek | Eredeti nevek, címek, telefonok, faxok, URL-ek, fotók, kategóriaképek, életrajzi jegyzetek, demográfiai és területi táblák, eredeti nézetek. A nyers SQL-források nincsenek a csomagban. |

## Adatszótár

A technikai mezőnevek ékezet nélküli magyar azonosítók. A megjelenő szövegek és állapotértékek ékezetesek. Az `id` egész belső kulcs, a `kod`, `cikkszam` és bizonylatszám megjeleníthető egyedi kulcs. A naptári dátum `YYYY-MM-DD`, az e-mail időpontja budapesti helyi idő `YYYY-MM-DDTHH:MM:SS` formában. A `NULL` hiányzó vagy nem alkalmazható érték.

| Táblák és nézet | Szerep |
| --- | --- |
| `metaadat`, `adatforras`, `licenc_ertesites` | Verzió, fordulónap, időzóna, származás és teljes licencszövegek. |
| `telepules`, `partner`, `kapcsolattarto`, `munkatars` | Földrajzi minták, partnertípusok, kapcsolattartók és hierarchia. |
| `termekkategoria`, `termek` | Cikkszám, kiszerelés, beszállító, ár, áfa és készletjelzők. |
| `szerzodes`, `ajanlat`, `ajanlattetel` | Keretfeltételek, ajánlati állapot és tételek. Az ajánlat lejárata dátumfeltétel, a lezárás külön művelet. |
| `rendeles`, `rendelestetel` | Rendelés, opcionális ajánlat és szerződés, szállítás, fuvarozó és tételek. |
| `szamla`, `szamlatetel`, `befizetes` | Számlafej, tételadatok, számított sorösszegek és könyvelt jóváírások. A fuvardíjsor `termek_id` értéke `NULL`. |
| `szamla_egyenleg` | Számlaösszegek, befizetett összeg és hátralék. A `lejart` akkor 1, ha a határidő a fordulónap előtt van és maradt tartozás. |
| `levelezes`, `email`, `feladat` | Ajánlathoz, rendeléshez vagy számlához tartozó ügykezelés. Az összetett idegen kulcsok a megfelelő vevőhöz és levélfolyamhoz kötik a rekordokat. |

## Újraépítés és ellenőrzés

A generátor a Python standard könyvtárát használja. Python 3.10+ és SQLite 3.37+ szükséges. Az alábbi parancsok a benchmark rögzített Python 3.12-környezetét és az SQLite parancssori kliensét használják. Külön útvonalra építs, hogy a mellékelt bemenet összehasonlítható maradjon.

~~~sh
out=$(mktemp -d)
uv run --locked python scripts/build_seed.py --output "$out/seed.db"
sqlite3 -readonly "$out/seed.db" 'PRAGMA integrity_check; PRAGMA foreign_key_check;'
sqlite3 -readonly data/seed.db .dump > "$out/bundled.sql"
sqlite3 -readonly "$out/seed.db" .dump > "$out/rebuilt.sql"
diff -u "$out/bundled.sql" "$out/rebuilt.sql"
~~~

Az integritásvizsgálat `ok` eredményt ad, utána az idegenkulcs-ellenőrzésnek üresnek kell lennie. Azonos logikai tartalomnál a diff nem ír ki eltérést. Azonos rekordokból eltérő SQLite-verziók eltérő adatbázisfájlt készíthetnek. A futtatási naplók bájtszintű lenyomatainak összevetéséhez a mellékelt seedet használd. Offline építéshez töltsd le a fent rögzített bemeneteket, nevezd el őket `create.sql` és `update.sql` néven, majd add meg a könyvtárukat a `--source-dir /utvonal/northwind` kapcsolóval. A licencmásolatok a `sources/` könyvtárban vannak. `--output` nélkül a generátor az ellenőrzés után lecseréli a mellékelt seedet.

A generátor ellenőrzi a forrás- és licencfájlok lenyomatait, a klasszikus rekorddarabszámokat, az SQLite integritását, az idegen kulcsokat, a fő kapcsolatok tételszintű egyezését és a befizetések, illetve válaszlevelek időrendjét. A pillanatképre épülnek az [MCP-eszközök](docs/mcp.hu.md) és a [benchmarkfeladatok](docs/methodology.hu.md).
