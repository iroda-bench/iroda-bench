#!/usr/bin/env python3
"""Az IRODA magyar vállalati mintájának determinisztikus előállítása."""

import argparse
from collections import defaultdict
from contextlib import closing
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
REVISION = "4f56e7f5906dfd23b25244c5bfe8fb5da6402efd"
UPSTREAM = f"https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/{REVISION}"
INPUTS = {
    "create.sql": "5854b536dea3fe8c586223bf7b47a793727dd44c34fc32537a68a97fec8e2f4b",
    "update.sql": "59df0f3c88b1878946b712cc6e8a7f37c971c802ff2ed611c59feb72acb39ea6",
}
MS_LICENSE = "https://raw.githubusercontent.com/microsoft/sql-server-samples/4693087abebd7e835f9ee46d005dcdaa03092a40/license.txt"
LICENSES = (
    ("northwind", "LICENSE-Northwind-SQLite3.txt", f"{UPSTREAM}/LICENSE",
     "A Northwind SQLite3 származtatott adatainak elsődleges értesítése.",
     "c28e204be6418b87ae1c83127096aad9c9e1a218c365f8f4d630e84d8ba96c47"),
    ("microsoft", "LICENSE-Microsoft-SQL-Samples.txt", MS_LICENSE,
     "A Microsoft külön kiadott SQL Server Northwind mintájának kiegészítő eredetjelölése.",
     "201f3705979e932c92cd3c6ddbddf4dc3c71dcc5a82089a1e4018227cfe1cf09"),
)
SNAPSHOT = date(2026, 11, 8)
DATE_SHIFT = date(2026, 11, 6) - date(2018, 5, 6)
COMPANY_ID = 900
TOWNS = [
    ("Budapest", "1117", "Budapest"), ("Győr", "9021", "Győr-Moson-Sopron"),
    ("Debrecen", "4025", "Hajdú-Bihar"), ("Pécs", "7621", "Baranya"),
    ("Szeged", "6720", "Csongrád-Csanád"), ("Kecskemét", "6000", "Bács-Kiskun"),
    ("Veszprém", "8200", "Veszprém"), ("Miskolc", "3525", "Borsod-Abaúj-Zemplén"),
    ("Székesfehérvár", "8000", "Fejér"), ("Szolnok", "5000", "Jász-Nagykun-Szolnok"),
    ("Eger", "3300", "Heves"), ("Nyíregyháza", "4400", "Szabolcs-Szatmár-Bereg"),
    ("Sopron", "9400", "Győr-Moson-Sopron"), ("Szombathely", "9700", "Vas"),
    ("Zalaegerszeg", "8900", "Zala"), ("Kaposvár", "7400", "Somogy"),
    ("Szekszárd", "7100", "Tolna"), ("Békéscsaba", "5600", "Békés"),
    ("Tatabánya", "2800", "Komárom-Esztergom"), ("Salgótarján", "3100", "Nógrád"),
    ("Budaörs", "2040", "Pest"),
]
STREETS = ["Barkaív utca", "Aranylomb köz", "Harmatkapu út", "Szélhíd utca",
           "Gyöngyliget tér", "Rézlevél sor", "Pirkadókert utca"]
STEMS = ["Dérliget", "Rézpart", "Holdmalom", "Vadszilva", "Szélzug", "Tisztaág",
         "Égerkert", "Nádorom", "Fényrév", "Boglárhíd", "Dombkoszorú", "Harmatív",
         "Mécsvölgy", "Őszberek", "Csermelykapu", "Hajnalszél", "Borókásdomb"]
