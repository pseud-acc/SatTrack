# SatTrack improvement plan

> **For Claude Code.** This is the working improvement plan for SatTrack (`pseud-acc/SatTrack`). Work through phases in order unless told otherwise. Each phase is sized for **~5 hours/week** of the owner's time; treat each numbered task as roughly one PR. Read the "Working rules" before starting any task.

---

> **Revised 2026-11-18** with the roadmap review of 17 Nov 2026: Phase 0 updated (0.2 done, 0.3 and 0.4 added), corrections on six-digit catalogue numbers, the Cesium spike moved straight after 2.1, a +25% buffer on Phases 3 and 6, new tasks 5.4 and 7.2, and Phase 7 reordered.

## Where we are (baseline, v2.1.0 + 17 Nov 2026)

- **Pipeline** (`pipeline/`): Space-Track GP + GCAT ingestion → dbt on DuckDB → app CSVs via `pipeline/scripts/export_app_csvs.py` and `transform/analyses/app_export/app__satcat_tle.sql`. Runs **once daily** (EventBridge, 03:17 UTC, `infra/aws/sattrack-scheduler.yaml`).
- **Marts**: rich, tested descriptive model (`fct__satellite_master`, org/launch/geography dims and bridges, uncertainty flags, source lineage). Tracking mart `fct__gp_elements` holds mean elements + TLE lines.
- **App** (`app/`): Dash + Plotly. Positions computed **server-side** with `sgp4` from TLE lines (`app/helper/helper__satellite_position.py::compute_satloc`), refreshed by `dcc.Interval` (3D every 20 s, 2D every 3 s). Export scope is **payloads only**. Hosted on Heroku.
- **Delivery**: PR checks (Heroku-identical build, pipeline tests + dbt checks) required on `main`; deploy to Heroku on merge when app files change; the app reads the private S3 bucket's `app/` folder at start-up.
- **3D traffic**: responses compressed and position-only patches on refresh (28.7 MB → 0.31 MB per 3D refresh, PR #37). A stopgap that Phase 3 retires.
- **Legacy pipeline** (`src/`, `dat/`, root `run_pipeline.py`): removed in PR #30.

## Target state

1. Positions from **OMM** fields (6-digit catalogue numbers safe), with **SupGP** preferred where available, refreshed several times a day.
2. **CesiumJS** globe with smooth, client-side real-time propagation, one viewer for 3D and 2D, and payloads + rocket bodies + debris.
3. A deep satellite detail panel: physical detail (bus, shape, dimensions, power, payload, equipment) alongside SatTrack's multi-org roles, uncertainty and lineage.
4. **Plain-English query** that compiles to a validated filter spec, shown back as editable filters, with an eval suite in CI.

## Capability plan

Where SatTrack is today in each area, what it should do, and the work to get there. Hours are rough owner-time estimates at the current pace.

| Area | SatTrack today | Target | Work | Phase | Est. h |
|---|---|---|---|---|---|
| Multi-org ownership (owners, manufacturers, launch agencies, with roles) | Bridge tables, role + order, split rules | All co-owners and roles visible per satellite | Show them in the detail panel | 5.2 | incl. |
| Data quality & lineage | Uncertainty flags, `_source` columns, date precision, link method | Visible to users | Data-quality section in the panel; caveats in plain-English answers | 5.2, 6.3 | incl. |
| Launch context | Vehicle family/capacity/thrust, site coords, nearest city, org/site dates | Visible per satellite | Site map pin, launch section in the panel | 5.2 | incl. |
| Documented, tested data model | dbt docs site, model-health tests, contracts | Keep | Reuse the docs as context for plain-English query | 6 | — |
| Core identity & orbit summary | Names, IDs, apogee/perigee, inclination, period, RCS, orbit class | Keep | — | — | — |
| Mission, purpose, status | GCAT-based, tested status model | Status with its source | Show the status source and "stopped transmitting" vs "stopped operating" | 5.2 | incl. |
| Element source / accuracy | Space-Track GP only | Most accurate set per object | Ingest SupGP, precedence rule, show the source | 4.2–4.4 | 8 |
| Data freshness | Daily run | Several runs a day | Multi-run schedule, GP-only mode, hot reload | 4.1 | 4 |
| Six-digit catalogue readiness | TLE-line propagation; works today via Alpha-5 TLEs (1,492 GP objects above 99,999 on 16 Nov, all 1,040 such app payloads parse) but Alpha-5 stops at 339,999 and SupGP is OMM-only | Propagation from OMM | Switch to OMM | 1 | 8 |
| Object coverage | Payloads only in the app (19,721 of 32,672 GP objects on 16 Nov) | Payloads, rocket bodies and debris | Widen the export, UI toggles | 2.1, 3.3 | 2 |
| 3D/2D visualisation | Plotly, server-side propagation every 3–20 s | Smooth WebGL globe, propagated in the browser | Cesium viewer + Web Worker propagation | 3 | 30 |
| Physical spacecraft detail | Mass, dry mass, span | Bus, shape, length, diameter, power, payload, equipment, motor | Add the remaining GCAT fields | 5.1 | 5 |
| Rollup views (by bus/owner/constellation) | Filters only | Views per group | Rollup views driven by the filter spec | 5.3 | 3 |
| Natural-language query | None | Plain-English questions, answered on the globe | Spec-based NLQ with editable interpretation, uncertainty caveats, eval suite | 6 | 20 |
| Element history / trends | Latest set only | History per object | Append-only GP snapshots, decay/manoeuvre plots | 7 | 8 |
| Pass predictions & visibility | None | Passes for an observer's location | Client-side passes, McCants magnitude | 7 | 10 |
| Radio frequencies | None | Frequencies per satellite | SatNOGS DB ingest, panel section | 7 | 4 |
| Re-entry predictions | Decay filtered out | Objects re-entering soon | Re-entry layer | 7 | 4 |
| Conjunctions | None | Close approaches | Visualise CelesTrak SOCRATES pairs | 7 | 8 |

**Summary:** SatTrack's strengths are modelling depth and data trust. The plan adds live accuracy and freshness (Phases 1, 4), a modern globe (Phase 3), deeper per-object detail (Phase 5) and plain-English query (Phase 6), then observer features from the Phase 7 backlog.

---

## Timeline at ~5 h/week

| Phase | Theme | Est. hours | Est. weeks |
|---|---|---|---|
| 0 | Housekeeping & guardrails | 12 (done) | 2–3 |
| 1 | OMM propagation | 8 (done) | 2 |
| 2 | Client data contract + filter spec | 11.5 (incl. 2.4, the one task left) | 2–3 |
| 3 | Cesium migration | 85.5 (spike 3.1: 3, done; core 63.5 incl. 3.3a/3.3b, 3.7, 3.12, 3.13; extensions 19 incl. 3.14; +15% buffer → ~98) | 18–20 |
| 4 | Freshness & SupGP | 12 | 3 |
| 5 | Detail enrichment | 14 (incl. 5.4, 5.5 and the optional 5.3) | 3 |
| 6 | Natural-language query | 20 (+25% buffer → 25) | 4–5 |
| 7 | Backlog (pick as wanted) | — | — |

Each phase's hours are the sum of its task estimates, done tasks included; the plan adds the stated buffers (Phase 3 +15%, Phase 6 +25%). To the end of Phase 6 that is **163 h of estimates, ~181 h with the buffers: roughly 36 weeks (~8 months) at 5 h a week**, of which ~56 h is done (Phases 0 and 1, 2.1 to 2.3, 3.1, 3.2, 3.8 and 3.12), leaving ~121 h with the buffers (~24 weeks). On 26 Nov 2026 3.3 was split into 3.3a and 3.3b (~11 h against ~6 h, D-048) and the constellation and system filters were added as 3.14 (~3 h, D-047). It includes the tasks added by the review, the Phase 3 scope set after the Cesium spike (D-028; 93 h as originally written) and the design and "Colour by" tasks added on 24 Nov 2026 (3.12, 3.13; D-044, D-045). Phases 4 and 5 are independent of 3 and can be swapped in if Cesium work stalls. On 28 Nov 2026 3.4 grew to ~13 h (detail dataset, citation, share link, GEO longitude), 5.5 was added (~2 h), and 5.4, 5.5, 5.3 and 7.5 were moved straight after 3.4 for the analyst and journalist audience; 7.4 rose to ~6–8 h, behind a coverage check.

---

## Working rules (apply to every task)

- **Branch/PR naming** per `CHANGELOG.md`: `feature/`, `fix/`, `refactor/`, `chore/`, `docs/`, `test/`, `major/`. Add an entry under `[Unreleased]` in `CHANGELOG.md` for every user-visible change.
- **Dependencies** via `uv` (app: root `pyproject.toml`; pipeline: `pipeline/pyproject.toml`). Keep `uv.lock` committed.
- **dbt**: every new/changed column gets a schema YAML entry and a doc block; keep `model_health` tests and contracts passing (`dbt build`). Regenerate contracts with `pipeline/scripts/codegen_contracts.py` if it applies.
- **Space-Track quota**: GP at most once per hour. Never add loops or retries that could exceed this. No credentials in code, logs or the public Actions log.
- **Infra** (`infra/`, `.github/workflows/`): propose changes in the PR description; do not deploy or alter AWS resources without the owner's explicit go-ahead.
- **Tests**: add/extend tests with each change; parity tests for anything that changes satellite positions.
- **Keep PRs small** (one task each) so they fit a 5-hour week, including review.
- When a task's assumption turns out wrong (e.g. a library lacks a feature), stop and write up options in the PR rather than working around it silently.
- **Accessibility** (owner, 28 Nov 2026: essential, for every task): everything works from the keyboard with a visible focus; controls have names a screen reader can read; text meets WCAG AA contrast and colour is never the only signal (colour-blind-safe palettes); tap targets are at least 24 px (WCAG 2.2); motion respects `prefers-reduced-motion`. Check these in the PR for anything a visitor sees.
- **UX choices** are discussed with the owner and tried on a laptop and a phone before they're decided (owner, 28 Nov 2026). Keep the app sleek and uncluttered: one panel open at a time, nothing shown that wasn't asked for, depth inside sections that open.

---

## Phase 0 — Housekeeping & guardrails (~12 h)

**Goal:** a clean base for agent-driven work.

0.1 `chore/claude-md` — Add `CLAUDE.md` at repo root summarising architecture, commands (`uv sync`, `dbt build`, run app locally, run pipeline locally with a dev profile), and the Working rules above. Commit this roadmap as `docs/ROADMAP.md`. (~2 h)

0.2 `chore/retire-legacy-pipeline` — **Done** in PR #30 (16 Nov 2026): `src/`, `dat/` and root `run_pipeline.py` deleted; the app reads S3 or a local folder (`SATTRACK_APP_DATA_DIR`); CI uses `tests/app_data`. (~2 h)

0.3 `test/app-ci` — Add an app pytest job to the PR and merge checks, running app tests against `tests/app_data`. Without it, 1.4 (parity) and 2.3 (filter spec) would never run in CI. (~1.5 h)

0.4 `chore/cleanup` — Open clean-up items: Dependabot alerts (app lockfile), archive the two expected IAM Access Analyzer findings, delete stale branches, laptop clean-up (Task Scheduler entry, `SPACETRACK_*` in the local env file, leftover untracked files). (~1 h)

0.5 `test/app-e2e` — A small browser (E2E) test set: Playwright + headless Chromium on the sample, four journeys (home → tracker, 3D draws the selected satellites, one satellite's 2D track, list view), failing on any JS/console error. Checks by counts and rows so they carry over to Cesium; Phase 3 extends them. Runs before each deploy. (~1 h)

0.6 `major/dash-4` — Planned major upgrade: Dash 2.18 → 4.5 (the current release; Dash 3 is skipped), which allows the patched Flask and Werkzeug and clears the last 5 Dependabot alerts (the other 123 were cleared in #45). Upgrade only; new Dash features are separate tasks. Known changes: `app.run_server` becomes `app.run` (`run_app.py`, `run_app_dev.py`); dash-bootstrap-components 1.x → the 2.x release that supports Dash 4 (confirm first); Dash 4's redesigned core components (Dropdown, RangeSlider, Checklist) change how the sidebar looks, so compare screenshots before and after; `dash_table.DataTable` (list view) is deprecated but still works, so it stays; review deprecated component props. The app unit, integration and browser tests are the safety net; check the 3D payload size again (PR #37). About 4.5 h. Do it before Phase 3, which builds the Cesium viewer into the Dash shell.

**Done when:** `CLAUDE.md` exists, legacy code is removed, app unit/integration and E2E tests run in CI, clean-up items closed or listed, the app is on Dash 4.5 with no open Dependabot alerts, CI green.

---

## Phase 1 — OMM propagation (~8 h)

**Why first:** a prerequisite, not an emergency. Space-Track already gives objects above 99,999 TLE lines in Alpha-5 format and the app reads them correctly, but Alpha-5 ends at 339,999, SupGP data for new objects is OMM-only (Phase 4), and the browser propagator reads OMM directly (Phase 3).

1.1 `feature/omm-fields-in-marts` — **Done** in PR #50 (21 Nov 2026). Carry `mean_motion_dot`, `mean_motion_ddot`, `rev_at_epoch`, `element_set_no`, `ephemeris_type`, `classification_type` from `stg__spacetrack__gp` through `int__spacetrack__satellite_catalogue` into `fct__gp_elements` (tracking). Not into `fct__satellite_master`: since #42 the app export takes elements from the tracking mart, which updates every run, and only descriptive fields from the master, which is held when GCAT enrichment fails. Schema YAML + doc blocks (reused from staging). Keep TLE columns. A warn-level check flags any `ephemeris_type` other than 0 (SGP4). (~2 h)

1.2 `feature/omm-app-export` — **Done** in PR #54 (21 Nov 2026). In `app__satcat_tle.sql`: add OMM columns; take `mean_motion`/`eccentricity` from columns instead of `substr(tle_line_2, …)`; replace `tle_line_1/2 is not null` filter with a check on the element columns; format epoch explicitly as `%Y-%m-%dT%H:%M:%S.%f`. Add new columns to `APP_COLUMNS["satcat_tle.csv"]` in `export_app_csvs.py`. Update the CI sample `tests/app_data` to the new columns. (~2 h)

1.3 `refactor/omm-propagation` — **Done** in PR #56 (22 Nov 2026), with WGS 84 geodetic latitude/altitude and a per-element-set propagator cache (D-004 to D-006). In `compute_satloc`, build `Satrec` via `sgp4.omm.initialize(Satrec(), fields)` (available in pinned `sgp4>=2.21`). Update callers in `helper__app_data.py` (lines ~111, ~140). Also build the `Satrec` once outside the time loop in the orbit-path branch. Keep a TLE fallback for one release. Building `Satrec` once per satellite also speeds up the 2D/3D callbacks until Cesium replaces them. (~2.5 h)

1.4 `test/omm-parity` — **Done** in PR #56 (22 Nov 2026): its OMM-vs-TLE parity test covers every sample object incl. Alpha-5 at −24 h, 0 and +24 h; checked against NASA's ISS ephemeris and wheretheiss.at. Test propagating a sample of objects via TLE and via OMM over ±24 h; assert position difference under a small tolerance (expect metres, OMM carries more precision). Include objects above 99,999 (Alpha-5) in the sample. Runs in CI via 0.3. (~1.5 h)

**Done when:** app runs entirely off OMM fields, parity test passes, no object is dropped for lacking TLE lines.

---

## Phase 2 — Client data contract + filter spec (~11.5 h)

**Goal:** define what the browser receives and how selections are expressed, so Cesium (Phase 3) and NL query (Phase 6) plug into the same contracts.

2.1 `feature/app-data-json` — The `objects` dataset for the browser, built to the data contracts decided on 22 Nov 2026 (`docs/DECISIONS.md` D-009 to D-012, `docs/app-data-contract.md`): one record per tracked object with the warehouse's field names, the full OMM element set and the filter fields; every object type (payloads, rocket bodies, debris, and `UNKNOWN` hidden by default in the UI); a shared envelope (dataset, schema version, count, run, attribution, caution); every record validated against `app/contracts/objects.schema.json` before publishing; pre-compressed (Brotli and gzip) and listed in `app/current.json` with the CSVs. The app serves it at `/data/objects.json` with an ETag, on threaded gunicorn workers so slow downloads can't block callbacks. The shape of the second core dataset, `object_detail`, is documented now; its file ships with the detail panel (3.4). (~3.5 h)

2.2 `feature/filter-spec` — Define a **filter spec** as a JSON Schema (`app/contracts/filter_spec.schema.json`): a list of `{field, op, value}` clauses with an allowlist of fields and ops, generated from dbt schema YAML + `accepted_values` where possible (script in `pipeline/scripts/`). Write a Python function that applies a spec to the app dataframe and refactor the existing sidebar callbacks to build a spec and call it. Behaviour must be unchanged. This is also the NLQ safety boundary in Phase 6, so keep the allowlist strict. (~3 h)

2.3 `test/filter-spec` — Unit tests: each existing sidebar filter → spec → same result set as before. Runs in CI via 0.3. (~1.5 h)

2.4 `feature/list-view-ag-grid` — Replace the list view's `dash_table.DataTable` (deprecated in Dash 3.3, to be removed in a future major) with AG Grid (`dash[ag-grid]`): virtual scrolling instead of 20-row pages, column filters, built-in CSV export. Keep the export's columns, order, hidden columns and the ±180° longitudes (#41); restyle for the dark theme; update `callback_table.py`, its integration tests and the E2E list journey (which reads table rows). About 3.5 h; independent of 2.1–2.3.

**Order:** run the Cesium spike (3.1) straight after 2.1; it needs only the JSON export, not the filter spec, so the biggest risk is tested early.

**Done when:** sidebar filters run through the spec; JSON export produced by the pipeline; contracts documented.

---

## Phase 3 — Cesium migration (~85.5 h: spike ~3 h (done), core ~63.5 h, extensions ~19 h; plan for ~98 h)

**Goal:** replace Plotly 3D/2D with a CesiumJS viewer, propagating in the browser.

**Architecture (decided after the 3.1 spike; `docs/cesium-architecture.md`, decisions D-013 to D-029):**
- Keep **Dash** as the shell (sidebar, table, routing, detail panel).
- A plain JS module in **`static/viewer/`** (never `assets/`, which Dash loads on every page), loaded only on the tracker page, mounts Cesium in an empty `html.Div(id="globe")` that no callback writes to. Filters go in through a `dcc.Store` and a clientside callback; the selected object comes back through `dash_clientside.set_props` (D-013).
- **Self-host** CesiumJS and satellite.js: `vendor/cesium.lock` pins versions and npm tarball hashes; the Heroku and CI builds download, verify and extract the files used (~10.2 MB) into a versioned `static/vendor/` path. No CDN at runtime, **no Cesium ion account or token**. CSP `'self'` plus `worker-src 'self'` (D-014).
- Propagate with **satellite.js** from the OMM fields of `/data/objects.json`, in a **Web Worker** on an adaptive time grid (0.25–10 s of simulation time); the main thread interpolates between samples (D-015). JavaScript engine now, WASM when shadow dimming lands (D-029). Render with one `PointPrimitiveCollection`.
- One viewer for 3D, 2D and Columbus: it replaces both Plotly tabs (D-021). Natural Earth II imagery, self-hosted (D-022, provisional).
- **Colour by object type** by default, with a "Colour by" menu (orbit class, status, owner, constellation) and a legend (D-017; the menu is its own task, 3.13, D-045). Payloads by default; rocket bodies and debris one switch away ("space junk mode") (D-016).
- Performance budget (D-027): laptop 60 fps, main thread ≤ 5 ms a frame, first positions ≤ 1.5 s, heap ≤ 80 MB; at 4× CPU with payloads ≥ 24 fps; at 6× with all objects ≥ 20 fps; phones capped at 30 fps. CI checks main-thread time, load time and heap; frame rates are a release check on the reference laptop.
- **Design (D-044):** deep navy chrome with one teal accent (`#2bb3a3`) kept clear of the data colours, 6 px corners, hairline borders, no card shadows; plain Bootstrap 5 plus SatTrack's own `tokens.css` (colours, type scale, spacing, radius) shared by the Dash shell and the viewer; filters in a left panel, collapsible to a thin strip (phones keep the bottom sheet, D-025). Any satellite search offers a browsable list as well as typing.
- Credits in the viewer: USSPACECOM via Space-Track.org with the conjunction caution, GCAT (CC-BY), CelesTrak groups (D-026), CesiumJS, satellite.js, Natural Earth.

3.1 `docs/cesium-spike` — **Done** (22–23 Nov 2026). Spike page and measurements in `docs/cesium-spike/` and `docs/cesium-architecture.md`: parity with Python sgp4 within 9.5 m; the worker gives 20–32 fps at 4–6× CPU against 2–11 fps on the main thread; a real phone ran 59–60 fps with every object. Decisions D-013 to D-029. (~3 h)

**Core (~54.5 h, counting 3.12 at 9 h)**

**Order:** 3.2 → 3.12 → 3.3 → 3.13 → 3.4 → 3.5 → 3.6; 3.7 at any point before Phase 3 is done. 3.12 and 3.13 were added on 24 Nov 2026 (D-044, D-045) and numbered after 3.11 so that existing task references don't change.

3.2 `feature/cesium-viewer` — **Done** in PR #70 (flag off in production; the globe goes on with 3.3). Viewer behind a feature flag (env var): vendoring script and lock file with CI checks (hash mismatch, off-site requests, CSP violations), the worker with the adaptive step and `compute(dates)` engine interface, points coloured by type with the legend, type toggles and space junk mode, CSP (report-only first) and HSTS, credits, clock offset from the server's `Date` header. CI parity test against Python sgp4 (50 m tolerance, same failures on both sides). Budget checks in Playwright. (~12 h)

3.12 `feature/design-tokens-shell` — The design direction (D-044), before 3.3: remove `assets/bootstrap.css` and `assets/bootstrap.min.css` (an old Bootstrap 4.5 Cyborg build that Dash loads on every page) and `dbc.themes.CYBORG` (Bootstrap 5.3 from the jsDelivr CDN); plain Bootstrap 5 plus `tokens.css` (colours, type scale, spacing, radius) shared by the Dash shell and the viewer; deep navy chrome with the one teal accent `#2bb3a3`; Bootstrap 5.3's CSS and the Source Sans 3 font committed under `assets/`, each pinned by a SHA-256 unit test; inline SVG icons instead of Font Awesome's CDN (shortens the CSP, D-041); 15 px app text, 16 px reading text; no inline font sizes or colours in Python layouts. Also the globe size: a compact top bar, the globe filling the rest of the window (instead of Plotly's `calc(70vh - 100px)`) and a full-screen button. (~8–10 h)

3.3a `feature/cesium-filters` — The panel drives the globe (D-048 to D-050): one page-level filter-spec store read by the globe, Plotly 3D/2D and the list; object-type switches and Space junk mode in the panel (junk mode also ticks Inactive), with a note that almost all junk is inactive; the browser's filter spec (`static/viewer/filter_spec.js`) runs the shared conformance cases and masks in the worker with no data reload; opens on every active satellite in any orbit; points coloured by status with no outline. Flag stays off. (~5.5 h)

3.3b `feature/filter-panel` — The rest of the panel (D-044, D-048, D-051): live match count ("16,576 of 32,652 objects", computed on the server), type counts "matching / total", segmented status and orbit controls, "More filters" rows showing their values, active-filter chips with "Clear all", no Update button, Clear Orbits into the Plotly 3D tab, search lists set once at load (Q8 S2), a hint when a shown type matches 0, a filter-change budget test, the D-027 release check, then the globe switched on with the Heroku config var (owner's go-ahead). (~5.5 h)

3.3c `feature/globe-usable` — **Done** in PR #85 (D-052; owner, 27 Nov 2026: production close to unusable on a phone after 3.3b). The globe on by default and Plotly 3D removed (ahead of 3.6); only the open tab holds a view; search as 3.9's browsable list (`/data/search.json`; fly-to and Save image stay in 3.9); Filters open in the browser; the globe drawn on demand, on a darker Earth with smaller red dots; hover labels (3.4's first tier); a loading bar; a phone budget test in CI. Merging it switches the globe on in production.

3.13 `feature/cesium-colour-by` — The "Colour by" menu and legend (D-017), straight after 3.3 (D-045): object type (default), orbit class, status and owner. (~3 h)

3.4 `feature/cesium-selection` — **Done** in this PR (D-054; owner tried every part on a phone, 28 Nov 2026). Three tiers (D-018): throttled hover label, click panel, "More" → the list view. Single selection with toggles for orbit path (one period, past faded), follow camera and ground track (D-019). Labels on the selection and the ~20 nearest when zoomed in (D-023). Every data string through `textContent`. **Scope widened (owner, 28 Nov 2026)** for two audiences, children and casual visitors, and analysts and journalists in comms, tech and space: the panel is fed by an on-demand per-object detail dataset (a pipeline export) and shows a plain headline (name, type, status with operating vs transmitting and end dates, owner, operator and manufacturer with roles, live altitude and speed, for GEO objects the live longitude, launch) with exact values only (masses in kg, no comparisons), then sections in which every fact carries its source and as-of date and uncertain values show a marker in place; a short "Copy citation" link; a share link that opens the globe with the satellite selected (D-024's hash, version and satellite only; 3.5 adds the other fields). Search pick → select + fly-to (from 3.9) and a compact phone bottom card (until 3.5's sheet) are tried by the owner on a local test server before they're decided. (~13 h)

3.4b `feature/card-sections-fullscreen` — **Done** in this PR (D-055; owner, 28 Nov 2026): the card's sections open on their own with a description line, and a full-screen mode with the filter panel as a drawer. (~3 h)

**Next after 3.4 (owner, 28 Nov 2026): the analyst track.** 5.4 (page per satellite), 5.5 (CSV download), 5.3 (counts by owner, country, constellation), then 7.5 (re-entry), then the rest of Phase 3. These serve the analyst and journalist audience sooner; each is small and uses data already ingested.

3.5 `feature/cesium-modes-time-mobile` — 3D / 2D / Columbus switch with ground tracks split at ±180°; camera presets (Earth, LEO close-up, GEO belt); own time scrubber ±1 day with Now, play/pause and 1×–1000× (D-020); shareable links in the URL hash with allowlist parsing (D-024); the phone bottom sheet (D-025) with Playwright tests at phone sizes. (~11 h)

3.6 `refactor/remove-plotly-viz` — Once at parity, remove Plotly 3D/2D callbacks, `dcc.Interval` position refresh and server-side propagation from the request path (keep `compute_satloc` only if still used, e.g. the list view). Flip the feature flag default, then remove it. Switch the Content-Security-Policy from report-only to enforced and drop the Plotly `blob:` worker exception and the USGS tile host (D-041). This retires the 3D payload stopgap (PR #37). (~3 h)

3.7 `chore/licence-agpl` — Open-source licence and contributor agreement (~1.5 h). Must be merged before Phase 3 is done; it does not depend on the other Phase 3 tasks. The repo has no licence today, so it is legally "all rights reserved".
- Owner decides first: AGPL-3.0-only or -or-later (recommended: -only); how contributors sign the agreement (recommended: the CLA GitHub Action, with signatures stored on a branch in the repo, no extra account); and the agreement text (recommended: based on the Apache individual contributor agreement plus an explicit relicensing clause, checked by a lawyer before any revenue use).
- `LICENSE` with the unchanged AGPL-3.0 text; `license` field in `pyproject.toml`; `SPDX-License-Identifier` headers in new files only.
- AGPL source offer: the About page links to the repo at the deployed commit (Heroku `SOURCE_VERSION`).
- `THIRD_PARTY_NOTICES.md`, plus the CesiumJS licence and NOTICE files shipped with the self-hosted build in `static/`; keep the satellite.js MIT licence text.
- `CONTRIBUTING.md` and `docs/legal/CLA.md`; `.github/workflows/cla.yml` (pinned actions), proposed in the PR.
- README licence section, stating that data licences are separate (GCAT CC-BY, Space-Track citation, CelesTrak credit); CLAUDE.md rule: no outside PR is merged until the CLA check passes.
- Decision record D-036 in `DECISIONS.md` and `docs/decisions/`.
- After merge, owner only: make the CLA check a required status check (GitHub settings change).

**Extensions (~16 h, D-028)**

3.8 `feature/constellation-field` — **Done** in PR #69 (24 Nov 2026); its `constellation` field was replaced by D-047's constellation and system fields in PR #81 (25 Nov 2026), with the space station flag (D-043) and decisions D-039, D-040. Pipeline task, parallel to 3.2: download CelesTrak's constellation and operator groups under D-008 and the usage policy (CSV, compressed, once per update, stop on any non-200), keep the last good copy on failure, add a documented `constellation` field to `objects`; a test warns when CelesTrak's index shows a new group (D-026). Also CelesTrak's space station group as `flag_space_station` (D-043). (~4 h)

3.9 `feature/cesium-search-image` — Search by name or SATCAT number with fly-to; "Save image" (PNG) from the canvas with the credits drawn in. Search must offer a browsable list (e.g. newest launches, stations first via `flag_space_station`, D-043) as well as type-to-search (D-044): users include children and casual visitors. Dash 4's `dcc.Dropdown` indexes every option in the browser (2.2 s for ~32k options, measured 24 Nov 2026), so the list is built in the worker, not as Dropdown options. (~4 h)

3.10 `feature/cesium-constellations` — Adds "constellation" and "satellite system" to 3.13's "Colour by" menu and legend, from the D-047 fields (`satellite_constellation_name`, `primary_satellite_system_name`), with the CelesTrak credit. (~2 h)

3.14 `feature/constellation-system-filters` — **Done** in this PR (D-056; owner, 28 Nov 2026: a priority), except the definition popovers (3.14b). Constellation and satellite system filters (D-047): multi-selects on `satellite_constellation_name` and `satellite_system_names`, a "primary system only" switch, and info popovers showing each grouping's definition and source link (`dim__satellite_constellation`, `dim__satellite_system`). Follows 3.3b. (~3 h, estimate)

3.14b `feature/groupings-dataset` — A small `groupings` dataset from `dim__satellite_constellation` and `dim__satellite_system` (name, kind, definition, source name and link, member and active counts), for the filter rows' definition and source popovers and the home page's summary tiles. With the home page work. (~2 h)

3.15 `feature/live-clock-bar` — A slim bar on the globe: "LIVE · 28 Nov 2026 02:44:52 UTC", always visible; it becomes the home of 3.5's time controls (owner, 28 Nov 2026, from comparing with other trackers). (~1.5 h)

3.17 `feature/filter-panel-redesign` — A full redesign of the filter panel once 3.5's time controls and the clock bar (3.15) are in: clearer segments per group of filters, closer to the segmented layouts of professional trackers, while staying sleek and uncluttered (owner, 28 Nov 2026). Options are mocked up and tried by the owner first. Triggered also by D-056's revisit note (six rows in "More filters"). (~6 h, estimate)

3.16 `feature/orbit-on-hover` — On desktop, resting the pointer on a dot for about 300 ms draws its orbit (the selection's orbit code); phones keep tap-to-select. Never while dragging; honours `prefers-reduced-motion`. (~1.5 h)

3.11 `feature/cesium-daylight` — Day/night terminator and satellites dimmed in Earth's shadow; switches the worker to satellite.js's WASM `BulkPropagator` (zero-vector guard, parity-test row, `'wasm-unsafe-eval'` in the CSP) (D-029). (~6 h)

**Done when:** Cesium is the only viewer, in the 3.12 design; filters (with the live match count), the "Colour by" menu (3.13), selection, orbit paths, 2D/3D, time controls and the phone layout all work; the D-027 budget passes (CI checks plus the release check on the reference laptop); the Heroku slug grows by no more than 15 MB; the four extensions (3.8–3.11) are merged; the repo is licensed AGPL-3.0 with a contributor agreement in force (3.7).

---

## Phase 4 — Freshness & SupGP (~12 h)

**Goal:** positions as fresh and accurate as the best free trackers.

4.1 `feature/pipeline-cadence` — Propose (do not apply) a schedule change to several runs per day within Space-Track limits, and a lighter "GP-only" run mode that skips GCAT (GCAT updates ~monthly). Make the app pick up new data **without redeploying** (e.g. app reads the export from S3/HTTPS with cache invalidation keyed on `last_data_update`). Infra changes need owner sign-off. Three changes: the pipeline's 12-hour gate (`--min-hours` in `infra/state/sattrack_state.py`), the EventBridge schedule (`sattrack-scheduler` stack update), and the app reloading `app/current.json` while it runs. GP stays at most once an hour; lower the gate deliberately. (~4 h)

4.2 `feature/supgp-ingest` — Ingest CelesTrak SupGP (OMM JSON) per source group (start with SpaceX, OneWeb, Kuiper, Planet, Iridium, GPS). Respect CelesTrak's usage policy (no more than needed; one fetch per group per run). Design a fetch budget first: CelesTrak enforces download limits on large sets such as Starlink. If a fetch is refused, GP stays the fallback (4.3). Staging model `stg__celestrak__supgp`. (~3.5 h)

**CelesTrak access risk (Nov 2026).** CelesTrak blocks IP addresses that download more than its usage policy allows; the owner's home IP was blocked after old local scripts (no longer run) fetched too often. Rules for 4.2:
- **Never fetch locally.** SupGP is downloaded only by the pipeline on GitHub Actions. Development and tests use a saved sample file, not live requests.
- **One download per group per CelesTrak update.** Skip a group whose data has not changed since the last run (check the update time first), and use the bulk group files, never one request per satellite.
- **No retries on refusal.** A 403/429 or a tiny/HTML body means "no SupGP this run": record it, keep GP for those objects, don't fail the run.
- **Shared runner IPs.** GitHub-hosted runners share IP addresses with other users, so a block may not be caused by us. Warn (report, not a failed run) only when SupGP has been refused for 3 days in a row; lifting a lasting block needs an email to CelesTrak, which is acceptable because GP keeps the app working without it.

4.3 `feature/element-source-precedence` — Intermediate model choosing one element set per object: SupGP if newer than GP epoch and within a sanity bound of GP, else GP. Add `element_source` (`spacetrack_gp` / `celestrak_supgp:<source>`) and `element_epoch` to `fct__gp_elements` and the export. Note: SupGP can have multiple rows per object (multiple sources/epochs) — pick deterministically and document the rule. (~3 h)

4.4 `feature/freshness-ui` — Show element age and source in the detail panel; optional legend/colour mode by element age. (~1.5 h)

**Done when:** most active payloads propagate from SupGP; data refreshes several times a day; UI shows age/source.

---

## Phase 5 — Detail enrichment (~14 h)

**Goal:** deep per-object detail, using data already ingested from GCAT where possible.

5.1 `feature/gcat-physical-fields` — (Pipeline-only, no dependency on Cesium: a good task to swap in if Phase 3 stalls.) From GCAT satcat/psatcat: `bus`, `shape`, `length_m`, `diameter_m`, `power`, `payload`, `equipment`, `motor`, design life where available, with precision/uncertainty handling consistent with existing columns. Add to `fct__satellite_master`. (~3 h)

5.2 `feature/detail-panel` — Detail panel sections: identity, mission, ownership (all co-owners with roles), manufacture, launch (vehicle, site with map pin), physical, orbit, data quality (uncertainty flags, sources, element age). Surface uncertainty visibly — this is a differentiator. (~5 h)

5.3 `feature/rollup-views` (optional) — Simple views by owner, manufacturer, bus, constellation that set the filter spec and fly the camera to the selection. (~2 h)

5.4 `feature/satellite-page` — A shareable page per satellite (`/satellite/<id>`) built from the detail panel, linkable from search results and the globe, and indexable by search engines (README planned item "Satellite informational page"). Do it before 5.3. First on the analyst track, straight after 3.4. (~2 h)

5.5 `feature/list-download` — Download the objects matching the current filters as CSV, with the field names of the data contract, the as-of dates and the citation (USSPACECOM via Space-Track.org with the conjunction caution; GCAT CC-BY; CelesTrak for groupings) in the file. Added 28 Nov 2026 for analysts and journalists. (~2 h)

**Done when:** detail panel covers the fields above with sources/uncertainty shown; each satellite has its own page.

---

## Phase 6 — Natural-language query (~20 h, plan for ~25 h)

**Goal:** "Ask in plain English → see it on the globe", reliable and safe for a public app. The owner has built a self-serve analytics tool before — ask for their learnings at the start of 6.1 and fold them into the design.

6.1 `docs/nlq-design` — Design doc: LLM returns a **filter spec** (Phase 2 schema), never raw SQL. Context = field allowlist + descriptions generated from dbt doc blocks + accepted values. Ambiguity policy (e.g. "Chinese satellites": owner vs manufacturer vs launch site — default + show interpretation, or ask). Model choice (small/cheap: a small, fast model such as Claude Haiku is enough for producing specs), daily spending cap, caching, rate limits per session, server-side API key (Heroku config), prompt-injection considerations. (~3 h)

6.2 `test/nlq-eval-set` — Build ~50 question → expected-satcat-ID-set cases (include ambiguous ones and ones that need SatTrack's multi-org and status data: built in one country/operated by another, co-owned, launched outside owner's country, stopped transmitting but in orbit). Scorer reports precision/recall per case. Run in CI with recorded responses; live runs on demand. Labelling is the expensive part: start with 25 cases and grow the set. (~5 h)

6.3 `feature/nlq-backend` — Endpoint: question → LLM → spec → JSON-Schema validation → (retry once with validation errors) → apply spec. Return spec + interpretation text + counts + uncertainty summary (e.g. "4 matches have uncertain ownership"). (~7 h)

6.4 `feature/nlq-ui` — Query box above the sidebar; resulting spec rendered as editable filter chips in the existing sidebar; globe updates via the same store as Phase 3; example prompts. (~5 h)

**Done when:** eval suite ≥ agreed threshold (set in 6.1), costs capped, interpretation always shown and editable.

---

## Phase 7 — Backlog (pick as wanted)

Recommended order: passes first (README planned items; the main feature for people watching from the ground), then element history and radio.

- **7.1 Passes & visibility**: observer location (browser geolocation, opt-in), client-side pass prediction; add standard magnitude (McCants) for visual passes. (~10 h)
- **7.2 Pass export**: a pass list as CSV and as calendar events (`.ics`). README planned item. (~2 h)
- **7.3 Element history**: append-only GP snapshot table (incremental model) → altitude/decay and manoeuvre plots per object. `raw_history` already keeps 90 days of GP in S3 to seed it. (~8 h)
- **7.4 Radio**: SatNOGS DB frequencies/transmitters in the detail panel. SatNOGS DB data is CC BY-SA 4.0 (share-alike: the republished frequencies keep that licence, so a separate file) and SatNOGS is a community catalogue, not the original publisher, so it needs a recorded sourcing exception like CelesTrak's. **First count its coverage of active GEO and commercial communications satellites** (owner, 28 Nov 2026: analysts in comms are an audience; SatNOGS is likely strongest on amateur and CubeSat missions). (~6–8 h)
- **7.5 Re-entry**: Space-Track decay/TIP predictions as a "re-entering soon" layer. Brought forward onto the analyst track after 5.3 (28 Nov 2026). (~4 h)
- **7.6 Conjunctions**: CelesTrak SOCRATES close approaches visualised between pairs; check CelesTrak's usage policy, show with the conjunction caution. (~8 h)
- **7.7 Deep-space view** (optional): JWST and other L1/L2/lunar/interplanetary craft from JPL Horizons, at a scale where L2 fits (SGP4 can't propagate these). (~8 h)
- **7.8 Operator ephemerides direct** (optional; Starlink files on Space-Track) — only if independence from CelesTrak SupGP is wanted; check licensing before republishing. (~6 h)

---

## Licensing & attribution checklist

- GCAT: CC-BY — cite "data from GCAT (J. McDowell, planet4589.org/space/gcat)" in the app footer/about page.
- Space-Track and CelesTrak: follow their user agreement / usage policy; attribute in the about page.
- Take data only from its original publishers; never republish another tracker's compiled data.
- CesiumJS: Apache 2.0; when self-hosted, ship its licence and NOTICE files (3.7). Cesium ion (if used): check free-tier terms.
- SatTrack code: AGPL-3.0 with a contributor agreement (3.7). The code licence does not change any data licence above.
- Space-Track fields in public outputs: cite "USSPACECOM via Space-Track.org" and keep the caution that public TLEs must not be used for conjunction assessment.
- CelesTrak SupGP and SOCRATES: CelesTrak's usage policy.
- SatNOGS DB (radio, 7.4): CC BY-SA, attribute.
- Not yet verified: "SupGP covers ~77% of active satellites". Check it before quoting it anywhere public.
