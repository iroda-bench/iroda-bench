# IRODA MCP-referencia

`IRODA / IRODAI ESZKÖZÖK`

Indítsd el az irodai szervert, nézd meg az eszközök sémáját, és keresd ki az olvasási és írási műveleteket.

[English](mcp.en.md) · [Projektáttekintés](../README.md)

## A szerver indítása és ellenőrzése

A benchmark automatikusan elindítja és konfigurálja a szervert. Önálló használathoz az `uv run mcp_server.py` indítja a helyi stdio szervert a szkriptben rögzített MCP SDK-val. A szkript Python 3.11-et vagy újabbat és SQLite 3.37-et vagy újabbat igényel. A benchmark Python 3.12-t használ. A szerver alapból olvasási módban nyitja meg a seedet. Az `uv sync --locked` után az alábbi parancs LLM nélkül listázza az olvasási sémákat és lekéri az iroda beállításait. Az írási sémákhoz adj meg külön adatbázismásolatot a `--adatbazis` kapcsolóval, és add a szkript argumentumaihoz az `--irhato` opciót. [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/v1/)

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

MCP-klienshez cseréld le a három példaútvonalat a saját abszolút útvonalaidra. Írható munkamenethez először futtasd a shellparancsokat, hogy friss adatbázismásolatot kapj. Olvasási módhoz hagyd el az `--irhato` kapcsolót. A seed közvetlen olvasásához a `--adatbazis` és az útvonal is elhagyható.

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

