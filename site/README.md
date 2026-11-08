<img src="dist/mark.svg" width="40" height="40" alt="">

# IRODA project page

`IRODA / BILINGUAL HOMEPAGE`

The static homepage introduces the benchmark, shows a starter case, and explains how to run it. [Magyar](#magyar)

| Page or asset | Source |
| --- | --- |
| Magyar (default) | [Kezdőlap](dist/index.html) |
| English | [Homepage](dist/en/index.html) |
| Shared design | [Tokens](dist/tokens.css) · [Stylesheet](dist/style.css) · [Motion](dist/motion.js) · [Mark](dist/mark.svg) |

## Preview and update

From this directory, run the following command and open the printed address.

~~~sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
~~~

Edit both pages together. On pushes to `main`, the [CI workflow](../.github/workflows/ci.yml) deploys `dist/` to GitHub Pages after the tests pass. The repository's Pages source is GitHub Actions. Add measured results in both languages when a reproducible evaluation is ready to share.

The website source is [MIT licensed](LICENSE).

## Magyar

`IRODA / KÉTNYELVŰ KEZDŐLAP`

A statikus kezdőlap bemutatja a benchmarkot, egy mintafeladatot és a futtatás lépéseit. Az angol és magyar oldal közös tokeneket, stíluslapot és arculati jelet használ. [Forrásfájlok](#iroda-project-page)

### Előnézet és frissítés

Ebben a könyvtárban futtasd a fenti parancsot, majd nyisd meg a kiírt címet.

A két oldalt együtt frissítsd. A `main` ágra történő push után a [CI-folyamat](../.github/workflows/ci.yml) sikeres tesztek esetén telepíti a `dist/` könyvtárat a GitHub Pagesre. A repó Pages-forrása a GitHub Actions. Az eredményeket akkor add hozzá mindkét nyelven, amikor reprodukálható kiértékelés áll rendelkezésre.

A weboldal forráskódja [MIT-licencű](LICENSE).
