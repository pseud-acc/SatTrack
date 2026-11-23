# D-039 Security headers ship with the viewer flag; Cesium needs a decision before the CSP is enforced

**Status:** Proposed (owner to confirm) · **Date:** 2026-11-23 · **PRs:** roadmap 3.2 (`feature/cesium-viewer`)
**Component:** every page's response headers (`app/core/viewer.py`) · **Tier:** full (HSTS is hard to undo)

## Context
Roadmap 3.2 asks for a Content-Security-Policy, report-only first (`'self'`, `worker-src 'self'`, no
`'wasm-unsafe-eval'` while the worker runs the JavaScript engine), and HSTS. The app sets no security headers today.
Its page shell (every page) already loads third parties: Google Analytics (`www.googletagmanager.com`), the Bootswatch
theme (`cdn.jsdelivr.net`), Font Awesome (`cdnjs.cloudflare.com`), Google Fonts (imported by `assets/bootstrap.css`)
and, on the 2D tab, USGS map tiles (`basemap.nationalmap.gov`), whose Plotly map starts workers from `blob:` URLs.

Measured with the viewer (headless Chromium, 23 Nov): Cesium 1.147.0 itself, in both its IIFE (`Cesium.js`) and ES
module (`index.js`) builds, compiles five small WebAssembly modules (bundled meshoptimizer) and runs
`(0,eval)("this")` (bundled Knockout) as it loads. Under an **enforced** policy without `'unsafe-eval'` the eval throws
and Cesium does not load at all (`Cesium.CesiumWidget` undefined). Under the report-only policy it loads and works;
the browser reports those six calls. D-014 and D-029 assumed only satellite.js's WASM engine would need anything beyond
`'self'`: that assumption is wrong.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **A. Headers only with the viewer flag on; report-only CSP listing the shell's existing third parties; HSTS `max-age=86400`** | Production unchanged until the flag flips; nothing can break (report-only); a short HSTS is reversible within a day | The policy allows today's third parties; Cesium's six reports are known and accepted in tests until B or C is chosen | 3.6 removes the Plotly entries; 3.11 adds `'wasm-unsafe-eval'` anyway |
| B. Before enforcing: patch Cesium's `(0,eval)("this")` to `globalThis` at vendoring (recorded in the lock and manifest) and add `'wasm-unsafe-eval'` | Keeps `'unsafe-eval'` out; one-line deterministic patch | A modified upstream file to re-check on every upgrade | WASM needed in 3.11 regardless |
| C. Before enforcing: allow `'unsafe-eval'` and `'wasm-unsafe-eval'` | No patch | Weakens the policy for every script on the page | – |
| D. Headers on every page now, flag or not | Reports start at once | Changes production in a flag-off release; HSTS commits the domain | – |
| E. Self-host Bootswatch, Font Awesome and the Roboto font; drop them from the policy | A shorter policy, fewer third parties | Outside 3.2's scope; page-shell change | Could ride with 3.6 |

## Decision (proposed)
A, now. With `SATTRACK_CESIUM_VIEWER` on, every response carries `Content-Security-Policy-Report-Only` (`default-src
'self'`; `script-src 'self' 'report-sample'` plus the hashes of every inline script (Dash's renderer and clientside
callbacks, the analytics snippet) and Google Tag Manager; `worker-src 'self'`; `object-src 'none'`; `base-uri`,
`form-action`, `frame-ancestors 'self'`; styles, fonts, images and connections allow the shell's listed third parties
and `'unsafe-inline'` styles) and `Strict-Transport-Security: max-age=86400` (no `includeSubDomains`, no `preload`).
No report endpoint yet: violations show in the browser console, and the browser tests fail on any violation other than
Cesium's six known ones and the Plotly map's `blob:` workers. Enforcement needs the owner to choose B (recommended) or
C, and to raise HSTS to a year once every host name is confirmed HTTPS-only.

## Evidence
`tests/e2e/test_viewer.py` (the `KNOWN_CSP` list) and the enforced-policy run described above. The Plotly views
report nothing except the 2D map's `blob:` workers.

## Consequences
- The header set is decided in one place (`app/core/viewer.py`); `tests/app/test_viewer.py` pins it.
- A new third party or inline script on any page fails the browser tests until the policy (and this record) is
  updated.

## Revisit when
- The viewer flag is turned on in production: confirm HSTS on `www.sattrackapp.com` and the apex, then raise max-age.
- Before switching to an enforced policy: choose B or C.
- Roadmap 3.6 removes Plotly: drop the tile host and the `blob:` exception.
- A Cesium upgrade: re-run the CSP checks; the Knockout eval may go away.

## Related
D-014, D-029, D-038; roadmap 3.2, 3.6, 3.11.
