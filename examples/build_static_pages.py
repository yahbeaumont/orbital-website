#!/usr/bin/env python3
"""Generate a small static site from content dictionaries.

The idea: pages are data plus one shared shell. A page family is a function
that turns a dictionary into HTML, and the shell is rendered once per page
with that page's metadata. Changing the navigation means changing one
function, not every file.

Usage:
    python3 build_static_pages.py [output_dir]
"""

import html
import sys
from pathlib import Path

NAV = [("Home", "/"), ("Products", "/products/"), ("Support", "/support/")]

PAGES = [
    {"slug": "", "title": "Northwind Devices",
     "description": "Small machines that run models locally.",
     "heading": "Local inference, on your desk.",
     "body": ["No account, no quota, no network round trip."]},
    {"slug": "products", "title": "Products | Northwind Devices",
     "description": "Two models, one chassis.",
     "heading": "Products",
     "body": ["Standard: 64 GB unified memory.", "Studio: 128 GB unified memory."]},
    {"slug": "support", "title": "Support | Northwind Devices",
     "description": "Setup guides and warranty terms.",
     "heading": "Support",
     "body": ["Setup takes about ten minutes.", "Warranty runs for twelve months."]},
]


def shell(title: str, description: str, body: str, depth: int) -> str:
    """The layout every page shares. Depth is how far the page sits from the root."""
    root = "../" * depth
    links = "\n".join(f'      <a href="{root}{href.lstrip("/")}">{html.escape(label)}</a>'
                      for label, href in NAV)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}">
</head>
<body>
  <header><nav>
{links}
  </nav></header>
  <main>
{body}
  </main>
  <footer><p>Northwind Devices, fictional example.</p></footer>
</body>
</html>
"""


def render(page: dict) -> str:
    """One page: a heading, then paragraphs. Escaping happens here, once."""
    paragraphs = "\n".join(f"    <p>{html.escape(p)}</p>" for p in page["body"])
    body = f"    <h1>{html.escape(page['heading'])}</h1>\n{paragraphs}"
    depth = len([part for part in page["slug"].split("/") if part])
    return shell(page["title"], page["description"], body, depth)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "public")
    for page in PAGES:
        target = out / page["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(page), encoding="utf-8")
        print(f"wrote {target}")
    print(f"{len(PAGES)} pages written to {out.resolve()}")
