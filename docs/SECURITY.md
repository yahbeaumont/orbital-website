# Security and privacy

## What is being protected

**The published surface.** The HTML, CSS, JavaScript and images served from the CDN. The threat here is not data loss, it is a page that runs code it should not, or that serves something the build intended to keep private.

**The repository boundary.** The site's hosting configuration publishes a directory. Anything inside that directory and not explicitly excluded is public, which makes the publish ignore list a security control: tooling, documentation, function sources, environment files, archives and repository metadata must not be reachable.

**Commercial content before publication.** Prices, model specifications, case narratives and legal text are approved in one place and generated into pages. A generator that reads the wrong module, or a page that bypasses the single source, publishes an unapproved number.

**The commerce handoff.** The payment session, the order status lookup and the webhook. The site never sees card data, but it does handle the identifier of a session and the e-mail address attached to an order.

**Visitor privacy.** Analytics consent state, the region preference, and the bag contents, which live in local storage and never leave the browser.

## Trust boundaries

1. **Build machine to static output.** The generators are trusted. Their output is not verified by any automated check before deploy, so the boundary is the review of the generated diff.
2. **Browser to hosting.** The browser is untrusted. Everything it receives is public, cacheable and inspectable.
3. **Browser to functions.** Requests arrive from anywhere. Origin, method, content type, body size and rate are checked before any work happens.
4. **Payment provider to functions.** The webhook is an unauthenticated endpoint until the signature is verified over the raw body. Before that check, the request is treated as hostile.
5. **Third-party scripts to the page.** The tag manager is the only third-party script allowed to execute, and it is constrained by the content security policy and by consent state.

## Threats considered

**Repository metadata exposure.** The hosting configuration published the repository root. Dot directories, tooling, documentation and function sources were excluded by a pattern list that did not cover everything. The list is now explicit and treats every non-publishable path as a named exclusion, and archived routes are served with a `noindex` header rather than removed, so old URLs cannot be used to reach retired content in the index.

**Injection through generated markup.** Copy is authored, not user supplied, so the realistic vector is a value that reaches HTML unescaped: a product name, a case metric, a legal paragraph with an ampersand. Generators are expected to escape interpolated text and to keep markup in template literals rather than in data. This is a convention, not an enforced rule, and it is the weakest point of a string-based pipeline.

**Clickjacking and framing.** Pages and functions send `X-Frame-Options: DENY` and `frame-ancestors 'none'`.

**Cross-site scripting through a compromised dependency.** There is no package tree to compromise: no framework, no library fetched from a registry or a public CDN. The one third-party script is the tag manager, which the content security policy limits to the analytics endpoints it actually needs, while blocking `object`, `base` and unknown frames.

**Payment session abuse.** The session function accepts only POST from an allowlisted origin, requires JSON, rejects bodies above a small size cap, validates the catalogue identifier and quantity, and rate limits per instance. Prices are resolved server side, so a tampered client cannot change an amount.

**Webhook forgery.** The signature is verified against the raw body before any side effect. An unsigned request produces no e-mail and no state change.

**Order status enumeration.** The status function accepts GET only, validates the identifier, rate limits per instance with `Retry-After`, and returns a masked e-mail address so a shared confirmation link does not disclose the buyer's full address.

**Analytics over-collection.** Consent defaults to denied, set before the tag manager loads, and is updated only by an explicit choice stored in local storage. The region bar uses session storage, so it needs no consent and leaves nothing behind after the tab closes.

## Controls implemented

| Control | Where |
|---|---|
| Content security policy with an explicit source list | Hosting header rule |
| `X-Frame-Options`, `frame-ancestors`, `Permissions-Policy`, `Referrer-Policy`, `nosniff`, HSTS | Hosting header rules |
| Cache policy that revalidates HTML and assets, with content-hashed asset URLs | Hosting plus a build step |
| Publish ignore list covering tooling, docs, functions, env files, archives and dot directories | Hosting configuration |
| `noindex` on archived routes | Header rule scoped to the archive path |
| No secrets in any served file | Build convention; secrets live in the function environment |
| Server-side price resolution | Session function catalogue |
| Signature verification over the raw body | Webhook function |
| Per-instance rate limit, body size cap, content type check, origin allowlist | Session and status functions |
| Masked e-mail on the status page, HTML escaping before render | Status function and confirmation page |
| Consent denied by default, updated on choice | Inline bootstrap generated at build time |
| `security.txt` with a contact and a validity window | `/.well-known/` |

The content security policy allows inline scripts and styles. That is a deliberate, documented compromise: the site is static and carries a small number of inline blocks per page, including the analytics bootstrap, and replacing them with hashes would require regenerating hashes on every build and would break the tag manager snippet. The policy still blocks every external origin that is not on the list, which is the part that matters for a compromise of a third-party script.

## What is not guaranteed

The rate limit is per function instance and does not stop a distributed source; there is no WAF or edge limiter in front of the functions. There is no uptime check and no error alerting. The pipeline does not validate HTML, links or structured data before deploy, so a broken page is found by reading it. Escaping in generated markup depends on generator discipline. Case figures supplied for the case pages were delivered as projections, and the site presents them as published content; this repository does not repeat them and does not describe any of them as a measured result. Nothing here asserts legal compliance, certification or a security guarantee for the brand's operations.

## Reporting a problem

Security contact details and the disclosure window are published in `/.well-known/security.txt` on the live site. Reports about this repository can also go through the contact form linked from the site's support page. Please include the URL, the observed behaviour and the steps to reproduce, and allow time for a fix before publishing details.
