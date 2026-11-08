# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp==1.30.0"]
# ///

import argparse
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from iroda import Iroda, IrodaHiba, SEED


def make_server(iroda: Iroda) -> FastMCP:
    server = FastMCP(
        "IRODA",
        instructions=(
            "A Rézrigó Kft. szimulált vállalati irodája. A keresőeszközök megadott szűrői együtt érvényesek. "
            "A szöveges keresés kis- és nagybetűtől független részszövegre keres. "
            "Lapozáskor add át a kovetkezo_eltolas értékét az oldal.eltolas mezőben. "
            "Időfüggő műveletekhez használd az irodai_kornyezet fordulónapját. "
            "A pénzösszegek egész forintban, a kedvezmények bázispontban szerepelnek."
        ),
    )
    read_only = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
    for method, title in (
        (iroda.irodai_kornyezet, "Irodai környezet"),
        (iroda.partner_kereses, "Partnerkeresés"),
        (iroda.kapcsolattarto_kereses, "Kapcsolattartó-keresés"),
        (iroda.munkatars_kereses, "Munkatárskeresés"),
        (iroda.termek_kereses, "Termékkeresés"),
        (iroda.szerzodes_kereses, "Szerződéskeresés"),
        (iroda.ajanlat_kereses, "Ajánlatkeresés"),
        (iroda.ajanlat_reszletek, "Ajánlat részletei"),
        (iroda.rendeles_kereses, "Rendeléskeresés"),
        (iroda.rendeles_reszletek, "Rendelés részletei"),
        (iroda.szamla_kereses, "Számlakeresés"),
        (iroda.szamla_reszletek, "Számla részletei"),
        (iroda.email_kereses, "E-mail-keresés"),
        (iroda.email_olvasas, "E-mail olvasása"),
        (iroda.feladat_kereses, "Feladatkeresés"),
    ):
        server.add_tool(method, title=title, annotations=read_only, structured_output=True)

    if iroda.irhato:
        for method, title, destructive in (
            (iroda.ajanlat_modositas, "Ajánlat módosítása", True),
            (iroda.feladat_letrehozas, "Feladat létrehozása", False),
            (iroda.feladat_modositas, "Feladat módosítása", True),
            (iroda.email_kuldes, "Szimulált e-mail küldése", False),
            (iroda.befizetes_rogzitese, "Befizetés rögzítése", False),
        ):
            annotations = ToolAnnotations(readOnlyHint=False, destructiveHint=destructive, openWorldHint=False)
            server.add_tool(method, title=title, annotations=annotations, structured_output=True)
    return server


def main():
    parser = argparse.ArgumentParser(description="Az IRODA üzleti MCP-szervere (stdio).")
    parser.add_argument("--adatbazis", type=Path, default=SEED, help="Meglévő IRODA-adatbázisfájl útvonala.")
    parser.add_argument("--irhato", action="store_true", help="Engedélyezi az írást a futási példányon.")
    args = parser.parse_args()
    try:
        iroda = Iroda(args.adatbazis, args.irhato)
        iroda.irodai_kornyezet()
    except IrodaHiba as error:
        parser.error(str(error))
    make_server(iroda).run(transport="stdio")


if __name__ == "__main__":
    main()
