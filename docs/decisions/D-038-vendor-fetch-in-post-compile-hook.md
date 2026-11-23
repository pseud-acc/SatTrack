# D-038 Fetch the self-hosted viewer files in the buildpack's `bin/post_compile` hook

**Status:** Proposed (owner to confirm) · **Date:** 2026-11-23 · **PRs:** roadmap 3.2 (`feature/cesium-viewer`)
**Component:** the Heroku build and CI's Heroku-identical build · **Tier:** full (changes what every build runs)

## Context
D-014 decided that the Heroku build and CI's Heroku-identical build download the npm tarballs pinned in
`vendor/cesium.lock`, verify them and extract the files the viewer uses. It didn't say how a build runs the script.
sattrackapp builds with the classic `heroku/python` buildpack only (pinned in `.github/scripts/heroku_build_check.sh`
at v362, `e5d67bc`), installing with uv.

Read in the buildpack source at that tag: `bin/compile` calls `hooks::run_hook "post_compile"` (`lib/hooks.sh`) after
the dependencies are installed, whatever the package manager, uv included. The hook runs `bin/post_compile` from the
app root (`cd "${BUILD_DIR}"`), with the app's Python first on `PATH` (`/app/.heroku/python/bin`), `CACHE_DIR`
exported, and config vars from the env dir loaded (`sub_env`). A non-zero exit fails the build with
`failure_reason hooks::post_compile`, so the live release stays. `.slugignore` is applied before the build, so files the
hook writes stay in the slug. `cache::save` touches only `CACHE_DIR/.heroku/...`, so a `CACHE_DIR/sattrack-vendor`
folder survives between builds.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **`bin/post_compile` runs `python vendor/fetch.py --cache "$CACHE_DIR/sattrack-vendor"`** | Supported by the pinned buildpack with uv; no Heroku config change; CI's build check runs it unchanged; a failure keeps the live release | A hook the buildpack could drop in a future major (watched by the build check's version notice) | WASM (3.11) and licence files (3.7) are lock-file changes only |
| A second buildpack (e.g. `heroku/nodejs` + `npm ci`) | Standard npm tooling, Dependabot | Heroku config change (buildpacks), a `package.json` and npm toolchain in the repo (rejected in D-014), CI script changes | – |
| Fetch at app start-up | No build change | A runtime dependency on the npm registry on every dyno boot; slower boots; a registry outage stops the app | – |
| Release phase (`Procfile` `release:`) | Runs once per release | Its files don't reach the slug or the dynos | – |
| Commit the files | Simplest | ~10 MB of history per upgrade (rejected in D-014) | – |

## Decision (proposed)
`bin/post_compile` runs `vendor/fetch.py`. The script uses only the standard library plus `brotli` (now a direct
dependency), contacts only `https://registry.npmjs.org`, verifies each tarball's sha512 against the lock, extracts
only the listed files into `static/vendor/<package>-<version>/` with pre-compressed Brotli and gzip copies, and writes
`static/vendor/manifest.json` with every file's SHA-256. Verified tarballs are cached in `CACHE_DIR/sattrack-vendor`
and re-verified on use. At start-up the app checks the manifest against the committed lock and every file against its
hash; if anything is missing or different, the viewer stays off (the Plotly views remain) and the log says why.

## Evidence
- Buildpack v362 source, as quoted above (`bin/compile` lines 91–92 and 296–297, `lib/hooks.sh`, `lib/cache.sh`).
- Local run, 23 Nov: 162 files, 13.2 MB on disk with the compressed copies; 6.8 MB added to the compressed slug
  (measured with `tar -czf`), within D-014's 15 MB. The CI build check now prints and enforces the figure.

## Consequences
- Every build downloads ~23.6 MB from the npm registry unless the cache already holds the tarballs.
- A registry outage fails a build (the live release stays). D-014's revisit trigger covers this.
- The build check fails if `static/vendor/manifest.json` is missing or the vendor folder adds more than 15 MB.

## Revisit when
- The buildpack stops supporting `bin/post_compile`, or sattrackapp moves to the Cloud Native Buildpacks stack.
- npm registry outages fail builds more than occasionally.

## Related
D-014, D-029, D-039; roadmap 3.2, 3.7, 3.11.
