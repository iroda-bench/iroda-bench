# IRODA 0.1.0 dataset

`IRODA / DATASET / v0.1.0`

See where the data comes from, what the schema contains, and how to rebuild the seed.

[Magyar](ADATLEIRAS.md) · [Project overview](README.en.md)

The 8 November 2026 snapshot models a fictional Hungarian domestic B2B food wholesaler. Any resemblance between synthetic company names, streets or people and real ones is coincidental. Tax identifiers are deliberately invalid test values. Email addresses use the reserved `.invalid` domain. [RFC 2606](https://datatracker.ietf.org/doc/html/rfc2606)

## Sources and licenses

| Source | Role and license |
| --- | --- |
| [Northwind SQLite3, pinned revision](https://github.com/jpwhite3/northwind-SQLite3/tree/4f56e7f5906dfd23b25244c5bfe8fb5da6402efd) | Data source. The generator runs upstream `src/create.sql` and `src/update.sql` in memory. The MIT notice and © 2016 JP White attribution are preserved in the [license copy](sources/LICENSE-Northwind-SQLite3.txt). |
| [Microsoft SQL Server Northwind](https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/northwind-pubs) | Additional provenance reference. The SQLite upstream describes its source as the Access 2000 sample. IRODA does not import the separately released MIT-licensed SQL Server dataset. The [Microsoft notice](sources/LICENSE-Microsoft-SQL-Samples.txt) is included. |
| [DemoDB Northwind](https://northwind.demodb.dev/about/) | Reference used to distinguish the classic dataset from the `dist/northwind.db` version with random orders. The generator uses the pinned upstream SQL files. |
| IRODA | Original Hungarian mappings, synthetic records, business rules, generator, schema and documentation are covered by the [MIT license](LICENSE). Retain the upstream notices when redistributing the derived data. |
| [NAV Online Számla](https://github.com/nav-gov-hu/Online-Invoice) | Structural reference for invoice issue, fulfilment and due dates, and net, VAT and gross amounts. Its repository is [MIT licensed](https://github.com/nav-gov-hu/Online-Invoice/blob/master/LICENCE.md). IRODA does not include its XSD, XML, sample invoices, text or code. |
| [Hungarian Invoice Catalog Decisions](https://huggingface.co/datasets/k3dani/hu-invoice-catalog-decisions) | Reviewed item-identification dataset labeled CC BY 4.0. IRODA generates its invoices from its own orders and imports no records from this dataset. |
| [Synthetic Hungarian Document OCR Dataset](https://huggingface.co/datasets/GaborMadarasz/synthetic_OCR_dataset) | Reviewed dataset labeled Apache-2.0. IRODA includes no images or text from it. |

The locations, counties and example postal codes were assembled manually. The dataset uses simulated product VAT classifications and no downloaded company-register, corporate-report or postal-code database records. [Hungarian Post address formats](https://www.posta.hu/ugyfelszolgalat/nemzetkozi_iranyitoszam_formatumok) · [Hungarian VAT Act](https://njt.hu/jogszabaly/2007-127-00-00.82)

Sources and license labels were checked for the 8 November 2026 snapshot. The pinned hashes are also in the seed's `adatforras` table. The full notices are in `licenc_ertesites`.

| Input | SHA-256 |
| --- | --- |
| [create.sql](https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/4f56e7f5906dfd23b25244c5bfe8fb5da6402efd/src/create.sql) | `5854b536dea3fe8c586223bf7b47a793727dd44c34fc32537a68a97fec8e2f4b` |
| [update.sql](https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/4f56e7f5906dfd23b25244c5bfe8fb5da6402efd/src/update.sql) | `59df0f3c88b1878946b712cc6e8a7f37c971c802ff2ed611c59feb72acb39ea6` |
| [Upstream MIT notice](https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/4f56e7f5906dfd23b25244c5bfe8fb5da6402efd/LICENSE) | `c28e204be6418b87ae1c83127096aad9c9e1a218c365f8f4d630e84d8ba96c47` |
| [Microsoft MIT notice](https://raw.githubusercontent.com/microsoft/sql-server-samples/4693087abebd7e835f9ee46d005dcdaa03092a40/license.txt) | `201f3705979e932c92cd3c6ddbddf4dc3c71dcc5a82089a1e4018227cfe1cf09` |

## Localization and transformations

| Area | Retained fields and changes |
| --- | --- |
| Companies, addresses and contacts | `Customers`, `Suppliers` and `Shippers` share one partner table. Customer IDs start at 1 in source-key order. Supplier IDs add 100 to the source ID and carrier IDs add 200. Company names, legal forms, job titles, contacts, streets, street numbers and contact details are synthetic. Some customers have a separate finance contact or delivery address. |
| Employees | IDs and direct reporting relationships are retained. Names use Hungarian family-name-first order. Names, roles and contact details are localized. |
| Products | Product, category and supplier links, inventory counts, reorder thresholds and discontinued flags follow the source. The [77-entry mapping](scripts/termekek.txt) sets Hungarian product names, metric or item-count packaging and simulated VAT rates. Stock is the source snapshot. Orders do not generate an inventory movement ledger. |
| Orders | Order IDs and customer, owner, carrier, product, quantity and discount relationships are retained. Lines are numbered by product ID. Order, requested delivery and shipping dates receive the same offset. The latest order is dated November 6, 2026. Synthetic fulfilment follows shipping by one to three days. Orders stay shipped when fulfilment falls after the reference date. Unshipped orders include cancelled and in-progress records. |
| Amounts | Source unit prices and freight are scaled by 400 and rounded half up to whole forints. The multiplier is a generation parameter. Discounts use whole basis points, so 500 bp means 5%. Discounted net and the VAT calculated from it are rounded separately per line. Gross equals net plus VAT. |
| Quotes and contracts | Accepted quotes reflect their related order lines. Other quotes have generated dates, items and statuses, including expiry on the reference date, earlier expiry, negotiation and draft. Some customers have short synthetic framework contracts. A quote or order links to the customer contract valid on its own date. |
| Invoices and payments | Each fulfilled order has one invoice. Positive freight is a separate line. The due date is measured in calendar days from issue. Customer and framework-contract terms agree. Payment patterns include single payment, multiple credits, partial payment and unpaid balances. The records support benchmarking. NAV reporting and accounting are outside the model. |
| Email and tasks | Original Hungarian templates use simulated case IDs, names and deadlines. Quote, shipment and payment reminder threads may include an incoming reply. Tasks have an owner, priority, due date and status. |
| Omitted elements | Original names, addresses, telephone and fax numbers, URLs, photos, category images, biographies, demographic and territory tables and upstream views. The raw SQL files are fetched by the generator. |

## Data dictionary

Technical names are Hungarian without diacritics. Display text and statuses retain accents. The `id` column is an internal integer key. Fields such as `kod`, `cikkszam` and document numbers are unique display keys. Calendar dates use `YYYY-MM-DD`. Emails use Budapest local timestamps in `YYYY-MM-DDTHH:MM:SS`. `NULL` means missing or inapplicable. [SQLite schema](schema.sql)

| Tables and view | Purpose |
| --- | --- |
| `metaadat`, `adatforras`, `licenc_ertesites` | Version, reference date, timezone, provenance and license notices. |
| `telepules`, `partner`, `kapcsolattarto`, `munkatars` | Locations, partner types, contacts and reporting hierarchy. |
| `termekkategoria`, `termek` | Product categories, SKUs, supplier, packaging, price, VAT and inventory. |
| `szerzodes`, `ajanlat`, `ajanlattetel` | Framework terms, quote status and line items. Expiry and closing are separate. |
| `rendeles`, `rendelestetel` | Orders, optional quote and contract, delivery, carrier and line items. |
| `szamla`, `szamlatetel`, `befizetes` | Invoice headers, computed line totals and payments. Freight has a null product ID. |
| `szamla_egyenleg` | Invoice totals, payments and balance. `lejart` is 1 when payment is overdue at the reference date and a balance remains. |
| `levelezes`, `email`, `feladat` | Case-linked threads, emails and tasks. Composite foreign keys enforce customer and thread consistency. |

## Rebuild and verify

The generator uses the Python standard library and needs Python 3.10+ with SQLite 3.37+. The commands below use the benchmark's locked Python 3.12 environment and the SQLite CLI. Build to a separate path to keep the bundled input for comparison.

~~~sh
out=$(mktemp -d)
uv run --locked python scripts/build_seed.py --output "$out/seed.db"
sqlite3 -readonly "$out/seed.db" 'PRAGMA integrity_check; PRAGMA foreign_key_check;'
sqlite3 -readonly data/seed.db .dump > "$out/bundled.sql"
sqlite3 -readonly "$out/seed.db" .dump > "$out/rebuilt.sql"
diff -u "$out/bundled.sql" "$out/rebuilt.sql"
~~~

Integrity checking should print `ok`, followed by no foreign-key violations. An identical logical dump produces no diff output. SQLite versions can produce different database bytes for equivalent records, so use the bundled seed when comparing logged byte hashes. For an offline rebuild, download the pinned inputs listed above, name them `create.sql` and `update.sql`, and pass their directory as `--source-dir /path/to/northwind`. The license copies are already in `sources/`. Without `--output` the generator replaces the bundled seed after verification.

The generator verifies input and license hashes, classic record counts, SQLite integrity, foreign keys, line-level relationships, and the chronology of payments and replies. The snapshot backs the [MCP tools](docs/mcp.en.md) and the [benchmark cases](docs/methodology.en.md).
