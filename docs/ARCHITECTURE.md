# Architecture

## Context

The site is a marketing and product surface for a hardware brand that sells machines running open-weight models locally. It publishes 45 routes per language in Portuguese and English, from a single repository, to Firebase Hosting. Nothing on the page is rendered on demand: the visitor receives a file generated on the build machine.

Two things follow from that. First, every page-level decision, routing, language pairing, canonical URL, structured data, price, has to be resolved before deploy. Second, the only runtime code is the small amount of JavaScript in the browser and the serverless functions behind the commerce and support paths.

## Components and responsibilities

**Content modules.** Copy lives in Python dictionaries, one subtree per locale, in the module that owns the page family. Cross-page data lives in dedicated modules: prices and product identity in one, model generation speeds in another, case entries and their relations in a third, currency conversion in a fourth. These modules contain data only, no markup.

**Shared shell.** One module exposes the header, the footer, the region bar, the purchase drawer and the icon set as functions. Thirteen of the sixteen page generators import it. Navigation labels, legal links and the language switch therefore exist once, and a change reaches every page on the next build.

**Page generators.** Sixteen scripts, one per page family: home, products, compact line, specifications, operating system, Ultra, models, about, hubs, cases, growth, demo, latency, legal, notebook composition and tag injection. Each reads its content dictionary, calls the shell functions and writes `index.html` into the language tree. A generator is the only place where the structure of that family is defined.

**Post-processing.** Five scripts run after the generators. One swaps interface images for their English variants. One adds social cards to pages that lack them. One appends a content hash to every CSS and JavaScript reference. One rebuilds `sitemap.xml` and `robots.txt` from the published files. One regenerates the redirect map.

**Orchestrator.** `tools/build_all.py` runs the sixteen generators and the five post steps as subprocesses, in a fixed order, and exits on the first non-zero status. It is the contract for "what a build is".

**Hosting layer.** Firebase Hosting serves the output directory, terminates TLS, applies the security and cache headers and evaluates the redirect rules. Its publish ignore list is the boundary between the repository and the public surface.

**Functions.** Three HTTPS functions in the same region handle payment session creation, order status lookup and the payment provider webhook, plus e-mail delivery and analytics forwarding. They hold every secret the product needs.

## Boundaries and contracts

*Repository to public surface.* The hosting configuration publishes the repository root but ignores tooling, documentation, functions, environment files, zip archives, markdown and repository metadata. Anything not on that list is public by default, which is why the list is treated as a security control rather than housekeeping.

*Build to browser.* Generators own the markup. The browser scripts never build a page section, they only mutate state that the markup already declares: classes for reveal animation, a transform for parallax, `aria-hidden` for overlays. A page without its script is readable and navigable.

*Browser to functions.* The browser sends a product identifier, a quantity and an address. It never sends a price, a currency or a total. The function resolves those from its own catalogue and rejects identifiers it does not know.

*Payment provider to functions.* The webhook verifies the signature against the raw request body before any effect. An unsigned or mismatched request has no side effect at all.

*Image to fallback.* The parallax targets an `<img>` by id. If the image fails, an inline handler reveals a CSS chassis that is the image's previous sibling, and an observer copies the transform from the image to the chassis. The ids live on the image, not on a wrapper, and that is a rule other markup must respect.

## A request through the site

A visitor requests a product page. The CDN answers with a file generated at build time; there is no origin render. The document declares its language, canonical URL and three `hreflang` alternates, and carries `Product` and `Offer` structured data whose price came from the price module during the build. CSS and JavaScript arrive with a content hash in the query string, so a browser holding an old copy fetches the new one after a deploy. The browser runs the shell script for the region bar and the header, and the interaction script for reveals, modals and the purchase drawer. Choosing a product writes only identifiers and quantities to local storage. Confirming a purchase navigates to the checkout page, which calls the payment function; the function validates the request, resolves prices server side, creates a hosted session and returns a redirect URL. The confirmation page later reads the order status through a second function, which returns a masked e-mail address.

A build run follows the same logic in reverse. A content module changes, `build_all.py` regenerates every page, the post steps re-stamp assets and rebuild the sitemap from what exists on disk, and the output is published.

## Conceptual data model

*Locale.* Two instances, `pt-br` and `en`, each with a URL prefix, a currency and a set of routes.

*Route.* A path inside a locale, materialised as a directory with an `index.html`. A route carries a page type, a canonical URL, an optional `noindex` flag and an identity key used for pairing.

*Locale pair.* Two routes, one per locale, that share an identity key. The key is usually the path; a small alias map handles slugs that differ between languages. A pair may be incomplete, and an incomplete pair produces no `hreflang` alternate.

*Product.* An identifier, a display name, a model name, a specification set and a price per currency. Referenced by the catalogue, the model pages, the comparison table, the drawer, the bag and the structured data.

*Case entry.* A slug, a sector, a narrative, a set of metrics, an optional quotation, an FAQ list and two relation links chosen by shared problem.

*Legal document.* A slug, an approved body, an effective date and a locale. The generator paginates and marks it up; it does not rewrite it.

## Deployment decisions

Output is committed to the repository, because the site is the artefact and the diff is the review. Deployment is a hosting release of that directory, with the header and redirect rules applied from configuration. Cache policy is deliberately conservative: HTML and assets revalidate, with asset invalidation handled by the content hash rather than by cache duration. Archived pages stay in the tree but are excluded from the sitemap and marked `noindex` by a header rule.

## Known limits

The pipeline has no incremental mode, so every run rewrites every page and diffs are large. HTML is produced by string concatenation with no validator in the pipeline, so malformed markup is caught in the browser. Order dependency is implicit: the sitemap is correct only because it runs after the generators. The alias map for translated slugs is maintained by hand. Structured data is generated from the same modules as the visible copy, which keeps them consistent, but nothing validates the result against a schema before deploy.
