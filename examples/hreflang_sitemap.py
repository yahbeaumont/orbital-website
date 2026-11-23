#!/usr/bin/env python3
"""Build a multilingual sitemap from the pages that were actually published.

The sitemap is derived, never maintained: walk each locale directory, skip
anything marked noindex, pair the remaining pages by a locale independent
key, and emit one <url> per page with its alternates.

Usage:
    python3 hreflang_sitemap.py [site_dir]
    python3 hreflang_sitemap.py            # builds a demo tree in a temp dir
"""

import re
import sys
import tempfile
from pathlib import Path

BASE = "https://example.com"
LOCALES = (("pt-br", "pt-BR"), ("en", "en"))
# slugs that are translated rather than transliterated: slug -> shared key
ALIASES = {"thank-you": "thanks", "obrigado": "thanks"}
SKIP_DIRS = {"_archive"}


def pages(root: Path, locale: str) -> list[tuple[str, str]]:
    """(relative path, pairing key) for every indexable page in a locale."""
    found = []
    for file in sorted((root / locale).rglob("index.html")):
        if SKIP_DIRS.intersection(file.parts):
            continue
        if re.search(r'name="robots"[^>]*noindex', file.read_text(encoding="utf-8")):
            continue
        rel = file.parent.relative_to(root / locale).as_posix()
        rel = "" if rel == "." else rel
        found.append((rel, ALIASES.get(rel, rel)))
    return found


def url(locale: str, rel: str) -> str:
    return f"{BASE}/{locale}/{rel}/" if rel else f"{BASE}/{locale}/"


def build(root: Path) -> str:
    inventory = {locale: pages(root, locale) for locale, _ in LOCALES}
    by_key = {loc: {key: rel for rel, key in inventory[loc]} for loc, _ in LOCALES}
    blocks = []
    for locale, _ in LOCALES:
        for rel, key in inventory[locale]:
            pairs = [(name, url(other, by_key[other][key]))
                     for other, name in LOCALES if key in by_key[other]]
            # x-default points at English when the pair is complete
            fallback = dict(pairs).get("en") or (pairs[0][1] if pairs else url(locale, rel))
            lines = ["  <url>", f"    <loc>{url(locale, rel)}</loc>"]
            for name, href in pairs + [("x-default", fallback)]:
                lines.append(f'    <xhtml:link rel="alternate" hreflang="{name}" href="{href}"/>')
            blocks.append("\n".join(lines + ["  </url>"]))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(blocks) + "\n</urlset>\n"
    )


def demo_tree(root: Path) -> None:
    """Two pages per locale, one translated slug, one noindex page."""
    blank = "<html><head></head><body></body></html>"
    targets = [("pt-br", ""), ("pt-br", "products"), ("pt-br", "obrigado"),
               ("en", ""), ("en", "products"), ("en", "thank-you")]
    for locale, rel in targets:
        path = root / locale / rel / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(blank, encoding="utf-8")
    draft = root / "en" / "draft" / "index.html"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text('<meta name="robots" content="noindex">', encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        site = Path(sys.argv[1])
    else:
        site = Path(tempfile.mkdtemp(prefix="sitemap-demo-"))
        demo_tree(site)
        print(f"demo tree: {site}")
    xml = build(site)
    (site / "sitemap.xml").write_text(xml, encoding="utf-8")
    print(xml)
