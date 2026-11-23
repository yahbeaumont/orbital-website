# Examples

Three small programs that demonstrate the techniques used in the site. They are written from scratch for this repository, with generic names and fictional data. None of them contains product copy, real prices, real routes or the actual generator code.

Requirements: Python 3.9 or newer, standard library only, no installation step. Each file runs on its own and writes its output to a directory or to standard output, so nothing outside the working directory is touched.

---

## `build_static_pages.py`

**Demonstrates:** a page family as a function. A content dictionary holds the text and metadata, one `shell()` function holds the layout, and `render()` composes the two. Navigation is defined once as a list and rendered with a relative root that depends on how deep the page sits, which is what lets the same output work at a domain root or in a subdirectory.

**What to look for:** escaping happens at the boundary, once, when text enters HTML. The generator never formats money, dates or prices; those arrive already formatted, from whatever module owns them. That is the discipline that keeps a number from being typed twice.

```sh
python3 build_static_pages.py /tmp/example-site
```

Output: three `index.html` files under the directory you pass, or under `public/` by default. Open any of them directly in a browser.

---

## `hreflang_sitemap.py`

**Demonstrates:** deriving a multilingual sitemap from what was published. The program walks each locale directory, skips pages marked `noindex`, and pairs the rest through a locale independent key. Slugs that are translated rather than transliterated are reconciled by an alias map, so `obrigado` and `thank-you` are recognised as the same page. Every URL is emitted with its `pt-BR`, `en` and `x-default` alternates, and `x-default` points at English when the pair is complete.

**What to look for:** the pairing key is the whole trick. Without it, a translated slug produces two unpaired URLs and an `hreflang` set that tells search engines nothing true. Also note what is not in the output: the page marked `noindex` in the demo tree never reaches the sitemap.

```sh
python3 hreflang_sitemap.py                # builds a demo tree in a temp directory
python3 hreflang_sitemap.py path/to/site   # scans a real tree
```

Output: `sitemap.xml` written next to the site tree, and printed to standard output.

---

## `currency_rounding.py`

**Demonstrates:** converting and rounding money for a static bilingual page. The rate is a constant, because a static page cannot show a figure that changes between visits. Rounding uses a step chosen by magnitude, so a converted number reads as an estimate instead of a spreadsheet cell. Formatting follows the locale, not the currency: dot as thousands separator in Portuguese, comma in English.

**What to look for:** payback is computed from the converted price, so two locales can disagree and both be right. The demo prints 22 months for one case in Portuguese and 21 in English, which is the arithmetic closing in different currencies rather than a bug.

```sh
python3 currency_rounding.py
```

Output: printed lines only. No files are written.

---

## What these examples are not

They are not a template to build the site from, and they deliberately omit the parts that make the real pipeline interesting at scale: the orchestration order, the post-processing steps, the structured data builders, the content model and the per-page metadata. Those are described in [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) and [../docs/DECISIONS.md](../docs/DECISIONS.md).
