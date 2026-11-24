# D-041 Security headers ship with the viewer flag; Cesium needs a decision before the CSP is enforced

**Status:** Accepted (owner, 2026-11-24): A now, B for Cesium (after a prototype), enforced at roadmap 3.6 · **Date:** 2026-11-23 · **PRs:** roadmap 3.2 (`feature/cesium-viewer`)
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

## Decision
A and B now; the policy is enforced at roadmap 3.6. With `SATTRACK_CESIUM_VIEWER` on, every response carries `Content-Security-Policy-Report-Only` (`default-src
'self'`; `script-src 'self' 'report-sample'` plus the hashes of every inline script (Dash's renderer and clientside
callbacks, the analytics snippet) and Google Tag Manager; `worker-src 'self'`; `object-src 'none'`; `base-uri`,
`form-action`, `frame-ancestors 'self'`; styles, fonts, images and connections allow the shell's listed third parties
and `'unsafe-inline'` styles) and `Strict-Transport-Security: max-age=86400` (no `includeSubDomains`, no `preload`).

B (owner's choice, 2026-11-24, after the prototype below): `vendor/cesium.lock` carries a `[[package.patch]]` that
replaces Cesium's single `(0,eval)("this")` with `globalThis` in `index.js`; `vendor/fetch.py` applies it after the
hash check, fails the build unless the text occurs exactly once, and records the patch with the file's hash before and
after in the manifest. `script-src` gains `'wasm-unsafe-eval'` and never `'unsafe-eval'`.

Enforcement waits for roadmap 3.6 (owner's choice): an enforced policy breaks the Plotly 2D map, whose workers start
from `blob:` URLs. 3.6 removes Plotly, drops the tile host and the `blob:` exception, and switches the header to
`Content-Security-Policy`. No report endpoint yet: violations show in the browser console, and the browser tests fail
on any violation other than the Plotly map's `blob:` workers. HSTS is raised to a year once every host name is
confirmed HTTPS-only.

## Evidence
- `tests/e2e/test_viewer.py` (the `KNOWN_CSP` list) and the enforced-policy run described above. The Plotly views
  report nothing except the 2D map's `blob:` workers.
- Prototype, 24 Nov 2026 (local, headless Chromium, the app's policy rewritten to an enforced
  `Content-Security-Policy`):
  - control, Cesium unpatched, `script-src` + `'wasm-unsafe-eval'`: Cesium fails to load (`EvalError`, one `eval`
    violation in `index.js`);
  - **B**, patched `index.js`, `script-src` + `'wasm-unsafe-eval'`: the globe loads and runs (339 objects, no Cesium
    violation); the 3D, 2D and list tabs render;
  - C, unpatched, `script-src` + `'unsafe-eval' 'wasm-unsafe-eval'`: also works.
  - In all three, the 2D map raises "Mapbox error" because its `blob:` workers are blocked: hence enforcement at 3.6.
- With the patch in the lock, the full browser suite passes with no Cesium CSP report; parity with Python sgp4 is
  unchanged (7.6 m at most).

## Consequences
- The header set is decided in one place (`app/core/viewer.py`); `tests/app/test_viewer.py` pins it.
- A new third party or inline script on any page fails the browser tests until the policy (and this record) is
  updated.

## Revisit when
- The viewer flag is turned on in production: confirm HSTS on `www.sattrackapp.com` and the apex, then raise max-age.
- Roadmap 3.6 removes Plotly: drop the tile host and the `blob:` exception, and enforce the policy.
- A Cesium upgrade: the build fails if the patched text moved or went; review the patch, and drop it if upstream no
  longer uses `eval`.
- 3.7 (licence): list the patched `index.js` as a modification in the third-party notices (Apache-2.0 section 4).

## Related
D-014, D-029, D-038; roadmap 3.2, 3.6, 3.11.