Codex CLI-ben az első blokk parancsával regisztráld a másolatot, majd ellenőrizd a bejegyzést. A második blokk egy eszközre szűkített jóváhagyási beállítást mutat egy kézzel kezelt, felügyelet nélküli futáshoz. A promptot cseréld le a tényleges feladatra. Új futáshoz használj friss másolatot, és frissítsd vagy távolítsd el a regisztrációt, amikor már másik másolatra van szükség. A mellékelt benchmark saját szervert konfigurál. [OpenAI Docs a Codex MCP-ről](https://learn.chatgpt.com/docs/extend/mcp#other-configuration-options)

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

## Argumentumok és eredmények

- Az eszközök, mezők és enumértékek az élő MCP-sémában szereplő magyar neveket használják. Szükség esetén keresd meg a megjelenített bizonylatszámhoz tartozó belső azonosítót. Például az `ajanlat_reszletek` egész számként kéri az `ajanlat_id`-t.
- Az `ugy` az ügyre hivatkozik. Például `{"tipus":"ajánlat","azonosito":20003}`. A másik két ügytípus a `rendelés` és a `számla`.
- A dátum alakja `YYYY-MM-DD`. A dátumtartomány `ettol`, `eddig` vagy mindkét mezőt tartalmazó objektum. Mindkét határnap beleértendő. Az irodai időszámítás alapja a `fordulonap`. Akkor lejárt egy számla, ha a fizetési határideje a fordulónap előtt volt, és maradt hátraléka.
- A keresési szűrők együttesen érvényesek. A szövegszűrők kis- és nagybetűtől független részszöveget keresnek az eszköznél jelzett mezőkben. A keresők `talalatok` és `kovetkezo_eltolas` mezőt adnak vissza. Az első oldalhoz az `oldal` értéke lehet `{"darab":20,"eltolas":0}`. Az alapértelmezett méret 20, a maximum 100. A következő oldalakhoz tartsd meg a szűrőket, és add át a kapott értéket az `eltolas` mezőben. A null az utolsó oldalt jelzi.
- A HUF-összegek egész forintok. A kedvezmény bázispontban szerepel, 500 értéke 5%. A levélidőpontok budapesti helyi időben értendők.
- Ha a kliens támogatja, használd a strukturált eredményt. Ellenőrizd az MCP hibajelzőjét és a hiba szövegét. Sikertelen írásnál az adott hívás visszagördül. Sikeres írásnál a módosítás a futási másolatban a szerver újraindítása után is megmarad. Minden hívás külön tranzakció, ezért egy későbbi hiba nem vonja vissza a korábbi írásokat.

## Olvasóeszközök

A táblázatban szereplő argumentumokon kívül minden kereső fogad `oldal` mezőt. A típusokat, az opcionális mezőket és az enumértékeket az élő séma adja meg.

| Eszköz | Argumentumok | Szerep |
| --- | --- | --- |
| `irodai_kornyezet` | — | Fordulónap, időzóna, pénznem, adatkészlet neve és írási mód. |
| `partner_kereses` | `szoveg`, `tipus`, `partner_id`, `telepules` | Cég keresése név, kód, e-mail, típus, azonosító vagy település szerint. |
| `kapcsolattarto_kereses` | `szoveg`, `partner_id`, `elsodleges` | Partnerkapcsolattartók, az elsődleges jelölésre is szűrhető. |
| `munkatars_kereses` | `szoveg`, `munkatars_id`, `vezeto_id` | Munkatársak és vezetői kapcsolataik. |
| `termek_kereses` | `szoveg`, `kategoria`, `beszallito_id`, `kifutott`, `keszlet_legfeljebb` | Termékek cikkszám, név, kategória, beszállító vagy készlet alapján. |
| `szerzodes_kereses` | `szoveg`, `vevo_id`, `felelos_id`, `lejarat`, `ervenyes_ekkor` | Keretszerződések, feltételek és szerződésszöveg. |
| `ajanlat_kereses` | `szoveg`, `vevo_id`, `felelos_id`, `allapot`, `kelte`, `lejarat`, `rendezes` | Ajánlatok állapot, keltezés vagy lejárat alapján. |
| `ajanlat_reszletek` | `ajanlat_id` | Ajánlatfej, kapcsolattartó és tételek. |
| `rendeles_kereses` | `szoveg`, `vevo_id`, `felelos_id`, `ajanlat_id`, `fuvarozo_id`, `allapot`, `kelte`, `kert_szallitas` | Rendelések ajánlat, fuvarozó és szállítási dátum szerint is. |
| `rendeles_reszletek` | `rendeles_id` | Rendelés, szállítási cím, fuvarozó, tételek és a kapcsolódó számla, ha van. |
| `szamla_kereses` | `szoveg`, `vevo_id`, `rendeles_id`, `fizetesi_allapot`, `lejart`, `kelte`, `hatarido`, `rendezes` | Számlaegyenleg, fizetési állapot és lejártság. |
| `szamla_reszletek` | `szamla_id` | Számlafej, egyenleg, tételek és rögzített befizetések. |
| `email_kereses` | `szoveg`, `ugy`, `vevo_id`, `levelezes_id`, `irany`, `felado`, `cimzett`, `idoszak`, `rendezes` | Keresés a tárgyban és a szövegben, a találat levélfejjel és ügyhivatkozással tér vissza. |
| `email_olvasas` | `email_id` | Teljes levélszöveg, fejléccel és ügyhivatkozással. |
| `feladat_kereses` | `szoveg`, `feladat_id`, `ugy`, `vevo_id`, `felelos_id`, `allapot`, `tipus`, `prioritas`, `hatarido` | Feladatok határidő szerint, a legkorábbi elöl. |

## Íróeszközök

Az íróeszközök csak akkor jelennek meg, ha a szerver külön adatbázison, `--irhato` kapcsolóval indul. Az IRODA a seedet nem engedi írható módban megnyitni. A kötelező és opcionális mezőket az élő séma adja meg. A módosítóeszközök a `valtozas` megadott, nem null értékű mezőit alkalmazzák. Kimenő levél címzettje az ügy vevője vagy a vevő kapcsolattartója lehet. A levelek és befizetések a szimulált irodát módosítják.

| Eszköz | Argumentumok | Szerep |
| --- | --- | --- |
| `ajanlat_modositas` | `ajanlat_id`, `valtozas` | Kiválasztott ajánlatmezők frissítése. A kapcsolattartó az ajánlat vevőjéhez tartozik. A lezárás napja a fordulónap. |
| `feladat_letrehozas` | `ugy`, `felelos_id`, `cim`, `leiras`, `hatarido`, `prioritas`, `allapot` | Követési feladat létrehozása. Az ügy adja a vevőt és a feladattípust. Kezdetben nyitott vagy folyamatban lévő lehet. |
| `feladat_modositas` | `feladat_id`, `valtozas` | Kiválasztott feladatmezők frissítése. Kész vagy törölt állapotnál a lezárás napja a fordulónap. |
| `email_kuldes` | `felado_id`, `cimzett`, `targy`, `uzenet`, `ugy`, `levelezes_id`, `valasz_erre_id` | Szimulált kimenő levél rögzítése. Az ügy és a levélfolyam közül pontosan egyet adj meg. A válasz ugyanarra a levélfolyamra hivatkozzon. |
| `befizetes_rogzitese` | `szamla_id`, `tranzakcioszam`, `ertek_nap`, `osszeg_ft`, `kozlemeny` | Befizetés rögzítése egyedi tranzakciószámmal. Az értéknap a számla kelte és a fordulónap közé esik, a határnapokat is beleértve. |

Többlépéses munkafolyamatnál olvasd be az iroda fordulónapját, keresd meg az előtte lejárt kiküldött ajánlatokat, majd a `feladat_kereses` hívással ellenőrizd az érintett ajánlat meglévő feladatait. Keresd ki a felelőst, és ellenőrizd az ügyazonosítót. Ha a feladat írást kér, hozz létre egy követési feladatot, és a visszaadott azonosítóval ellenőrizd a mentést. Az üzleti logika az [iroda.py](../iroda.py) fájlban, az eszközök regisztrációja a [mcp_server.py](../mcp_server.py) fájlban található.
