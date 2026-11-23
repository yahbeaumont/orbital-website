# Decision records

Seven decisions that shaped the site. Each one is a real fork in the build, with the cost that came with the choice.

---

## ADR-1: No framework and no bundler

**Context.** The site is a catalogue with heavy visual design and little state: galleries, modals, a purchase drawer, a bag, a language switch. It has to be deployable as files, openable from the file system, and editable by one engineer without a toolchain.

**Decision.** Hand-written HTML, CSS and JavaScript. No component framework, no bundler, no transpiler, no CSS preprocessor. Scripts are plain files loaded with `<script src>`, split by concern: shell, interactions, bag, chat, tracking, cookies, latency demo.

**Alternatives considered.** A component framework with static export would have given components and a build step. A static site generator with a template language would have given layouts but kept the routing and content model in someone else's abstractions. Both add a dependency tree that must be upgraded, audited and re-learned, for a site whose interaction model is a handful of overlays.

**Consequences.** A page is HTML plus its stylesheet and scripts, with no hydration step. Nothing breaks on a dependency bump because there are no dependencies to bump. The cost is that composition is manual: a header change is a generator change, a shared component is a Python function, and there is no type system or lint pass catching a typo in a class name. The shared stylesheet keeps growing, and nothing in the pipeline reports which rules stopped being used.

---

## ADR-2: Python generators instead of a CMS

**Context.** 45 routes per language, with a shared header and footer, repeated section structures across four model pages, and content that changes in bursts. A CMS would put a database and an editor between the copy and the deploy. The copy is written by the engineer who ships it, and every change should be reviewable line by line.

**Decision.** Each page family has a Python script that reads a content dictionary and writes HTML. Sixteen generators, one shared shell module, one orchestrator that runs them in order. Content lives in dictionaries next to the generator that consumes it. Cross-page data lives in dedicated modules with a single source.

**Alternatives considered.** A hosted CMS gives non-engineers an editor, at the cost of a content API, a preview environment and a rendering layer. A markdown-based generator gives simpler content files but weaker structure for pages that are 80 percent layout. Hand-editing HTML was the starting point and failed on drift: the same navigation list was copied into every page.

**Consequences.** Structural change happens once, in the generator, and the diff shows exactly which pages changed. Content review is a code review. The cost is that the content model is Python: writers need the repository, and the dictionaries have no schema, so a missing key is a runtime error during the build. The generators also hold markup as strings, which means indentation, quoting and escaping are manual disciplines rather than enforced ones.

---

## ADR-3: A fixed exchange rate for a static site

**Context.** Portuguese pages quote in the local currency, English pages quote in dollars. The values are used in case narratives, cost comparisons and payback calculations. A static page cannot call an exchange rate API at request time, and a number that changes between two visits would be indefensible in a case study that is meant to be read once and cited.

**Decision.** One rate, defined as a constant in a single module, applied at build time. Values are stored once as integers in the operating currency and converted during generation. Rounding is banded, with the step chosen on the converted value so results read as round figures. Payback is computed from the converted price divided by the monthly saving. Formatting follows the locale: dot thousands separator in Portuguese, comma in English.

**Alternatives considered.** A live rate would be accurate and unstable. A hard-coded dollar figure per case would be stable and unmaintainable, because the source value lives in the narrative. Quoting both currencies side by side would be honest but doubles the reading load.

**Consequences.** One edit changes every converted figure consistently, and no monetary value is typed by hand. The rate is a liability that decays silently; it is documented with a review threshold rather than a schedule. Two languages of the same case can disagree on a derived number, which is arithmetically correct and looks like an inconsistency to a reader who switches language.

---

## ADR-4: Structured data generated from the same source as the copy

**Context.** Search engines and answer engines read the pages, and different page types deserve different markup: `Product` and `Offer` for model pages, `Article`, `FAQPage` and `BreadcrumbList` for cases, `CollectionPage` with `ItemList` for indexes. Hand-writing JSON-LD per page guarantees that it drifts from the visible text, and a price mismatch between markup and page is a manual action risk.

