# D-014 Self-host CesiumJS and satellite.js, fetched and hash-checked at build

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #SPIKE (spike 3.1)
**Component:** front-end dependencies; the Heroku and CI builds · **Tier:** full

## Context
The roadmap planned to load CesiumJS from a CDN. Subresource Integrity covers only the script tag's file; Cesium then
loads workers, assets and imagery from its base URL, unchecked. The app serves Plotly itself today and has no CSP.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Fetch npm tarballs at build, verify pinned hashes, serve a subset from `static/vendor/<version>/`** | No third-party server at runtime; every file verified; CSP stays `'self'` | ~10 MB larger slug; no Dependabot; build depends on the npm registry | Workers and WASM stay same-origin (D-015, D-029) |
| jsDelivr with SRI | Small slug | Workers and assets unverified; runtime CDN dependency; CSP must allow the CDN | – |
| Commit the files | Simple | ~10 MB of git history per upgrade | – |
| npm bundle | Tree-shaking | A new toolchain in the repo | – |

## Decision
`vendor/cesium.lock` pins Cesium and satellite.js versions and their npm tarball hashes. A script run by the Heroku
build and CI's Heroku-identical build downloads each tarball, verifies the hash, extracts the files the viewer uses
(about 10.2 MB of Cesium's 22.8 MB build) and writes a manifest of per-file hashes. Served from a versioned path with
long-lived caching. A mismatch fails the build and the live release stays. No Cesium ion account or token.

## Evidence
Spike, 22 Nov: Cesium 1.147.0's build is 22.8 MB; the viewer needs ~10.2 MB in 308 files. Cesium.js is 1.54 MB with
Brotli.

## Consequences
CSP: `script-src 'self'`, `worker-src 'self'`, plus `'wasm-unsafe-eval'` once WASM is used (D-029). The "slug not
materially increased" check becomes "within 15 MB". A weekly workflow (proposed in its PR) opens an issue for new
releases. CI fails on any off-site request and on CSP violations. Licence and NOTICE files ship with the files (3.7).

## Revisit when
- The npm registry's outages break builds often enough to matter.
- Slug size nears Heroku's limit.
- Traffic justifies a CDN in front of the app (see D-012's revisit path).

## Related
D-012, D-013, D-029; roadmap 3.2, 3.7.