CUSTOMER_SEGMENTS = [
    ("Vendéglátó", "Kft.", "vendéglátás", "üzletvezető"),
    ("Élelmiszerbolt", "Bt.", "kiskereskedelem", "boltvezető"),
    ("Szálláshely", "Kft.", "szálláshely", "beszerzési ügyintéző"),
    ("Rendezvényház", "Kft.", "rendezvény", "rendezvényszervező"),
    ("Delikát", "Kft.", "kiskereskedelem", "beszerző"),
    ("Konyhaüzem", "Kft.", "közétkeztetés", "élelmezésvezető"),
]
SUPPLIER_SEGMENTS = [
    ("Élelmiszer-kereskedő", "Kft.", "élelmiszer-kereskedelem", "értékesítő"),
    ("Élelmiszerimport", "Kft.", "élelmiszer-import", "nagykereskedelmi ügyintéző"),
]
SURNAMES = ["Tóth", "Kovács", "Varga", "Nagy", "Kiss", "Molnár", "Farkas", "Balogh",
            "Papp", "Németh", "Takács", "Lakatos", "Szalai", "Bíró", "Kocsis", "Sipos",
            "Bodnár", "Pintér", "Barta", "Kelemen", "Jakab", "Bálint", "Sárközi",
            "Vincze", "Rácz", "Orbán", "Kerekes", "Bognár", "Szücs"]
GIVEN_NAMES = ["Eszter", "Ádám", "Júlia", "András", "Dóra", "Bence", "Noémi", "Gergő",
               "Zsófia", "Márton", "Réka", "Balázs", "Anna", "Tamás", "Éva", "Péter",
               "Ildikó", "Gábor", "Nóra"]
STAFF = [
    ("Szőke Lilla", "értékesítési munkatárs"), ("Földes Ágnes", "kereskedelmi igazgató"),
    ("Váradi Miklós", "területi értékesítő"), ("Gulyás Orsolya", "ügyfélkapcsolati munkatárs"),
    ("Pálfi Zoltán", "értékesítési csoportvezető"), ("Fekete Klára", "kiemelt ügyfélfelelős"),
    ("Hegedűs Dávid", "területi értékesítő"), ("Szekeres Judit", "értékesítési munkatárs"),
    ("Mészáros Levente", "ügyfélkapcsolati munkatárs"),
]
CATEGORIES = [
    "Italok", "Ízesítők és szószok", "Édességek és sütemények", "Sajtok és tejtermékek",
    "Pékáru és tészta", "Húsok és húsételek", "Növényi élelmiszerek",
    "Halak és tengeri élelmiszerek",
]


def add_days(day, count):
    return day + timedelta(days=count)


def rounded(value):
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def huf(source_amount):
    return rounded(Decimal(str(source_amount)) * 400)


def imported_date(value):
    return date.fromisoformat(value[:10]) + DATE_SHIFT


def code(prefix, day, serial):
    return f"{prefix}-{day.year}-{serial:05d}"


def insert(db, table, *values):
    # A táblanév kizárólag a generátor kódjából érkezik.
    params = ", ".join("?" for _ in values)
    values = tuple(value.isoformat() if isinstance(value, date) else value for value in values)
    db.execute(f"INSERT INTO {table} VALUES ({params})", values)


def load_source(db, source_dir):
    db.row_factory = sqlite3.Row
    for filename, digest in INPUTS.items():
        if source_dir:
            content = (source_dir / filename).read_bytes()
        else:
            with urlopen(f"{UPSTREAM}/src/{filename}", timeout=45) as response:
                content = response.read()
        if sha256(content).hexdigest() != digest:
            raise ValueError(f"A Northwind-forrás ellenőrzőösszege eltér: {filename}")
        db.executescript(content.decode("utf-8-sig"))


def record_provenance(db):
    for key, value in {
        "adatkeszlet": "IRODA – Rézrigó Élelmiszer-nagykereskedelmi Kft.",
        "verzio": "0.1.0",
        "fordulonap": SNAPSHOT.isoformat(),
        "idozona": "Europe/Budapest",
        "penznem": "HUF",
        "northwind_commit": REVISION,
    }.items():
        insert(db, "metaadat", key, value)
    for filename, digest in INPUTS.items():
        insert(db, "adatforras", filename, f"Northwind SQLite3 – {filename}",
               f"{UPSTREAM}/src/{filename}", digest, "Rögzített adatforrás")
    for source_id, filename, url, scope, digest in LICENSES:
        content = (ROOT / "sources" / filename).read_bytes()
        if sha256(content).hexdigest() != digest:
            raise ValueError(f"A licencfájl ellenőrzőösszege eltér: {filename}")
        insert(db, "adatforras", source_id, filename, url, digest, "Licenc és eredetjelölés")
        insert(db, "licenc_ertesites", source_id, "MIT", scope, content.decode("utf-8-sig"))
    insert(db, "licenc_ertesites", "iroda", "MIT", "Az IRODA saját hozzájárulásai.",
           (ROOT / "LICENSE").read_text(encoding="utf-8"))


