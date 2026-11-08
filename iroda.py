"""Az IRODA üzleti műveletei. Az MCP és a benchmarkharness közös felülete."""

import sqlite3
from contextlib import closing, contextmanager
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


SEED = Path(__file__).resolve().parent / "data" / "seed.db"
Adatok = dict[str, Any]
Azonosito = Annotated[int, Field(strict=True, gt=0, le=2**63 - 1)]
Darab = Annotated[int, Field(strict=True, ge=0, le=2**63 - 1)]
Forint = Annotated[int, Field(strict=True, gt=0, le=2**63 - 1, description="Összeg egész forintban.")]
Keresoszoveg = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
RovidSzoveg = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
HosszuSzoveg = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=12000)]
Nap = Annotated[date, Field(description="Naptári nap ÉÉÉÉ-HH-NN formátumban.")]
Ugytipus = Literal["ajánlat", "rendelés", "számla"]
Partnertipus = Literal["vevő", "beszállító", "fuvarozó", "saját cég"]
Ajanlatallapot = Literal["piszkozat", "kiküldve", "egyeztetés alatt", "elfogadva", "elutasítva", "lezárva"]
Rendelesallapot = Literal["feldolgozás alatt", "feladva", "teljesítve", "lemondva"]
Fizetesiallapot = Literal["nyitott", "részben fizetve", "kiegyenlítve", "túlfizetve"]
Feladatallapot = Literal["nyitott", "folyamatban", "kész", "törölve"]
Feladattipus = Literal["ajánlatkövetés", "szállítás", "számlakövetés"]
Prioritas = Literal["alacsony", "normál", "magas"]
Idorend = Literal["legújabb elöl", "legrégebbi elöl"]
UGY_TABLA = {"ajánlat": "ajanlat", "rendelés": "rendeles", "számla": "szamla"}
FELADAT_TIPUS = {"ajánlat": "ajánlatkövetés", "rendelés": "szállítás", "számla": "számlakövetés"}


class IrodaHiba(ValueError):
    """Érvénytelen üzleti művelet vagy elérhetetlen adat."""


