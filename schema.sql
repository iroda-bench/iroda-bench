PRAGMA foreign_keys = ON;
PRAGMA user_version = 1;

CREATE TABLE metaadat (
    kulcs TEXT PRIMARY KEY NOT NULL,
    ertek TEXT NOT NULL
) STRICT;

CREATE TABLE adatforras (
    id TEXT PRIMARY KEY NOT NULL,
    megnevezes TEXT NOT NULL,
    url TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    szerep TEXT NOT NULL
) STRICT;

CREATE TABLE licenc_ertesites (
    id TEXT PRIMARY KEY NOT NULL,
    licenc TEXT NOT NULL,
    hatokor TEXT NOT NULL,
    szoveg TEXT NOT NULL
) STRICT;

CREATE TABLE telepules (
    id INTEGER PRIMARY KEY,
    nev TEXT UNIQUE NOT NULL,
    iranyitoszam TEXT NOT NULL CHECK (iranyitoszam GLOB '[1-9][0-9][0-9][0-9]'),
    terulet TEXT NOT NULL
) STRICT;

CREATE TABLE partner (
    id INTEGER PRIMARY KEY,
    kod TEXT UNIQUE NOT NULL,
    cegnev TEXT UNIQUE NOT NULL,
    tipus TEXT NOT NULL CHECK (tipus IN ('vevő','beszállító','fuvarozó','saját cég')),
    szegmens TEXT NOT NULL,
    telepules_id INTEGER NOT NULL REFERENCES telepules,
    cim TEXT NOT NULL,
    orszagkod TEXT NOT NULL DEFAULT 'HU' CHECK (orszagkod = 'HU'),
    minta_adoszam TEXT UNIQUE,
    fizetesi_hatarido_nap INTEGER NOT NULL CHECK (fizetesi_hatarido_nap >= 0),
    email TEXT UNIQUE NOT NULL CHECK (email LIKE '%@%.invalid')
) STRICT;

CREATE TABLE kapcsolattarto (
    id INTEGER PRIMARY KEY,
    partner_id INTEGER NOT NULL REFERENCES partner,
    nev TEXT NOT NULL,
    beosztas TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL CHECK (email LIKE '%@%.invalid'),
    elsodleges INTEGER NOT NULL CHECK (elsodleges IN (0,1)),
    UNIQUE (id, partner_id)
) STRICT;
CREATE UNIQUE INDEX kapcsolattarto_elsodleges ON kapcsolattarto(partner_id) WHERE elsodleges = 1;

