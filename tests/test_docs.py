"""Checks for the rules in docs/design-system.*.md that can be automated."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
TOKENS = ROOT / "docs/design/tokens.css"
SITE_TOKENS = ROOT / "site/dist/tokens.css"

# Foreground, background and the WCAG minimum for that use.
CONTRAST_PAIRS = [
    ("ink", "paper", 4.5),
    ("ink", "surface", 4.5),
    ("muted", "paper", 4.5),
    ("muted", "surface", 4.5),
    ("muted", "copper-wash", 4.5),
    ("copper", "paper", 4.5),
    ("copper", "surface", 4.5),
    ("copper", "copper-wash", 4.5),
    ("on-copper", "copper", 4.5),
    ("on-copper", "copper-hover", 4.5),
    ("on-ledger", "ledger", 4.5),
    ("muted-on-ledger", "ledger", 4.5),
    ("copper-on-ledger", "ledger", 4.5),
    ("correct-ink", "correct-fill", 4.5),
    ("incorrect-ink", "incorrect-fill", 4.5),
    ("attention-ink", "attention-fill", 4.5),
    ("neutral-ink", "neutral-fill", 4.5),
    ("control-border", "paper", 3),
    ("control-border", "surface", 3),
    ("control-border", "copper-wash", 3),
    ("focus", "paper", 3),
    ("focus-on-ledger", "ledger", 3),
    ("correct-ink", "paper", 3),
    ("incorrect-ink", "paper", 3),
    ("attention-ink", "paper", 3),
    ("ledger", "paper", 3),
]

DOC_PAIRS = [
    ("README.md", "README.en.md"),
    ("ADATLEIRAS.md", "DATASET.md"),
    ("docs/agent.hu.md", "docs/agent.en.md"),
    ("docs/benchmark.hu.md", "docs/benchmark.en.md"),
    ("docs/design-system.hu.md", "docs/design-system.en.md"),
    ("docs/mcp.hu.md", "docs/mcp.en.md"),
    ("docs/methodology.hu.md", "docs/methodology.en.md"),
]
ONE_FILE_DOCS = ["AGENTS.md", "CONTRIBUTING.md"]
DOCS = [path for pair in DOC_PAIRS for path in pair] + ONE_FILE_DOCS

FENCE = re.compile(r"^(~~~|```).*?^\1", re.DOTALL | re.MULTILINE)
LINK = re.compile(r"\]\(([^)\s]+)\)")


def tokens() -> dict[str, str]:
    values = dict(re.findall(r"--iroda-([\w-]+):\s*([^;]+);", TOKENS.read_text()))
    return {
        name: values[value[len("var(--iroda-") : -1]]
        if value.startswith("var(")
        else value
        for name, value in values.items()
    }


def luminance(color: str) -> float:
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = (
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    )
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(first: str, second: str) -> float:
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def prose(path: str) -> str:
    return FENCE.sub("", (ROOT / path).read_text())


def anchor(heading: str) -> str:
    text = re.sub(r"[^\w\- ]", "", heading.replace("`", "").strip().lower())
    return text.replace(" ", "-")


@pytest.mark.parametrize(("foreground", "background", "minimum"), CONTRAST_PAIRS)
def test_token_contrast(foreground, background, minimum):
    values = tokens()
    assert contrast(values[foreground], values[background]) >= minimum


def test_copper_stays_off_the_ledger():
    values = tokens()
    assert contrast(values["copper"], values["ledger"]) < 3


@pytest.mark.skipif(not SITE_TOKENS.exists(), reason="site checkout is not present")
def test_site_uses_current_tokens():
    assert SITE_TOKENS.read_text() == TOKENS.read_text()


@pytest.mark.skipif(not SITE_TOKENS.exists(), reason="site checkout is not present")
@pytest.mark.parametrize("page", ["site/dist/index.html", "site/dist/en/index.html"])
def test_live_case_file_uses_real_tools(page):
    html = (ROOT / page).read_text()
    shown = re.findall(r'<code class="run-tool">(\w+)</code>', html)
    assert len(shown) == 4
    tools = (ROOT / "mcp_server.py").read_text() + (ROOT / "iroda.py").read_text()
    for name in shown:
        assert f"def {name}(" in tools


@pytest.mark.skipif(not SITE_TOKENS.exists(), reason="site checkout is not present")
def test_motion_is_a_pure_function_of_the_timeline():
    script = (ROOT / "site/dist/motion.js").read_text()
    assert "Date.now" not in script
    assert "Math.random" not in script
    assert "prefers-reduced-motion" in script


@pytest.mark.parametrize("path", DOCS)
def test_document_opening(path):
    lines = [line for line in (ROOT / path).read_text().splitlines() if line.strip()]
    if lines[0].startswith("<img "):
        lines = lines[1:]
    assert lines[0].startswith("# ")
    assert re.fullmatch(r"`[^`]+`", lines[1]), "document label follows the title"
    start = 2
    if path.startswith("README"):
        start = next(i for i, line in enumerate(lines) if line.startswith("["))
        start = next(i for i in range(start, len(lines)) if "·" in lines[i])
        assert lines[start].startswith(("[English]", "[Magyar]"))
        return
    assert not lines[start].startswith("["), "purpose comes before the link row"
    assert lines[start + 1].startswith(("[English]", "[Magyar]"))


@pytest.mark.parametrize(("hungarian", "english"), DOC_PAIRS)
def test_language_pairs_match(hungarian, english):
    first, second = prose(hungarian), prose(english)
    for pattern in (r"^#{2,3} ", r"^\|", r"^> ", r"^\d+\. ", r"^- "):
        assert len(re.findall(pattern, first, re.MULTILINE)) == len(
            re.findall(pattern, second, re.MULTILINE)
        ), pattern
    assert FENCE.findall((ROOT / hungarian).read_text()) == FENCE.findall(
        (ROOT / english).read_text()
    )


@pytest.mark.parametrize("path", DOCS)
def test_relative_links_resolve(path):
    source = ROOT / path
    for link in LINK.findall(prose(path)):
        if link.startswith(("http://", "https://", "mailto:")):
            continue
        target_path, _, fragment = link.partition("#")
        target = source.parent / target_path if target_path else source
        assert target.exists(), link
        if fragment and target.suffix == ".md":
            headings = re.findall(
                r"^#{1,6} (.+)$", FENCE.sub("", target.read_text()), re.MULTILINE
            )
            assert fragment in {anchor(heading) for heading in headings}, link


@pytest.mark.parametrize("path", DOCS)
def test_code_fences_use_tildes(path):
    assert "\n```" not in (ROOT / path).read_text()


SITE = ROOT / "site/dist"
SITE_URL = "https://www.irodabench.hu/"
SITE_PAGES = {
    "index.html": SITE_URL,
    "en/index.html": SITE_URL + "en/",
    "modszertan/index.html": SITE_URL + "modszertan/",
    "en/methodology/index.html": SITE_URL + "en/methodology/",
}


def head_links(html: str) -> tuple[str, dict[str, str]]:
    canonical = re.findall(r'<link rel="canonical" href="([^"]+)">', html)
    alternates = dict(
        re.findall(r'<link rel="alternate" hreflang="([\w-]+)" href="([^"]+)">', html)
    )
    assert len(canonical) == 1
    return canonical[0], alternates


@pytest.mark.skipif(not SITE_TOKENS.exists(), reason="site checkout is not present")
@pytest.mark.parametrize(("page", "url"), SITE_PAGES.items())
def test_site_page_head(page, url):

    html = (SITE / page).read_text()
    canonical, alternates = head_links(html)
    assert canonical == url
    assert set(alternates) == {"hu", "en", "x-default"}
    assert url in alternates.values()
    assert alternates["x-default"] == alternates["hu"]
    for target in alternates.values():
        assert target.startswith(SITE_URL)
        other = next(p for p, u in SITE_PAGES.items() if u == target)
        assert head_links((SITE / other).read_text())[1] == alternates
    assert f'<meta property="og:url" content="{url}">' in html
    image = re.search(r'<meta property="og:image" content="([^"]+)">', html)[1]
    assert (SITE / image.removeprefix(SITE_URL)).exists()
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL
    )
    assert len(blocks) == 1
    json.loads(blocks[0])


@pytest.mark.skipif(not SITE_TOKENS.exists(), reason="site checkout is not present")
def test_sitemap_lists_every_page():
    sitemap = (SITE / "sitemap.xml").read_text()
    assert set(re.findall(r"<loc>([^<]+)</loc>", sitemap)) == set(SITE_PAGES.values())
    assert f"Sitemap: {SITE_URL}sitemap.xml" in (SITE / "robots.txt").read_text()