**Decision.** Structured data is produced by Python functions that take the same arguments as the visible markup, including the price module and the case data. Product offers are built from the price module, so the JSON-LD price and the printed price cannot disagree. FAQ markup is generated from the same list that renders the visible questions. Social cards and canonical URLs are added by a post step so no page family can forget them.

**Alternatives considered.** A single generic `Organization` block on every page is easy and useless. Hand-written JSON-LD per page is expressive and unverifiable at this page count. A schema validation step in the pipeline was considered and is not implemented.

**Consequences.** Consistency is structural rather than reviewed: the markup cannot state a price the page does not show. The cost is coupling, because a change to the price module's shape touches the structured data builder, and the JSON-LD is only as correct as the Python that assembles it. Nothing validates the output against schema.org before deploy, so a malformed block ships and is discovered in a search console report.

---

## ADR-5: A CSS chassis as the fallback for missing renders

**Context.** Product photography and renders arrive late and change often. The hero depends on a transparent PNG that the parallax script moves. A missing file would leave a hole in the most important section of the page, and the design cannot wait for assets.

**Decision.** Every hero keeps its `<img>` as the parallax target, with the id on the image itself. An inline error handler reveals a CSS-drawn chassis positioned where the image would be. A small observer mirrors the image's transform onto the chassis, so the motion survives the substitution without touching the interaction script. Explicit `width` and `height` reserve the space in both cases.

**Alternatives considered.** A placeholder image is a broken-looking grey box. Blocking the build on missing assets stops content work for a design dependency. Removing the parallax when the image is absent loses the motion that the section was designed around.

**Consequences.** The page is presentable before the assets exist, and the parallax has one code path. The cost is a second representation of the product in CSS that must be maintained alongside the renders, and a markup constraint that outlives the reason for it: the id cannot move to a wrapper, and the chassis must remain the image's previous sibling. The observer also runs on every style mutation of the image.

---

## ADR-6: The sitemap is generated from published files

**Context.** The sitemap has to list exactly the indexable URLs, with `hreflang` alternates. A hand-maintained list is wrong the moment a page is added, and a wrong `hreflang` pair is worse than none, because it tells search engines that two pages are translations of each other when they are not.

**Decision.** A post step walks the language trees for `index.html` files, skips anything whose robots meta says `noindex`, skips the archived folder, and pairs the remaining pages by identity key, with an explicit alias map for the slugs that are translated. `x-default` points at the English URL. The modification date comes from the page's structured data when present, otherwise from git: today if the working copy differs from the last commit, the commit date if it does not.

**Alternatives considered.** A route manifest maintained by hand is simple and stale. Deriving the sitemap from the generators' registries is accurate for generated pages but blind to anything else in the tree, including pages added by other means.

**Consequences.** The sitemap describes what is deployed, and a `noindex` page removes itself from the index without a second edit. The cost is order dependency: the step is only correct because it runs after every generator, and a page generated but not registered in the pipeline is silently missing from the sitemap while still being reachable. The alias map is a manual exception that must be updated when a new translated slug appears.

---

## ADR-7: A region bar backed by session storage, not geolocation

**Context.** The site has two language trees and two currencies, and visitors arrive from both audiences. An automatic redirect based on IP address guesses wrong for travellers, for VPN users and for anyone reading a link shared from the other language.

**Decision.** A region bar appears once per session on first load, offering eight regions mapped to two destinations. The initial option follows the page's language. Changing the select does not navigate; the switch happens on an explicit continue button, which preserves query string and anchor so a checkout link keeps its product selection. The dismissal is stored in session storage, not a cookie, so no consent is needed for it.

**Alternatives considered.** Geo-IP redirect is invisible when right and infuriating when wrong. A permanent language switch in the header only is less discoverable for a first-time visitor comparing prices. A cookie would have required consent handling for a preference that does not need to persist beyond the session.

**Consequences.** The visitor chooses, the choice is reversible, and nothing is stored across sessions. The cost is one extra decision before the content on a first visit, and a keyboard interaction that needed a separate continue button to avoid navigating while tabbing through options. The region list is a fixed mapping, so a new market is a content change, not a configuration change.