class Bemenet(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Idoszak(Bemenet):
    ettol: Nap | None = Field(None, description="Kezdőnap, a megadott napot is beleértve.")
    eddig: Nap | None = Field(None, description="Zárónap, a megadott napot is beleértve.")

    @model_validator(mode="after")
    def ellenoriz(self):
        if self.ettol and self.eddig and self.ettol > self.eddig:
            raise ValueError("A kezdőnap a zárónap után van.")
        return self


class Lapozas(Bemenet):
    darab: Annotated[int, Field(strict=True, ge=1, le=100)] = Field(20, description="A kért találatok száma.")
    eltolas: Darab = Field(0, description="Az átugrandó találatok száma.")


class Ugy(Bemenet):
    tipus: Ugytipus = Field(description="A hivatkozott ügy típusa.")
    azonosito: Azonosito = Field(description="A hivatkozott ajánlat, rendelés vagy számla belső azonosítója.")


class AjanlatValtozas(Bemenet):
    targy: RovidSzoveg | None = None
    ervenyes_ig: Nap | None = None
    allapot: Ajanlatallapot | None = None
    felelos_id: Azonosito | None = Field(None, description="A kijelölt munkatárs azonosítója.")
    kapcsolattarto_id: Azonosito | None = Field(None, description="Az ajánlat vevőjéhez tartozó kapcsolattartó.")


class FeladatValtozas(Bemenet):
    cim: RovidSzoveg | None = None
    leiras: HosszuSzoveg | None = None
    hatarido: Nap | None = None
    allapot: Feladatallapot | None = None
    prioritas: Prioritas | None = None
    felelos_id: Azonosito | None = Field(None, description="A kijelölt munkatárs azonosítója.")


def _iso(value):
    return value.isoformat() if isinstance(value, date) else value


def _idoszak(oszlop: str, idoszak: Idoszak | None):
    return [(f"{oszlop} >= ?", idoszak.ettol), (f"{oszlop} <= ?", idoszak.eddig)] if idoszak else []


def _szoveg(keresoszoveg: str | None, *oszlopok: str):
    mezok = " || ' ' || ".join(f"coalesce({oszlop}, '')" for oszlop in oszlopok)
    return (f"instr(kisbetus({mezok}), kisbetus(?)) > 0", keresoszoveg)


def _ugy_szuro(ugy: Ugy | None, alias: str = ""):
    return [(f"{alias}{UGY_TABLA[ugy.tipus]}_id = ?", ugy.azonosito)] if ugy else []


def _egy(db, sql, parameterek, hibauzenet):
    sor = db.execute(sql, parameterek).fetchone()
    if sor is None:
        raise IrodaHiba(hibauzenet)
    return dict(sor)


def _sorok(db, sql, parameterek=()):
    return [dict(sor) for sor in db.execute(sql, parameterek)]


def _fordulonap(db):
    sor = _egy(db, "SELECT ertek FROM metaadat WHERE kulcs = 'fordulonap'", (), "Hiányzik a fordulónap.")
    return sor["ertek"]


def _frissit(db, tabla, azonosito, ertekek):
    if not ertekek:
        raise IrodaHiba("Adj meg legalább egy módosítandó mezőt.")
    mezok = ", ".join(f"{mezo} = ?" for mezo in ertekek)
    return dict(db.execute(
        f"UPDATE {tabla} SET {mezok} WHERE id = ? RETURNING *",
        (*map(_iso, ertekek.values()), azonosito),
    ).fetchone())


def _ugy_vevoje(db, ugy: Ugy):
    return _egy(db, f"SELECT vevo_id FROM {UGY_TABLA[ugy.tipus]} WHERE id = ?",
                (ugy.azonosito,), "A megadott ügy nem található.")["vevo_id"]


def _teteles_adatok(db, tabla, azonosito):
    # A nettó és az áfa külön kerekítése megegyezik a számlatételek szabályával.
    tetel = f"{tabla}tetel"
    return _sorok(db, f"""
        WITH netto AS (
            SELECT t.*, p.cikkszam, p.nev AS termeknev,
                   (t.mennyiseg * t.netto_egysegar_ft * (10000 - t.kedvezmeny_bp) + 5000) / 10000 AS netto_ft
            FROM {tetel} t JOIN termek p ON p.id = t.termek_id
            WHERE t.{tabla}_id = ?
        )
        SELECT *, (netto_ft * afa_szazalek + 50) / 100 AS afa_ft,
                  netto_ft + (netto_ft * afa_szazalek + 50) / 100 AS brutto_ft
        FROM netto ORDER BY sorszam
        """, (azonosito,))


class Iroda:
    def __init__(self, utvonal: Path = SEED, irhato: bool = False):
        self.utvonal = utvonal.resolve()
        self.irhato = irhato
        if not self.utvonal.is_file():
            raise IrodaHiba(f"Az adatbázisfájl nem található: {self.utvonal}")
        if irhato and SEED.exists() and self.utvonal.samefile(SEED):
            raise IrodaHiba("Íráshoz adj meg külön futási példányt.")

    @contextmanager
    def _kapcsolat(self, iras=False):
        if iras and not self.irhato:
            raise IrodaHiba("Ehhez a művelethez írható futási példány szükséges.")
        mode = "rw" if iras else "ro"
        try:
            with closing(sqlite3.connect(f"{self.utvonal.as_uri()}?mode={mode}", uri=True, timeout=2)) as db, db:
                db.row_factory = sqlite3.Row
                db.create_function("kisbetus", 1, str.casefold, deterministic=True)
                db.execute("PRAGMA foreign_keys = ON")
                db.execute("PRAGMA trusted_schema = OFF")
                db.execute("BEGIN IMMEDIATE" if iras else "BEGIN")
                yield db
        except sqlite3.IntegrityError as error:
            uzenet = {
                sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY: "Az egyik hivatkozott rekord hiányzik vagy másik ügyhöz tartozik.",
                sqlite3.SQLITE_CONSTRAINT_UNIQUE: "A megadott egyedi azonosító már szerepel az irodában.",
                sqlite3.SQLITE_CONSTRAINT_CHECK: "A megadott értékek nem felelnek meg az üzleti szabályoknak.",
            }.get(error.sqlite_errorcode, "A megadott adatok nem menthetők.")
            raise IrodaHiba(uzenet) from error
        except sqlite3.Error as error:
            raise IrodaHiba("Az iroda adatai jelenleg nem érhetők el.") from error

    def _kereses(self, select, szurok, sorrend, oldal):
        oldal = oldal or Lapozas()
        aktiv = [(feltetel, _iso(ertek)) for feltetel, ertek in szurok if ertek is not None]
        where = " WHERE " + " AND ".join(feltetel for feltetel, _ in aktiv) if aktiv else ""
        with self._kapcsolat() as db:
            sorok = _sorok(db, f"{select}{where} ORDER BY {sorrend} LIMIT ? OFFSET ?",
                           [*(ertek for _, ertek in aktiv), oldal.darab + 1, oldal.eltolas])
        return {"talalatok": sorok[:oldal.darab],
                "kovetkezo_eltolas": oldal.eltolas + oldal.darab if len(sorok) > oldal.darab else None}

    def irodai_kornyezet(self) -> Adatok:
        """Megadja az iroda fordulónapját, időzónáját, pénznemét és az írási módot."""
        with self._kapcsolat() as db:
            adatok = dict(db.execute(
                "SELECT kulcs, ertek FROM metaadat WHERE kulcs IN ('fordulonap', 'idozona', 'penznem', 'adatkeszlet')"
            ).fetchall())
        return {**adatok, "irhato": self.irhato}

    def partner_kereses(self, szoveg: Keresoszoveg | None = None, tipus: Partnertipus | None = None,
                        partner_id: Azonosito | None = None, telepules: Keresoszoveg | None = None,
                        oldal: Lapozas | None = None) -> Adatok:
        """Partnereket keres cégnév, partnerkód, e-mail-cím, típus, azonosító vagy település alapján."""
        return self._kereses(
            """SELECT p.id, p.kod, p.cegnev, p.tipus, p.szegmens, p.cim, p.email, p.fizetesi_hatarido_nap,
                      t.nev AS telepules, t.iranyitoszam
               FROM partner p JOIN telepules t ON p.telepules_id = t.id""",
            [_szoveg(szoveg, "p.cegnev", "p.kod", "p.email"), ("p.tipus = ?", tipus),
             ("p.id = ?", partner_id), _szoveg(telepules, "t.nev")], "p.cegnev, p.id", oldal)

    def kapcsolattarto_kereses(self, szoveg: Keresoszoveg | None = None, partner_id: Azonosito | None = None,
                               elsodleges: bool | None = None, oldal: Lapozas | None = None) -> Adatok:
        """Kapcsolattartókat keres név, beosztás, e-mail-cím vagy partner szerint. Szűrhet az elsődleges kapcsolattartóra."""
        return self._kereses(
            "SELECT k.*, p.cegnev FROM kapcsolattarto k JOIN partner p ON p.id = k.partner_id",
            [_szoveg(szoveg, "k.nev", "k.beosztas", "k.email"), ("k.partner_id = ?", partner_id),
             ("k.elsodleges = ?", elsodleges)], "k.nev, k.id", oldal)

    def munkatars_kereses(self, szoveg: Keresoszoveg | None = None, munkatars_id: Azonosito | None = None,
                          vezeto_id: Azonosito | None = None, oldal: Lapozas | None = None) -> Adatok:
        """Munkatársakat keres név, beosztás, e-mail-cím, azonosító vagy közvetlen vezető alapján."""
        return self._kereses("SELECT * FROM munkatars",
                             [_szoveg(szoveg, "nev", "beosztas", "email"), ("id = ?", munkatars_id),
                              ("vezeto_id = ?", vezeto_id)], "nev, id", oldal)

    def termek_kereses(self, szoveg: Keresoszoveg | None = None, kategoria: Keresoszoveg | None = None,
                       beszallito_id: Azonosito | None = None, kifutott: bool | None = None,
                       keszlet_legfeljebb: Darab | None = None, oldal: Lapozas | None = None) -> Adatok:
        """Termékeket keres név, cikkszám, kategórianév, beszállító, készlet vagy kifutott jelölés alapján."""
        return self._kereses(
            "SELECT t.*, k.nev AS kategoria FROM termek t JOIN termekkategoria k ON k.id = t.kategoria_id",
            [_szoveg(szoveg, "t.nev", "t.cikkszam"), _szoveg(kategoria, "k.nev"),
             ("t.beszallito_id = ?", beszallito_id), ("t.kifutott = ?", kifutott),
             ("t.keszlet <= ?", keszlet_legfeljebb)], "t.cikkszam, t.id", oldal)

    def szerzodes_kereses(self, szoveg: Keresoszoveg | None = None, vevo_id: Azonosito | None = None,
                         felelos_id: Azonosito | None = None, lejarat: Idoszak | None = None,
                         ervenyes_ekkor: Nap | None = None, oldal: Lapozas | None = None) -> Adatok:
        """Keretszerződéseket keres szerződésszám, tárgy, vevő, felelős, lejárati tartomány vagy érvényességi nap alapján. A feltételeket és a szöveget is visszaadja."""
        return self._kereses(
            "SELECT s.*, p.cegnev AS vevo, m.nev AS felelos FROM szerzodes s JOIN partner p ON p.id = s.vevo_id "
            "JOIN munkatars m ON m.id = s.felelos_id",
            [_szoveg(szoveg, "s.szerzodesszam", "s.targy"), ("s.vevo_id = ?", vevo_id),
             ("s.felelos_id = ?", felelos_id), *_idoszak("s.ervenyes_ig", lejarat),
             ("s.ervenyes_tol <= ?", ervenyes_ekkor), ("s.ervenyes_ig >= ?", ervenyes_ekkor)],
            "s.ervenyes_ig, s.szerzodesszam", oldal)

    def ajanlat_kereses(self, szoveg: Keresoszoveg | None = None, vevo_id: Azonosito | None = None,
                       felelos_id: Azonosito | None = None, allapot: Ajanlatallapot | None = None,
                       kelte: Idoszak | None = None, lejarat: Idoszak | None = None,
                       rendezes: Literal["legújabb elöl", "legrégebbi elöl", "lejárat szerint"] = "legújabb elöl",
                       oldal: Lapozas | None = None) -> Adatok:
        """Ajánlatokat keres ajánlatszám, tárgy, vevő, felelős, állapot, keltezés vagy lejárat szerint. Lejárati sorrendben a legkorábbi dátum áll elöl, egyezéskor az ajánlatszám dönt."""
        sorrend = {"legújabb elöl": "a.kelt DESC", "legrégebbi elöl": "a.kelt", "lejárat szerint": "a.ervenyes_ig"}
        return self._kereses(
            "SELECT a.*, p.cegnev AS vevo, m.nev AS felelos FROM ajanlat a JOIN partner p ON p.id = a.vevo_id "
            "JOIN munkatars m ON m.id = a.felelos_id",
            [_szoveg(szoveg, "a.ajanlatszam", "a.targy"), ("a.vevo_id = ?", vevo_id),
             ("a.felelos_id = ?", felelos_id), ("a.allapot = ?", allapot),
             *_idoszak("a.kelt", kelte), *_idoszak("a.ervenyes_ig", lejarat)],
            f"{sorrend[rendezes]}, a.ajanlatszam", oldal)

    def ajanlat_reszletek(self, ajanlat_id: Azonosito) -> Adatok:
        """Egy ajánlatot ad vissza a kapcsolattartóval, tételekkel és forintban számolt tételösszegekkel."""
        with self._kapcsolat() as db:
            ajanlat = _egy(db, """SELECT a.*, p.cegnev AS vevo, m.nev AS felelos, k.nev AS kapcsolattarto,
                                        k.email AS kapcsolattarto_email
                                 FROM ajanlat a JOIN partner p ON p.id = a.vevo_id
                                 JOIN munkatars m ON m.id = a.felelos_id
                                 JOIN kapcsolattarto k ON k.id = a.kapcsolattarto_id WHERE a.id = ?""",
                           (ajanlat_id,), "Az ajánlat nem található.")
            return {"ajanlat": ajanlat, "tetelek": _teteles_adatok(db, "ajanlat", ajanlat_id)}

    def rendeles_kereses(self, szoveg: Keresoszoveg | None = None, vevo_id: Azonosito | None = None,
                        felelos_id: Azonosito | None = None, ajanlat_id: Azonosito | None = None,
                        fuvarozo_id: Azonosito | None = None, allapot: Rendelesallapot | None = None,
                        kelte: Idoszak | None = None, kert_szallitas: Idoszak | None = None,
                        oldal: Lapozas | None = None) -> Adatok:
        """Rendeléseket keres rendelésszám, vevő, felelős, ajánlat, fuvarozó, állapot, keltezés vagy kért szállítás alapján."""
        return self._kereses(
            "SELECT r.*, p.cegnev AS vevo FROM rendeles r JOIN partner p ON p.id = r.vevo_id",
            [_szoveg(szoveg, "r.rendelesszam"), ("r.vevo_id = ?", vevo_id), ("r.felelos_id = ?", felelos_id),
             ("r.ajanlat_id = ?", ajanlat_id), ("r.fuvarozo_id = ?", fuvarozo_id), ("r.allapot = ?", allapot),
             *_idoszak("r.kelt", kelte), *_idoszak("r.kert_szallitas", kert_szallitas)],
            "r.kelt DESC, r.rendelesszam", oldal)

    def rendeles_reszletek(self, rendeles_id: Azonosito) -> Adatok:
        """Egy rendelést ad vissza a szállítási címmel, fuvarozóval, tételekkel és a kapcsolódó számla azonosítójával."""
        with self._kapcsolat() as db:
            rendeles = _egy(db, """SELECT r.*, t.nev AS szallitasi_telepules, t.iranyitoszam,
                                          p.cegnev AS fuvarozo, s.id AS szamla_id, s.szamlaszam
                                   FROM rendeles r JOIN telepules t ON t.id = r.szallitasi_telepules_id
                                   JOIN partner p ON p.id = r.fuvarozo_id
                                   LEFT JOIN szamla s ON s.rendeles_id = r.id WHERE r.id = ?""",
                            (rendeles_id,), "A rendelés nem található.")
            return {"rendeles": rendeles, "tetelek": _teteles_adatok(db, "rendeles", rendeles_id)}

    def szamla_kereses(self, szoveg: Keresoszoveg | None = None, vevo_id: Azonosito | None = None,
                      rendeles_id: Azonosito | None = None, fizetesi_allapot: Fizetesiallapot | None = None,
                      lejart: bool | None = None, kelte: Idoszak | None = None, hatarido: Idoszak | None = None,
                      rendezes: Literal["legújabb elöl", "határidő szerint", "legnagyobb hátralék elöl"] = "legújabb elöl",
                      oldal: Lapozas | None = None) -> Adatok:
        """Számlákat keres számlaszám, vevő, rendelés, keltezés, fizetési határidő, fizetési állapot vagy lejártság alapján. Lejárt az a számla, amelynek a fordulónap előtt lejárt a határideje és van hátraléka."""
        sorrend = {"legújabb elöl": "s.kelt DESC", "határidő szerint": "s.fizetesi_hatarido",
                   "legnagyobb hátralék elöl": "e.hatralevo_ft DESC"}
        return self._kereses(
            """SELECT e.*, s.rendeles_id, s.kelt, p.cegnev AS vevo FROM szamla_egyenleg e
               JOIN szamla s ON s.id = e.szamla_id JOIN partner p ON p.id = s.vevo_id""",
            [_szoveg(szoveg, "s.szamlaszam"), ("s.vevo_id = ?", vevo_id), ("s.rendeles_id = ?", rendeles_id),
             ("e.fizetesi_allapot = ?", fizetesi_allapot), ("e.lejart = ?", lejart),
             *_idoszak("s.kelt", kelte), *_idoszak("s.fizetesi_hatarido", hatarido)],
            f"{sorrend[rendezes]}, s.szamlaszam", oldal)

    def szamla_reszletek(self, szamla_id: Azonosito) -> Adatok:
        """Egy számla fejadatait, egyenlegét, tételeit és a hozzá könyvelt befizetéseket adja vissza."""
        with self._kapcsolat() as db:
            szamla = _egy(db, """SELECT s.*, p.cegnev AS vevo, r.felelos_id, r.rendelesszam
                                 FROM szamla s JOIN partner p ON p.id = s.vevo_id
                                 JOIN rendeles r ON r.id = s.rendeles_id WHERE s.id = ?""",
                          (szamla_id,), "A számla nem található.")
            egyenleg = db.execute("SELECT * FROM szamla_egyenleg WHERE szamla_id = ?", (szamla_id,)).fetchone()
            return {"szamla": szamla, "egyenleg": dict(egyenleg) if egyenleg else None,
                    "tetelek": _sorok(db, "SELECT * FROM szamlatetel WHERE szamla_id = ? ORDER BY sorszam", (szamla_id,)),
                    "befizetesek": _sorok(db, "SELECT * FROM befizetes WHERE szamla_id = ? ORDER BY ertek_nap, id",
                                          (szamla_id,))}

    def email_kereses(self, szoveg: Keresoszoveg | None = None, ugy: Ugy | None = None,
                     vevo_id: Azonosito | None = None, levelezes_id: Azonosito | None = None,
                     irany: Literal["bejövő", "kimenő"] | None = None, felado: Keresoszoveg | None = None,
                     cimzett: Keresoszoveg | None = None, idoszak: Idoszak | None = None,
                     rendezes: Idorend = "legújabb elöl", oldal: Lapozas | None = None) -> Adatok:
        """E-maileket keres a tárgy és üzenet szövegében, illetve ügy, vevő, levélfolyam, irány, feladó, címzett vagy időszak szerint. A találatok a levélfejet és a kapcsolódó ügyet tartalmazzák."""
        sorrend = "e.kuldes_ideje DESC, e.id DESC" if rendezes == "legújabb elöl" else "e.kuldes_ideje, e.id"
        return self._kereses(
            """SELECT e.id, e.levelezes_id, e.valasz_erre_id, e.kuldes_ideje, e.irany, e.felado, e.cimzett,
                      e.targy, l.vevo_id, l.ajanlat_id, l.rendeles_id, l.szamla_id
               FROM email e JOIN levelezes l ON l.id = e.levelezes_id""",
            [_szoveg(szoveg, "e.targy", "e.uzenet"), *_ugy_szuro(ugy, "l."), ("l.vevo_id = ?", vevo_id),
             ("e.levelezes_id = ?", levelezes_id), ("e.irany = ?", irany), _szoveg(felado, "e.felado"),
             _szoveg(cimzett, "e.cimzett"), *_idoszak("substr(e.kuldes_ideje, 1, 10)", idoszak)],
            sorrend, oldal)

    def email_olvasas(self, email_id: Azonosito) -> Adatok:
        """Egy e-mail teljes szövegét, fejlécét, levélfolyamát és a kapcsolódó ügy azonosítóját adja vissza."""
        with self._kapcsolat() as db:
            return _egy(db, """SELECT e.*, l.vevo_id, l.ajanlat_id, l.rendeles_id, l.szamla_id
                               FROM email e JOIN levelezes l ON l.id = e.levelezes_id WHERE e.id = ?""",
                        (email_id,), "Az e-mail nem található.")

    def feladat_kereses(self, szoveg: Keresoszoveg | None = None, feladat_id: Azonosito | None = None,
                       ugy: Ugy | None = None, vevo_id: Azonosito | None = None, felelos_id: Azonosito | None = None,
                       allapot: Feladatallapot | None = None, tipus: Feladattipus | None = None,
                       prioritas: Prioritas | None = None, hatarido: Idoszak | None = None,
                       oldal: Lapozas | None = None) -> Adatok:
        """Feladatokat keres cím, leírás, azonosító, ügy, vevő, felelős, állapot, típus, prioritás vagy határidő alapján. A legkorábbi határidő áll elöl."""
        return self._kereses(
            "SELECT f.*, m.nev AS felelos FROM feladat f JOIN munkatars m ON m.id = f.felelos_id",
            [_szoveg(szoveg, "f.cim", "f.leiras"), ("f.id = ?", feladat_id), *_ugy_szuro(ugy, "f."),
             ("f.vevo_id = ?", vevo_id), ("f.felelos_id = ?", felelos_id), ("f.allapot = ?", allapot),
             ("f.tipus = ?", tipus), ("f.prioritas = ?", prioritas), *_idoszak("f.hatarido", hatarido)],
            "f.hatarido, f.id", oldal)

    def ajanlat_modositas(self, ajanlat_id: Azonosito, valtozas: AjanlatValtozas) -> Adatok:
        """Egy ajánlat tárgyát, lejáratát, állapotát, felelősét vagy kapcsolattartóját módosítja. Csak a megadott, nem üres mezőket írja. Lezáráskor a fordulónapot rögzíti."""
        with self._kapcsolat(iras=True) as db:
            ajanlat = _egy(db, "SELECT * FROM ajanlat WHERE id = ?", (ajanlat_id,), "Az ajánlat nem található.")
            uj = valtozas.model_dump(exclude_none=True)
            if valtozas.ervenyes_ig and valtozas.ervenyes_ig.isoformat() < ajanlat["kelt"]:
                raise IrodaHiba("A lejárat nem lehet korábbi az ajánlat kelténél.")
            if valtozas.allapot is not None and valtozas.allapot != ajanlat["allapot"]:
                lezart = valtozas.allapot in {"elfogadva", "elutasítva", "lezárva"}
                uj["lezart_nap"] = _fordulonap(db) if lezart else None
            return _frissit(db, "ajanlat", ajanlat_id, uj)

    def feladat_letrehozas(self, ugy: Ugy, felelos_id: Azonosito, cim: RovidSzoveg, leiras: HosszuSzoveg,
                          hatarido: Nap, prioritas: Prioritas = "normál",
                          allapot: Literal["nyitott", "folyamatban"] = "nyitott") -> Adatok:
        """Új követési feladatot hoz létre egy ajánlathoz, rendeléshez vagy számlához. A vevőt és a típust az ügyből veszi, a létrehozás napja a fordulónap."""
        with self._kapcsolat(iras=True) as db:
            vevo = _ugy_vevoje(db, ugy)
            fordulonap = _fordulonap(db)
            if hatarido.isoformat() < fordulonap:
                raise IrodaHiba("A határidő nem lehet korábbi a létrehozás napjánál.")
            return dict(db.execute(
                f"""INSERT INTO feladat (vevo_id, felelos_id, {UGY_TABLA[ugy.tipus]}_id, cim, leiras,
                                         tipus, prioritas, allapot, letrehozva, hatarido)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING *""",
                (vevo, felelos_id, ugy.azonosito, cim, leiras, FELADAT_TIPUS[ugy.tipus], prioritas, allapot,
                 fordulonap, hatarido.isoformat()),
            ).fetchone())

    def feladat_modositas(self, feladat_id: Azonosito, valtozas: FeladatValtozas) -> Adatok:
        """Egy feladat címét, leírását, határidejét, állapotát, prioritását vagy felelősét módosítja. Készre vagy töröltre állításkor a fordulónapot rögzíti a lezárás napjaként."""
        with self._kapcsolat(iras=True) as db:
            feladat = _egy(db, "SELECT * FROM feladat WHERE id = ?", (feladat_id,), "A feladat nem található.")
            uj = valtozas.model_dump(exclude_none=True)
            if valtozas.hatarido and valtozas.hatarido.isoformat() < feladat["letrehozva"]:
                raise IrodaHiba("A határidő nem lehet korábbi a létrehozás napjánál.")
            if valtozas.allapot is not None and valtozas.allapot != feladat["allapot"]:
                uj["lezarva"] = _fordulonap(db) if valtozas.allapot in {"kész", "törölve"} else None
            return _frissit(db, "feladat", feladat_id, uj)

    def email_kuldes(self, felado_id: Azonosito, cimzett: Keresoszoveg, targy: RovidSzoveg, uzenet: HosszuSzoveg,
                     ugy: Ugy | None = None, levelezes_id: Azonosito | None = None,
                     valasz_erre_id: Azonosito | None = None) -> Adatok:
        """Szimulált kimenő e-mailt rögzít. A feladó munkatárs, a címzett az ügy vevőjének vagy kapcsolattartójának e-mail-címe. Meglévő levélfolyamhoz add meg a levelezes_id értékét, új levélfolyamhoz az ügyet. Válasz csak ugyanazon levélfolyam üzenetére rögzíthető."""
        if (ugy is None) == (levelezes_id is None):
            raise IrodaHiba("Adj meg egy ügyet új levélfolyamhoz vagy egy meglévő levélfolyam-azonosítót.")
        if valasz_erre_id is not None and levelezes_id is None:
            raise IrodaHiba("Válasz rögzítéséhez add meg a meglévő levélfolyamot is.")
        with self._kapcsolat(iras=True) as db:
            felado = _egy(db, "SELECT email FROM munkatars WHERE id = ?", (felado_id,),
                          "A feladó munkatárs nem található.")["email"]
            if ugy is None:
                vevo = _egy(db, "SELECT vevo_id FROM levelezes WHERE id = ?", (levelezes_id,),
                            "A levélfolyam nem található.")["vevo_id"]
            else:
                vevo = _ugy_vevoje(db, ugy)
                levelezes_id = db.execute(
                    f"INSERT INTO levelezes (vevo_id, {UGY_TABLA[ugy.tipus]}_id, targy) VALUES (?, ?, ?)",
                    (vevo, ugy.azonosito, targy),
                ).lastrowid
            cimzett = _egy(db, """SELECT email FROM (
                                      SELECT email FROM partner WHERE id = ?
                                      UNION ALL SELECT email FROM kapcsolattarto WHERE partner_id = ?
                                  ) WHERE kisbetus(email) = kisbetus(?)""",
                           (vevo, vevo, cimzett), "A címzett címe nem szerepel az ügy vevőjénél.")["email"]
            if valasz_erre_id is not None:
                _egy(db, "SELECT id FROM email WHERE id = ? AND levelezes_id = ?", (valasz_erre_id, levelezes_id),
                     "A válasz előzménye nem található ebben a levélfolyamban.")
            kuldes = datetime.combine(date.fromisoformat(_fordulonap(db)), time())
            utolso = db.execute("SELECT max(kuldes_ideje) FROM email WHERE levelezes_id = ?", (levelezes_id,)).fetchone()[0]
            if utolso:
                kuldes = max(kuldes, datetime.fromisoformat(utolso) + timedelta(seconds=1))
            return dict(db.execute(
                """INSERT INTO email (levelezes_id, valasz_erre_id, kuldes_ideje, irany, felado, cimzett, targy, uzenet)
                   VALUES (?, ?, ?, 'kimenő', ?, ?, ?, ?) RETURNING *""",
                (levelezes_id, valasz_erre_id, kuldes.isoformat(), felado, cimzett, targy, uzenet),
            ).fetchone())

    def befizetes_rogzitese(self, szamla_id: Azonosito, tranzakcioszam: RovidSzoveg, ertek_nap: Nap,
                            osszeg_ft: Forint, kozlemeny: RovidSzoveg) -> Adatok:
        """Egy ténylegesen jóváírt befizetést könyvel a megadott számlára. A tranzakciószám egyedi. A visszaadott egyenleg a befizetés utáni állapotot mutatja."""
        with self._kapcsolat(iras=True) as db:
            szamla = _egy(db, "SELECT kelt FROM szamla WHERE id = ?", (szamla_id,), "A számla nem található.")
            if not szamla["kelt"] <= ertek_nap.isoformat() <= _fordulonap(db):
                raise IrodaHiba("Az értéknapnak a számla kelte és a fordulónap közé kell esnie.")
            befizetes = dict(db.execute(
                """INSERT INTO befizetes (szamla_id, tranzakcioszam, ertek_nap, osszeg_ft, kozlemeny)
                   VALUES (?, ?, ?, ?, ?) RETURNING *""",
                (szamla_id, tranzakcioszam, ertek_nap.isoformat(), osszeg_ft, kozlemeny),
            ).fetchone())
            egyenleg = db.execute("SELECT * FROM szamla_egyenleg WHERE szamla_id = ?", (szamla_id,)).fetchone()
            return {"befizetes": befizetes, "egyenleg": dict(egyenleg) if egyenleg else None}
