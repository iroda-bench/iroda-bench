<img src="dist/mark.svg" width="40" height="40" alt="">

# IRODA project page

`IRODA / BILINGUAL HOMEPAGE`

The static homepage introduces the benchmark, shows a starter case, and explains how to run it. [Magyar](#magyar)

| Page or asset | Source |
| --- | --- |
| Magyar (default) | [Kezdőlap](dist/index.html) |
| English | [Homepage](dist/en/index.html) |
| Methodology | [Módszertan](dist/modszertan/index.html) · [Methodology](dist/en/methodology/index.html) |
| Shared design | [Tokens](dist/tokens.css) · [Stylesheet](dist/style.css) · [Motion](dist/motion.js) · [Mark](dist/mark.svg) |
| Search and sharing | [robots.txt](dist/robots.txt) · [Sitemap](dist/sitemap.xml) · [llms.txt](dist/llms.txt) · [Share card source](og/card.html) |

## Preview and update

From this directory, run the following command and open the printed address.

~~~sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
~~~

Edit each page together with its language counterpart. The site is served at `https://www.irodabench.hu/`. Every page has an absolute canonical URL, `hu`, `en` and `x-default` alternates, and JSON-LD that reuses the same `@id` values in both languages. When you add a page, list it in `sitemap.xml` and in `SITE_PAGES` in `tests/test_docs.py`, and update `lastmod` and the visible “Updated” date when content changes. To regenerate the 1200 × 630 share images after changing the card, run `node site/og/render.js` from the repository root. It needs Playwright. On pushes to `main`, the [CI workflow](../.github/workflows/ci.yml) deploys `dist/` to GitHub Pages after the tests pass. The repository's Pages source is GitHub Actions. Add measured results in both languages when a reproducible evaluation is ready to share.

The website source is [MIT licensed](LICENSE).

## Magyar

`IRODA / KÉTNYELVŰ KEZDŐLAP`

A statikus kezdőlap bemutatja a benchmarkot, egy mintafeladatot és a futtatás lépéseit. Az angol és magyar oldal közös tokeneket, stíluslapot és arculati jelet használ. [Forrásfájlok](#iroda-project-page)

### Előnézet és frissítés

Ebben a könyvtárban futtasd a fenti parancsot, majd nyisd meg a kiírt címet.

Minden oldalt a másik nyelvű párjával együtt frissíts. Az oldal címe `https://www.irodabench.hu/`. Minden oldal abszolút canonical URL-t, `hu`, `en` és `x-default` alternatívát, valamint mindkét nyelven azonos `@id` értékeket használó JSON-LD-t tartalmaz. Új oldalnál vedd fel a `sitemap.xml` fájlba és a `tests/test_docs.py` `SITE_PAGES` listájába, tartalmi változáskor pedig frissítsd a `lastmod` értéket és a látható „Frissítve” dátumot. A kártya módosítása után az 1200 × 630-as megosztási képeket a repó gyökeréből a `node site/og/render.js` paranccsal készítsd újra. Ehhez Playwright kell. A `main` ágra történő push után a [CI-folyamat](../.github/workflows/ci.yml) sikeres tesztek esetén telepíti a `dist/` könyvtárat a GitHub Pagesre. A repó Pages-forrása a GitHub Actions. Az eredményeket akkor add hozzá mindkét nyelven, amikor reprodukálható kiértékelés áll rendelkezésre.

A weboldal forráskódja [MIT-licencű](LICENSE).