def address(seed):
    town = 1 + (seed * 11) % len(TOWNS)
    street = STREETS[(seed // len(TOWNS)) % len(STREETS)]
    return town, f"{street} {1 + (seed * 13) % 97}."


def partner(db, partner_id, prefix, name, kind, segment, days):
    partner_code = f"{prefix}-{partner_id:03d}"
    town, street = address(partner_id)
    domain = f"{partner_code.lower()}.iroda.invalid"
    sample_tax = f"000{partner_id:05d}-0-00"
    insert(db, "partner", partner_id, partner_code, name, kind, segment, town, street,
           "HU", sample_tax, days, f"iroda@{domain}")
    return town, street, domain


def contact(db, partner_id, domain, role, primary):
    index = partner_id + (0 if primary else 253)
    name = f"{SURNAMES[index % len(SURNAMES)]} {GIVEN_NAMES[index % len(GIVEN_NAMES)]}"
    local_part = "kapcsolat" if primary else "penzugy"
    contact_id = partner_id * 10 + (1 if primary else 2)
    email = f"{local_part}@{domain}"
    insert(db, "kapcsolattarto", contact_id, partner_id, name, role, email, int(primary))
    return contact_id, email, name.split()[-1]


def masters(source, db):
    for town_id, town in enumerate(TOWNS, 1):
        insert(db, "telepules", town_id, *town)
    partner(db, COMPANY_ID, "IRODA", "Rézrigó Élelmiszer-nagykereskedelmi Kft.",
            "saját cég", "élelmiszer-nagykereskedelem", 0)
    customers = {}
    for customer_id, row in enumerate(source.execute(
        "SELECT CustomerID FROM Customers ORDER BY CustomerID"
    ), 1):
        i = customer_id - 1
        label, form, segment, role = CUSTOMER_SEGMENTS[i // len(STEMS)]
        name = f"{STEMS[i % len(STEMS)]} {label} {form}"
        days = (8, 15, 15, 30, 30, 30, 45)[i % 7]
        town, street, domain = partner(db, customer_id, "VEV", name, "vevő", segment, days)
        main = contact(db, customer_id, domain, role, True)
        billing = contact(db, customer_id, domain, "pénzügyi ügyintéző", False) if i % 3 == 0 else main
        customers[row["CustomerID"]] = (customer_id, town, street, days, main, billing)

    for (supplier_id,) in source.execute("SELECT SupplierID FROM Suppliers ORDER BY SupplierID"):
        i = supplier_id - 1
        label, form, segment, role = SUPPLIER_SEGMENTS[i // len(STEMS)]
        _, _, domain = partner(db, 100 + supplier_id, "BES", f"{STEMS[i % len(STEMS)]} {label} {form}",
                               "beszállító", segment, 30)
        contact(db, 100 + supplier_id, domain, role, True)
    carrier_names = ("Barkaív Fuvar Kft.", "Harmatkapu Hűtött Logisztika Kft.", "Révpart Expressz Kft.")
    for (shipper_id,) in source.execute("SELECT ShipperID FROM Shippers ORDER BY ShipperID"):
        _, _, domain = partner(db, 200 + shipper_id, "FUV", carrier_names[shipper_id - 1],
                               "fuvarozó", "áruszállítás", 15)
        contact(db, 200 + shipper_id, domain, "fuvarszervező", True)

    staff = {}
    for employee_id, manager_id in source.execute(
        "SELECT EmployeeID, ReportsTo FROM Employees ORDER BY EmployeeID"
    ):
        name, role = STAFF[employee_id - 1]
        email = f"munkatars.{employee_id:02d}@rezrigo.iroda.invalid"
        staff[employee_id] = (name, email)
        insert(db, "munkatars", employee_id, name, role, email, manager_id)

    for category_id, name in enumerate(CATEGORIES, 1):
        insert(db, "termekkategoria", category_id, name)
    localized = {}
    product_file = ROOT / "scripts" / "termekek.txt"
    for line in product_file.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            product_id, name, package, vat = line.split("|")
            localized[int(product_id)] = (name, package, int(vat))
    products = {}
    for row in source.execute("SELECT * FROM Products ORDER BY ProductID"):
        i = row["ProductID"]
        name, package, vat = localized[i]
        price = huf(row["UnitPrice"])
        products[i] = (name, vat, price, int(row["Discontinued"]))
        insert(db, "termek", i, f"ELM-{i:04d}", name, row["CategoryID"], 100 + row["SupplierID"],
               package, price, vat, row["UnitsInStock"], row["UnitsOnOrder"],
               row["ReorderLevel"], int(row["Discontinued"]))
    if products.keys() != localized.keys():
        raise ValueError("A termékmegfeleltetés és a forrás cikktörzse eltér.")
    return customers, staff, products


def contracts(db, customers):
    terms = {}
    for customer_id, _, _, days, _, _ in customers.values():
        if customer_id % 3 != 1:
            continue
        starts = date(2025, 1, 1)
        ends = date(2026, 12, 31) if customer_id % 2 else date(2026, 9, 30)
        signed = add_days(starts, -12)
        ref = code("SZER", signed, customer_id)
        description = (
            "A keretszerződés az egyedileg visszaigazolt élelmiszer-megrendelésekre vonatkozik. "
            "A mennyiséget, az árat és az átadás helyét minden rendelésnél külön rögzítik. "
            f"A számla kiegyenlítése banki átutalással, {days} naptári napon belül esedékes."
        )
        insert(db, "szerzodes", customer_id, ref, customer_id, 1 + customer_id % len(STAFF),
               "Élelmiszer-ellátási keretszerződés", signed, starts, ends, days, description)
        terms[customer_id] = (starts, ends)
    return terms


def contract_at(terms, customer_id, day):
    start, end = terms.get(customer_id, (date.max, date.min))
    return customer_id if start <= day <= end else None


class Communication:
    def __init__(self, db, staff):
        self.db = db
        self.staff = staff
        self.thread_id = 0
        self.message_id = 0
        self.task_id = 0

    def thread(self, customer, offer, order, invoice, subject):
        self.thread_id += 1
        insert(self.db, "levelezes", self.thread_id, customer, offer, order, invoice, subject)
        return self.thread_id

    def message(self, thread, parent, day, inbound, sender, recipient, subject, body):
        self.message_id += 1
        hour = "13:40:00" if inbound else "09:15:00"
        direction = "bejövő" if inbound else "kimenő"
        insert(self.db, "email", self.message_id, thread, parent, f"{day.isoformat()}T{hour}",
               direction, sender, recipient, subject, body)
        return self.message_id

    def task(self, customer, owner, offer, order, invoice, title, description, kind,
             priority, status, created, due, closed=None):
        self.task_id += 1
        insert(self.db, "feladat", self.task_id, customer, owner, offer, order, invoice, title,
               description, kind, priority, status, created, due, closed)

    def offer_mail(self, offer_id, customer, owner, contact_data, reference, day,
                   expiry, status, closed, mode):
        _, external, first_name = contact_data
        name, internal = self.staff[owner]
        subject = f"Élelmiszer-nagykereskedelmi ajánlat – {reference}"
        thread = self.thread(customer, offer_id, None, None, subject)
        first = self.message(
            thread, None, day, False, internal, external, subject,
            f"Kedves {first_name}!\n\nKüldöm a kért ajánlatot ({reference}). "
            f"Az árakat {expiry:%Y. %m. %d.}-ig tudjuk tartani. "
            f"Kérlek, jelezz, ha a kiszerelésen vagy az átvétel időpontján változtatnátok.\n\nÜdv,\n{name}",
        )
        if mode == "nyitott":
            replies = (
                "Kérlek, nézzétek meg, megoldható-e a kisebb kiszerelés. Az eredeti mennyiséget addig ne rögzítsétek rendelésként.",
                "Az ár rendben lenne, de a szállítási ablakot még egyeztetem a raktárral. Hétfőn visszajelzek.",
                "Az ajánlatot még nézzük. Kérlek, erősítsétek meg, meddig tudjátok tartani a készletet.",
            )
            reply = replies[offer_id % len(replies)]
        elif mode == "vár":
            reply = "Megkaptam, köszönöm. A következő beszerzési körben még visszatérhetünk rá."
        elif status == "elfogadva":
            reply = "Köszönöm, elfogadjuk az ajánlatot. Kérlek, a visszaigazolt tételeket rögzítsétek rendelésként."
        elif status == "elutasítva":
            reply = "Köszönöm az ajánlatot. Erre a beszerzésre végül kisebb keretünk maradt, ezért most nem rendelünk."
        else:
            return
        reply_day = closed if status in ("elfogadva", "elutasítva") else add_days(day, 2)
        self.message(thread, first, reply_day, True, external, internal, f"Re: {subject}",
                     f"Kedves {name.split()[-1]}!\n\n{reply}\n\nÜdv,\n{first_name}")

    def delivery_followup(self, order_id, customer, owner, contact_data, reference,
                          created, due, shipped, delivered):
        _, external, first_name = contact_data
        name, internal = self.staff[owner]
        subject = f"Szállítási időpont egyeztetése – {reference}"
        thread = self.thread(customer, None, order_id, None, subject)
        first = self.message(
            thread, None, created, True, external, internal, subject,
            f"Kedves {name.split()[-1]}!\n\n"
            f"A {reference} rendelés átvételére {due:%Y. %m. %d.}-re kértünk időpontot. "
            f"Kérlek, jelezd, melyik napszakban várhatjuk a fuvart.\n\nKöszönöm,\n{first_name}",
        )
        if shipped:
            self.message(thread, first, shipped, False, internal, external, f"Re: {subject}",
                         f"Kedves {first_name}!\n\nA raktár átadta a csomagokat a fuvarozónak. "
                         f"A fuvarozó fogja pontosítani az érkezés idejét.\n\nÜdv,\n{name}")
        self.task(customer, owner, None, order_id, None, "Átvételi időablak ellenőrzése",
                  "Nézd meg a fuvar állapotát, és szükség esetén egyeztess a vevő raktárával.",
                  "szállítás", "normál", "kész" if delivered else "nyitott",
                  created, due, delivered)


def accepted_offer(db, comm, order_id, customer_id, owner, main, terms, placed, lines):
    quoted = add_days(placed, -7)
    expiry = add_days(quoted, 14)
    reference = code("AJ", quoted, order_id)
    insert(db, "ajanlat", order_id, reference, customer_id, main[0], owner,
           contract_at(terms, customer_id, quoted), "Áruellátási ajánlat", quoted, expiry,
           "elfogadva", placed)
    for line in lines:
        insert(db, "ajanlattetel", order_id, *line)
    comm.offer_mail(order_id, customer_id, owner, main, reference, quoted, expiry,
                    "elfogadva", placed, None)


def open_pipeline(db, comm, customers, products, terms):
    # Ugyanarra a fordulónapra különböző, egymástól független CRM-állapotok.
    cases = [
        ("kiküldve", -32, -18, None, None),
        ("kiküldve", -22, -8, None, "vár"),
        ("egyeztetés alatt", -19, -5, None, "nyitott"),
        ("kiküldve", -5, 9, None, None),
        ("egyeztetés alatt", -6, 8, None, "nyitott"),
        ("piszkozat", -2, 12, None, None),
        ("elutasítva", -26, -12, -19, None),
        ("lezárva", -44, -30, -24, None),
        ("kiküldve", -14, 0, None, None),
    ]
    titles = (
        "Novemberi árufeltöltés", "Ünnepi kínálat beszerzése", "Készletpótlás a decemberi időszakra",
        "Év végi rendezvény ellátása", "Heti étlap alapanyagai", "Téli választék összeállítása",
        "Üzleti reggeli alapanyagai", "Hűtött áruk utánrendelése", "Szezonális kóstolócsomag",
    )
    clients = list(customers.values())
    active_products = [i for i, product in products.items() if not product[3]]
    for i in range(72):
        offer_id = 20001 + i
        customer_id, _, _, _, main, _ = clients[(i * 19) % len(clients)]
        status, made, until, close_offset, mode = cases[i % len(cases)]
        created, expiry = add_days(SNAPSHOT, made), add_days(SNAPSHOT, until)
        closed = add_days(SNAPSHOT, close_offset) if close_offset is not None else None
        owner = 1 + (i + i // len(cases)) % len(STAFF)
        reference = code("AJ", created, offer_id)
        title = titles[(i + i // len(cases)) % len(titles)]
        insert(db, "ajanlat", offer_id, reference, customer_id, main[0], owner,
               contract_at(terms, customer_id, created), title, created, expiry, status, closed)
        for j in range(2 + i % 3):
            product_id = active_products[(i * 7 + j * 13) % len(active_products)]
            _, vat, price, _ = products[product_id]
            insert(db, "ajanlattetel", offer_id, j + 1, product_id, 4 + (i * 5 + j * 7) % 41,
                   price, (0, 300, 500, 800)[i % 4], vat)
        if status != "piszkozat":
            comm.offer_mail(offer_id, customer_id, owner, main, reference, created,
                            expiry, status, closed, mode)
        if mode == "nyitott":
            comm.task(customer_id, owner, offer_id, None, None,
                      "A vevő válaszára várunk",
                      "Az ajánlat nyitott. Ellenőrizd a vevő kérését a levelezésben, majd egyeztess a raktárral.",
                      "ajánlatkövetés", "magas" if expiry < SNAPSHOT else "normál",
                      "folyamatban", add_days(created, 2), add_days(SNAPSHOT, 2))
        elif status == "lezárva":
            comm.task(customer_id, owner, offer_id, None, None,
                      "Ajánlat lezárása",
                      "A vevő nem jelzett vissza az érvényességi időn belül. A lezárást rögzítettük.",
                      "ajánlatkövetés", "alacsony", "kész", expiry, add_days(expiry, 7), closed)
        elif status == "kiküldve" and i % 2:
            comm.task(customer_id, owner, offer_id, None, None,
                      "Visszajelzés ellenőrzése",
                      "Nézd meg, érkezett-e válasz az ajánlatra.",
                      "ajánlatkövetés", "normál", "nyitott", created, add_days(expiry, 2))


def sales(source, db, comm, customers, products, terms):
    by_order = defaultdict(list)
    for row in source.execute("""
        SELECT OrderID, ProductID, UnitPrice, Quantity, Discount
        FROM "Order Details" ORDER BY OrderID, ProductID
    """):
        order_id, product_id, unit_price, quantity, discount = row
        lines = by_order[order_id]
        lines.append((len(lines) + 1, product_id, quantity, huf(unit_price),
                      rounded(Decimal(str(discount)) * 10000), products[product_id][1]))

    for row in source.execute("""
        SELECT OrderID, CustomerID, EmployeeID, OrderDate, RequiredDate, ShippedDate, ShipVia, Freight
        FROM Orders ORDER BY OrderID
    """):
        order_id, external, owner, ordered_on, requested_on, shipped_on, shipper_id, freight = row
        customer, town, street, terms_days, main, billing = customers[external]
        placed, due = imported_date(ordered_on), imported_date(requested_on)
        shipped = imported_date(shipped_on) if shipped_on else None
        delivered = add_days(shipped, 1 + order_id % 3) if shipped else None
        contract_id = contract_at(terms, customer, placed)
        order_reference = code("MR", placed, order_id)
        lines = by_order[order_id]
        if shipped is None:
            status = "lemondva" if order_id % 4 == 0 else "feldolgozás alatt"
        elif delivered > SNAPSHOT:
            status, delivered = "feladva", None
        else:
            status = "teljesítve"
        offer_id = None
        if order_id % 7 == 0 and status != "lemondva":
            offer_id = order_id
            accepted_offer(db, comm, order_id, customer, owner, main, terms, placed, lines)
        shipping_fee = huf(freight)
        if customer % 6 == 0:
            # A fióktelep címe eltér a vevő székhelyétől.
            town, street = address(customer + 59)
        insert(db, "rendeles", order_id, order_reference, customer, owner, offer_id, contract_id,
               200 + shipper_id, placed, due, shipped, status, shipping_fee, town, street, delivered)
        for line in lines:
            insert(db, "rendelestetel", order_id, *line)
        if (order_id % 11 == 0 and status != "lemondva"
                and (shipped is None or shipped > placed)):
            comm.delivery_followup(order_id, customer, owner, main, order_reference,
                                   placed, due, shipped, delivered)
        if delivered is not None:
            invoice(db, comm, order_id, customer, owner, billing, terms_days,
                    delivered, shipping_fee, lines, products)


def invoice(db, comm, order_id, customer, owner, contact_data, terms_days,
            delivered, shipping_fee, lines, products):
    issued = min(add_days(delivered, order_id % 3), SNAPSHOT)
    due = add_days(issued, terms_days)
    reference = code("SZ", issued, order_id)
    insert(db, "szamla", order_id, reference, order_id, customer, COMPANY_ID, issued, delivered,
           due, "átutalás", "HUF")
    sql = """
        INSERT INTO szamlatetel
          (szamla_id,sorszam,termek_id,megnevezes,mertekegyseg,mennyiseg,
           netto_egysegar_ft,kedvezmeny_bp,afa_szazalek)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    for line_number, product_id, quantity, price, discount, vat in lines:
        db.execute(sql, (order_id, line_number, product_id, products[product_id][0],
                         "csomag", quantity, price, discount, vat))
    if shipping_fee:
        db.execute(sql, (order_id, len(lines) + 1, None, "Szállítási díj",
                         "alkalom", 1, shipping_fee, 0, 27))
    total, = db.execute("SELECT sum(brutto_ft) FROM szamlatetel WHERE szamla_id = ?", (order_id,)).fetchone()
    value_date = max(issued, add_days(due, (order_id % 19) - 7))
    payments = []
    recent = (SNAPSHOT - issued).days < 100
    if recent and order_id % 13 == 0:
        payments = []
    elif recent and order_id % 11 == 0:
        payments = [(add_days(issued, 3), total // 2)]
    elif order_id % 23 == 0:
        first_amount = total // 3
        first_date = min(value_date, add_days(issued, 4))
        payments = [(first_date, first_amount), (value_date, total - first_amount)]
    else:
        payments = [(value_date, total)]
    booked = 0
    for j, (day, amount) in enumerate(payments, 1):
        if day <= SNAPSHOT and amount:
            insert(db, "befizetes", order_id * 10 + j, order_id, f"UT-{day.year}-{order_id}-{j}",
                   day, amount, reference)
            booked += amount

    if due < SNAPSHOT and booked < total:
        _, external, first_name = contact_data
        internal = "penzugy@rezrigo.iroda.invalid"
        subject = f"Fizetési emlékeztető – {reference}"
        thread = comm.thread(customer, None, None, order_id, subject)
        reminder_day = min(add_days(due, 2), SNAPSHOT)
        amount_text = f"{total - booked:,}".replace(",", " ")
        first = comm.message(
            thread, None, reminder_day, False, internal, external, subject,
            f"Tisztelt Partnerünk!\n\nA {reference} számú számla fizetési határideje "
            f"{due:%Y. %m. %d.} volt. A nyilvántartásunk szerint a fennmaradó összeg {amount_text} Ft. "
            f"Kérjük, utaláskor a számlaszámot írják a közleménybe.\n\nÜdvözlettel,\nRézrigó Kft. pénzügy",
        )
        if order_id % 2 == 0 and reminder_day < SNAPSHOT:
            comm.message(thread, first, add_days(reminder_day, 1), True, external, internal,
                         f"Re: {subject}",
                         "Tisztelt Pénzügy!\n\nKöszönöm a jelzést. Egyeztetek a könyvelésünkkel "
                         f"az utalás időpontjáról, és visszajelzek.\n\nÜdvözlettel,\n{first_name}")
        comm.task(customer, owner, None, None, order_id, "Lejárt számla követése",
                  "Ellenőrizd a banki jóváírásokat, és szükség esetén kérj utalási időpontot a vevőtől.",
                  "számlakövetés", "magas", "nyitott", reminder_day, add_days(reminder_day, 5))


def build(source_dir, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    # A végleges fájl csak sikeres ellenőrzés után cserélődik le.
    with TemporaryDirectory(dir=output.parent, prefix=".iroda-") as temp_dir:
        draft = Path(temp_dir) / "seed.db"
        with closing(sqlite3.connect(":memory:")) as source, closing(sqlite3.connect(draft)) as db:
            load_source(source, source_dir)
            db.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
            with db:
                record_provenance(db)
                customers, staff, products = masters(source, db)
                terms = contracts(db, customers)
                comm = Communication(db, staff)
                sales(source, db, comm, customers, products, terms)
                open_pipeline(db, comm, customers, products, terms)
            verify(db)
        draft.replace(output)


def verify(db):
    if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise ValueError("SQLite integritási hiba.")
    if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ValueError("Sérült idegen kulcs.")
    for table, expected in (
        ("termek", 77), ("termekkategoria", 8), ("munkatars", 9),
        ("rendeles", 830), ("rendelestetel", 2155),
    ):
        actual, = db.execute(f"SELECT count(*) FROM {table}").fetchone()
        if actual != expected:
            raise ValueError(f"{table}: {actual} rekord, a várt érték {expected}.")
    for role, expected in (("vevő", 93), ("beszállító", 29), ("fuvarozó", 3), ("saját cég", 1)):
        actual, = db.execute("SELECT count(*) FROM partner WHERE tipus = ?", (role,)).fetchone()
        if actual != expected:
            raise ValueError(f"{role}: {actual} partner, a várt érték {expected}.")

    # A tételes egyezés a terméket, mennyiséget, egységárat, kedvezményt és áfát is érinti.
    checks = {
        "elfogadott ajánlat és rendelés": """
            SELECT r.id FROM rendeles r JOIN ajanlat a ON a.id = r.ajanlat_id
            WHERE a.allapot <> 'elfogadva' OR a.lezart_nap > r.kelt
            UNION ALL
            SELECT r.id FROM rendeles r JOIN rendelestetel t ON r.id = t.rendeles_id
            WHERE r.ajanlat_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM ajanlattetel a WHERE a.ajanlat_id = r.ajanlat_id
                AND (a.sorszam, a.termek_id, a.mennyiseg, a.netto_egysegar_ft, a.kedvezmeny_bp, a.afa_szazalek)
                  = (t.sorszam, t.termek_id, t.mennyiseg, t.netto_egysegar_ft, t.kedvezmeny_bp, t.afa_szazalek)
            )
        """,
        "számla és rendelés": """
            SELECT r.id FROM rendeles r LEFT JOIN szamla s ON s.rendeles_id = r.id
            WHERE (s.id IS NOT NULL) <> (r.allapot = 'teljesítve')
               OR s.teljesites_napja <> r.teljesites_napja
            UNION ALL
            SELECT s.id FROM szamla s JOIN rendelestetel t ON s.rendeles_id = t.rendeles_id
            WHERE NOT EXISTS (
                SELECT 1 FROM szamlatetel a WHERE a.szamla_id = s.id
                AND (a.sorszam, a.termek_id, a.mennyiseg, a.netto_egysegar_ft, a.kedvezmeny_bp, a.afa_szazalek)
                  = (t.sorszam, t.termek_id, t.mennyiseg, t.netto_egysegar_ft, t.kedvezmeny_bp, t.afa_szazalek)
            )
        """,
        "befizetés időpontja": """
            SELECT b.id FROM befizetes b JOIN szamla s ON s.id = b.szamla_id
            WHERE b.ertek_nap < s.kelt OR b.ertek_nap > (SELECT ertek FROM metaadat WHERE kulcs = 'fordulonap')
        """,
        "túlfizetés": "SELECT szamla_id FROM szamla_egyenleg WHERE hatralevo_ft < 0",
        "válasz időrendje": """
            SELECT e.id FROM email e JOIN email v ON v.id = e.valasz_erre_id
            WHERE e.kuldes_ideje <= v.kuldes_ideje
        """,
        "hiányzó ajánlattétel": """
            SELECT a.id FROM ajanlat a WHERE NOT EXISTS (
                SELECT 1 FROM ajanlattetel t WHERE t.ajanlat_id = a.id
            )
        """,
    }
    for label, query in checks.items():
        first = db.execute(query).fetchone()
        if first is not None:
            raise ValueError(f"Üzleti konzisztenciahiba ({label}), rekord: {first[0]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="A két rögzített Northwind SQL-fájl helye offline futtatáshoz.")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "seed.db")
    args = parser.parse_args()
    build(args.source_dir, args.output.resolve())
    print(f"Elkészült és ellenőrizve: {args.output.resolve()}")


if __name__ == "__main__":
    main()