CREATE TABLE munkatars (
    id INTEGER PRIMARY KEY,
    nev TEXT NOT NULL,
    beosztas TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL CHECK (email LIKE '%@%.invalid'),
    vezeto_id INTEGER REFERENCES munkatars DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE termekkategoria (
    id INTEGER PRIMARY KEY,
    nev TEXT UNIQUE NOT NULL
) STRICT;

CREATE TABLE termek (
    id INTEGER PRIMARY KEY,
    cikkszam TEXT UNIQUE NOT NULL,
    nev TEXT UNIQUE NOT NULL,
    kategoria_id INTEGER NOT NULL REFERENCES termekkategoria,
    beszallito_id INTEGER NOT NULL REFERENCES partner,
    kiszereles TEXT NOT NULL,
    netto_listaar_ft INTEGER NOT NULL CHECK (netto_listaar_ft > 0),
    afa_szazalek INTEGER NOT NULL CHECK (afa_szazalek IN (5,18,27)),
    keszlet INTEGER NOT NULL CHECK (keszlet >= 0),
    beszallitotol_rendelve INTEGER NOT NULL CHECK (beszallitotol_rendelve >= 0),
    ujrarendelesi_szint INTEGER NOT NULL CHECK (ujrarendelesi_szint >= 0),
    kifutott INTEGER NOT NULL CHECK (kifutott IN (0,1))
) STRICT;

CREATE TABLE szerzodes (
    id INTEGER PRIMARY KEY,
    szerzodesszam TEXT UNIQUE NOT NULL,
    vevo_id INTEGER NOT NULL REFERENCES partner,
    felelos_id INTEGER NOT NULL REFERENCES munkatars,
    targy TEXT NOT NULL,
    alairas_napja TEXT NOT NULL,
    ervenyes_tol TEXT NOT NULL CHECK (ervenyes_tol >= alairas_napja),
    ervenyes_ig TEXT NOT NULL CHECK (ervenyes_ig >= ervenyes_tol),
    fizetesi_hatarido_nap INTEGER NOT NULL CHECK (fizetesi_hatarido_nap >= 0),
    szoveg TEXT NOT NULL,
    UNIQUE (id, vevo_id)
) STRICT;

CREATE TABLE ajanlat (
    id INTEGER PRIMARY KEY,
    ajanlatszam TEXT UNIQUE NOT NULL,
    vevo_id INTEGER NOT NULL REFERENCES partner,
    kapcsolattarto_id INTEGER NOT NULL,
    felelos_id INTEGER NOT NULL REFERENCES munkatars,
    szerzodes_id INTEGER,
    targy TEXT NOT NULL,
    kelt TEXT NOT NULL,
    ervenyes_ig TEXT NOT NULL CHECK (ervenyes_ig >= kelt),
    allapot TEXT NOT NULL CHECK (allapot IN ('piszkozat','kiküldve','egyeztetés alatt','elfogadva','elutasítva','lezárva')),
    lezart_nap TEXT CHECK (lezart_nap >= kelt),
    CHECK ((lezart_nap IS NOT NULL) = (allapot IN ('elfogadva','elutasítva','lezárva'))),
    FOREIGN KEY (kapcsolattarto_id, vevo_id) REFERENCES kapcsolattarto(id, partner_id),
    FOREIGN KEY (szerzodes_id, vevo_id) REFERENCES szerzodes(id, vevo_id),
    UNIQUE (id, vevo_id)
) STRICT;

CREATE TABLE ajanlattetel (
    ajanlat_id INTEGER NOT NULL REFERENCES ajanlat,
    sorszam INTEGER NOT NULL CHECK (sorszam > 0),
    termek_id INTEGER NOT NULL REFERENCES termek,
    mennyiseg INTEGER NOT NULL CHECK (mennyiseg > 0),
    netto_egysegar_ft INTEGER NOT NULL CHECK (netto_egysegar_ft >= 0),
    kedvezmeny_bp INTEGER NOT NULL CHECK (kedvezmeny_bp BETWEEN 0 AND 10000),
    afa_szazalek INTEGER NOT NULL CHECK (afa_szazalek IN (5,18,27)),
    PRIMARY KEY (ajanlat_id, sorszam)
) STRICT;

CREATE TABLE rendeles (
    id INTEGER PRIMARY KEY,
    rendelesszam TEXT UNIQUE NOT NULL,
    vevo_id INTEGER NOT NULL REFERENCES partner,
    felelos_id INTEGER NOT NULL REFERENCES munkatars,
    ajanlat_id INTEGER UNIQUE,
    szerzodes_id INTEGER,
    fuvarozo_id INTEGER NOT NULL REFERENCES partner,
    kelt TEXT NOT NULL,
    kert_szallitas TEXT NOT NULL CHECK (kert_szallitas >= kelt),
    feladas_napja TEXT CHECK (feladas_napja >= kelt),
    allapot TEXT NOT NULL CHECK (allapot IN ('feldolgozás alatt','feladva','teljesítve','lemondva')),
    szallitasi_dij_ft INTEGER NOT NULL CHECK (szallitasi_dij_ft >= 0),
    szallitasi_telepules_id INTEGER NOT NULL REFERENCES telepules,
    szallitasi_cim TEXT NOT NULL,
    teljesites_napja TEXT CHECK (teljesites_napja >= feladas_napja),
    CHECK ((feladas_napja IS NOT NULL) = (allapot IN ('feladva','teljesítve'))),
    CHECK ((teljesites_napja IS NOT NULL) = (allapot = 'teljesítve')),
    FOREIGN KEY (ajanlat_id, vevo_id) REFERENCES ajanlat(id, vevo_id),
    FOREIGN KEY (szerzodes_id, vevo_id) REFERENCES szerzodes(id, vevo_id),
    UNIQUE (id, vevo_id)
) STRICT;

CREATE TABLE rendelestetel (
    rendeles_id INTEGER NOT NULL REFERENCES rendeles,
    sorszam INTEGER NOT NULL CHECK (sorszam > 0),
    termek_id INTEGER NOT NULL REFERENCES termek,
    mennyiseg INTEGER NOT NULL CHECK (mennyiseg > 0),
    netto_egysegar_ft INTEGER NOT NULL CHECK (netto_egysegar_ft >= 0),
    kedvezmeny_bp INTEGER NOT NULL CHECK (kedvezmeny_bp BETWEEN 0 AND 10000),
    afa_szazalek INTEGER NOT NULL CHECK (afa_szazalek IN (5,18,27)),
    PRIMARY KEY (rendeles_id, sorszam)
) STRICT;

CREATE TABLE szamla (
    id INTEGER PRIMARY KEY,
    szamlaszam TEXT UNIQUE NOT NULL,
    rendeles_id INTEGER UNIQUE NOT NULL,
    vevo_id INTEGER NOT NULL REFERENCES partner,
    kibocsato_id INTEGER NOT NULL REFERENCES partner,
    kelt TEXT NOT NULL,
    teljesites_napja TEXT NOT NULL CHECK (teljesites_napja <= kelt),
    fizetesi_hatarido TEXT NOT NULL CHECK (fizetesi_hatarido >= kelt),
    fizetesi_mod TEXT NOT NULL DEFAULT 'átutalás' CHECK (fizetesi_mod = 'átutalás'),
    penznem TEXT NOT NULL DEFAULT 'HUF' CHECK (penznem = 'HUF'),
    FOREIGN KEY (rendeles_id, vevo_id) REFERENCES rendeles(id, vevo_id),
    UNIQUE (id, vevo_id)
) STRICT;

CREATE TABLE szamlatetel (
    szamla_id INTEGER NOT NULL REFERENCES szamla,
    sorszam INTEGER NOT NULL CHECK (sorszam > 0),
    termek_id INTEGER REFERENCES termek,
    megnevezes TEXT NOT NULL,
    mertekegyseg TEXT NOT NULL CHECK (mertekegyseg IN ('csomag','db','alkalom')),
    mennyiseg INTEGER NOT NULL CHECK (mennyiseg > 0),
    netto_egysegar_ft INTEGER NOT NULL CHECK (netto_egysegar_ft >= 0),
    kedvezmeny_bp INTEGER NOT NULL CHECK (kedvezmeny_bp BETWEEN 0 AND 10000),
    afa_szazalek INTEGER NOT NULL CHECK (afa_szazalek IN (5,18,27)),
    netto_ft INTEGER GENERATED ALWAYS AS
        ((mennyiseg * netto_egysegar_ft * (10000 - kedvezmeny_bp) + 5000) / 10000) STORED,
    afa_ft INTEGER GENERATED ALWAYS AS ((netto_ft * afa_szazalek + 50) / 100) STORED,
    brutto_ft INTEGER GENERATED ALWAYS AS (netto_ft + afa_ft) STORED,
    PRIMARY KEY (szamla_id, sorszam)
) STRICT;

CREATE TABLE befizetes (
    id INTEGER PRIMARY KEY,
    szamla_id INTEGER NOT NULL REFERENCES szamla,
    tranzakcioszam TEXT UNIQUE NOT NULL,
    ertek_nap TEXT NOT NULL,
    osszeg_ft INTEGER NOT NULL CHECK (osszeg_ft > 0),
    kozlemeny TEXT NOT NULL
) STRICT;

CREATE TABLE levelezes (
    id INTEGER PRIMARY KEY,
    vevo_id INTEGER NOT NULL REFERENCES partner,
    ajanlat_id INTEGER,
    rendeles_id INTEGER,
    szamla_id INTEGER,
    targy TEXT NOT NULL,
    CHECK ((ajanlat_id IS NOT NULL) + (rendeles_id IS NOT NULL) + (szamla_id IS NOT NULL) = 1),
    FOREIGN KEY (ajanlat_id, vevo_id) REFERENCES ajanlat(id, vevo_id),
    FOREIGN KEY (rendeles_id, vevo_id) REFERENCES rendeles(id, vevo_id),
    FOREIGN KEY (szamla_id, vevo_id) REFERENCES szamla(id, vevo_id)
) STRICT;

CREATE TABLE email (
    id INTEGER PRIMARY KEY,
    levelezes_id INTEGER NOT NULL REFERENCES levelezes,
    valasz_erre_id INTEGER,
    kuldes_ideje TEXT NOT NULL,
    irany TEXT NOT NULL CHECK (irany IN ('bejövő','kimenő')),
    felado TEXT NOT NULL CHECK (felado LIKE '%@%.invalid'),
    cimzett TEXT NOT NULL CHECK (cimzett LIKE '%@%.invalid'),
    targy TEXT NOT NULL,
    uzenet TEXT NOT NULL,
    UNIQUE (id, levelezes_id),
    FOREIGN KEY (valasz_erre_id, levelezes_id) REFERENCES email(id, levelezes_id)
) STRICT;

CREATE TABLE feladat (
    id INTEGER PRIMARY KEY,
    vevo_id INTEGER NOT NULL REFERENCES partner,
    felelos_id INTEGER NOT NULL REFERENCES munkatars,
    ajanlat_id INTEGER,
    rendeles_id INTEGER,
    szamla_id INTEGER,
    cim TEXT NOT NULL,
    leiras TEXT NOT NULL,
    tipus TEXT NOT NULL CHECK (tipus IN ('ajánlatkövetés','szállítás','számlakövetés')),
    prioritas TEXT NOT NULL CHECK (prioritas IN ('alacsony','normál','magas')),
    allapot TEXT NOT NULL CHECK (allapot IN ('nyitott','folyamatban','kész','törölve')),
    letrehozva TEXT NOT NULL,
    hatarido TEXT NOT NULL CHECK (hatarido >= letrehozva),
    lezarva TEXT CHECK (lezarva >= letrehozva),
    CHECK ((lezarva IS NOT NULL) = (allapot IN ('kész','törölve'))),
    CHECK ((ajanlat_id IS NOT NULL AND tipus = 'ajánlatkövetés')
        OR (rendeles_id IS NOT NULL AND tipus = 'szállítás')
        OR (szamla_id IS NOT NULL AND tipus = 'számlakövetés')),
    CHECK ((ajanlat_id IS NOT NULL) + (rendeles_id IS NOT NULL) + (szamla_id IS NOT NULL) = 1),
    FOREIGN KEY (ajanlat_id, vevo_id) REFERENCES ajanlat(id, vevo_id),
    FOREIGN KEY (rendeles_id, vevo_id) REFERENCES rendeles(id, vevo_id),
    FOREIGN KEY (szamla_id, vevo_id) REFERENCES szamla(id, vevo_id)
) STRICT;

CREATE INDEX rendeles_vevo_kelt ON rendeles(vevo_id, kelt);
CREATE INDEX ajanlat_allapot_lejarat ON ajanlat(allapot, ervenyes_ig);
CREATE INDEX szamla_vevo_hatarido ON szamla(vevo_id, fizetesi_hatarido);
CREATE INDEX befizetes_szamla ON befizetes(szamla_id, ertek_nap);
CREATE INDEX email_levelezes ON email(levelezes_id, kuldes_ideje);
CREATE INDEX feladat_felelos_hatarido ON feladat(felelos_id, allapot, hatarido);

CREATE VIEW szamla_egyenleg AS
WITH tetel AS (
    SELECT szamla_id, SUM(netto_ft) netto_ft, SUM(afa_ft) afa_ft, SUM(brutto_ft) brutto_ft
    FROM szamlatetel GROUP BY szamla_id
), fizetes AS (
    SELECT szamla_id, SUM(osszeg_ft) befizetett_ft FROM befizetes GROUP BY szamla_id
)
SELECT s.id AS szamla_id, s.szamlaszam, s.vevo_id, s.fizetesi_hatarido,
       t.netto_ft, t.afa_ft, t.brutto_ft,
       coalesce(f.befizetett_ft, 0) AS befizetett_ft,
       t.brutto_ft - coalesce(f.befizetett_ft, 0) AS hatralevo_ft,
       CASE WHEN f.befizetett_ft = t.brutto_ft THEN 'kiegyenlítve'
            WHEN f.befizetett_ft > t.brutto_ft THEN 'túlfizetve'
            WHEN f.befizetett_ft > 0 THEN 'részben fizetve'
            ELSE 'nyitott' END AS fizetesi_allapot,
       (t.brutto_ft > coalesce(f.befizetett_ft, 0) AND
        s.fizetesi_hatarido < (SELECT ertek FROM metaadat WHERE kulcs = 'fordulonap')) AS lejart
FROM szamla s
JOIN tetel t ON s.id = t.szamla_id
LEFT JOIN fizetes f ON s.id = f.szamla_id;
