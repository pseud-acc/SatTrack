# Architecture decisions

Why SatTrack's components are built the way they are. Each entry records the context, the decision, why it was
made, the options that were rejected and what follows from it. Add an entry in the PR that makes an architecture
decision. Don't rewrite an accepted entry: when a decision changes, add a new one that supersedes it and mark the
old one **Superseded by D-NNN**.

Entries D-001 to D-008 were recorded retrospectively on 22 Nov 2026 from the PRs that made them. D-013 to D-029
are reserved for the Cesium spike (plan 3.1).

Each entry has a record in [`decisions/`](decisions/) with the full trade-off analysis and when to revisit it.
Read the records a feature touches before scoping it.

| ID | Decision | Status | Date | Record |
|---|---|---|---|---|
| [D-001](#d-001-count-the-12-hour-gate-from-the-last-promoted-run) | Count the 12-hour gate from the last promoted run | Accepted | 2026-11-20 | [record](decisions/D-001-gate-from-last-promoted-run.md) |
| [D-002](#d-002-keep-the-first-row-of-a-repeated-gcat-jcat) | Keep the first row of a repeated GCAT JCAT | Accepted | 2026-11-21 | [record](decisions/D-002-first-row-of-repeated-gcat-jcat.md) |
| [D-003](#d-003-carry-omm-elements-in-the-tracking-mart-only) | Carry OMM elements in the tracking mart only | Accepted | 2026-11-21 | [record](decisions/D-003-omm-elements-in-tracking-mart.md) |
| [D-004](#d-004-propagate-from-omm-keep-tle-lines-as-a-one-release-fallback) | Propagate from OMM; keep TLE lines as a one-release fallback | Accepted | 2026-11-21 | [record](decisions/D-004-propagate-from-omm.md) |
| [D-005](#d-005-build-each-propagator-once-per-element-set) | Build each propagator once per element set | Accepted | 2026-11-21 | [record](decisions/D-005-build-propagators-once.md) |
| [D-006](#d-006-show-wgs-84-geodetic-latitude-and-altitude) | Show WGS 84 geodetic latitude and altitude | Accepted | 2026-11-22 | [record](decisions/D-006-wgs84-geodetic-latitude-altitude.md) |
| [D-007](#d-007-stay-on-sgp4-improve-accuracy-through-fresher-elements) | Stay on SGP4; improve accuracy through fresher elements | Accepted | 2026-11-22 | [record](decisions/D-007-stay-on-sgp4.md) |
| [D-008](#d-008-fetch-celestrak-data-only-from-the-pipeline-never-retry-a-refusal) | Fetch CelesTrak data only from the pipeline; never retry a refusal | Accepted | 2026-11-21 | [record](decisions/D-008-celestrak-only-from-pipeline.md) |
| [D-009](#d-009-browser-data-file-one-record-per-object-with-the-warehouses-field-names) | Browser data file: one record per object, with the warehouse's field names | Accepted | 2026-11-22 | [record](decisions/D-009-browser-data-file-records.md) |
| [D-010](#d-010-data-contracts-two-core-datasets-feature-datasets-one-envelope) | Data contracts: two core datasets, feature datasets, one envelope | Accepted | 2026-11-22 | [record](decisions/D-010-data-contracts.md) |
| [D-011](#d-011-objects-file-covers-every-tracked-object-unknown-hidden-by-default) | Objects file covers every tracked object; UNKNOWN hidden by default | Accepted | 2026-11-22 | [record](decisions/D-011-objects-cover-every-tracked-object.md) |
| [D-012](#d-012-the-app-serves-the-data-files-with-threaded-workers-no-extra-cdn-account) | The app serves the data files, with threaded workers; no extra CDN account | Accepted | 2026-11-22 | [record](decisions/D-012-app-serves-data-files.md) |
| [D-013](#d-013-cesium-runs-as-a-js-module-inside-the-dash-page) | Cesium runs as a JS module inside the Dash page | Accepted | 2026-11-22 | [record](decisions/D-013-cesium-js-module-in-dash.md) |
| [D-014](#d-014-self-host-cesiumjs-and-satellitejs-fetched-and-hash-checked-at-build) | Self-host CesiumJS and satellite.js, fetched and hash-checked at build | Accepted | 2026-11-22 | [record](decisions/D-014-self-host-cesium.md) |
| [D-015](#d-015-propagate-in-a-web-worker-and-interpolate-on-the-main-thread) | Propagate in a Web Worker and interpolate on the main thread | Accepted | 2026-11-23 | [record](decisions/D-015-worker-propagation-interpolation.md) |
| [D-016](#d-016-payloads-by-default-rocket-bodies-and-debris-one-switch-away) | Payloads by default; rocket bodies and debris one switch away | Accepted | 2026-11-22 | [record](decisions/D-016-payloads-by-default.md) |
| [D-017](#d-017-colour-by-object-type-with-a-colour-by-menu) | Colour by object type, with a "Colour by" menu | Accepted | 2026-11-22 | [record](decisions/D-017-colour-by-type.md) |
| [D-018](#d-018-three-information-tiers-hover-click-panel-full-record) | Three information tiers: hover, click panel, full record | Accepted | 2026-11-22 | [record](decisions/D-018-three-information-tiers.md) |
| [D-019](#d-019-single-selection-with-per-satellite-toggles) | Single selection with per-satellite toggles | Accepted | 2026-11-22 | [record](decisions/D-019-single-selection-toggles.md) |
| [D-020](#d-020-time-scrubber-of-1-day) | Time scrubber of ±1 day | Accepted | 2026-11-22 | [record](decisions/D-020-time-scrubber-one-day.md) |
| [D-021](#d-021-one-viewer-for-3d-2d-and-columbus-retire-the-plotly-2d-tab) | One viewer for 3D, 2D and Columbus; retire the Plotly 2D tab | Accepted | 2026-11-22 | [record](decisions/D-021-one-viewer-retire-plotly-2d.md) |
| [D-022](#d-022-natural-colour-earth-from-self-hosted-imagery) | Natural-colour Earth from self-hosted imagery | Provisional | 2026-11-22 | [record](decisions/D-022-natural-colour-earth.md) |
| [D-023](#d-023-label-the-selected-satellite-and-close-up-the-nearest-20) | Label the selected satellite and, close up, the nearest 20 | Accepted | 2026-11-22 | [record](decisions/D-023-labels-selected-and-nearest.md) |
| [D-024](#d-024-shareable-links-carry-the-core-view-in-the-url-hash) | Shareable links carry the core view in the URL hash | Accepted | 2026-11-22 | [record](decisions/D-024-shareable-links-url-hash.md) |
| [D-025](#d-025-bottom-sheet-on-phones) | Bottom sheet on phones | Accepted | 2026-11-22 | [record](decisions/D-025-mobile-bottom-sheet.md) |
| [D-026](#d-026-constellations-from-celestraks-group-lists-credited) | Constellations from CelesTrak's group lists, credited | Accepted | 2026-11-22 | [record](decisions/D-026-constellations-from-celestrak-groups.md) |
| [D-027](#d-027-a-measured-performance-budget-for-the-viewer) | A measured performance budget for the viewer | Accepted | 2026-11-23 | [record](decisions/D-027-performance-budget.md) |
| [D-028](#d-028-phase-3-scope-the-core-plus-four-extensions) | Phase 3 scope: the core plus four extensions | Accepted | 2026-11-22 | [record](decisions/D-028-phase-3-scope.md) |
| [D-029](#d-029-javascript-sgp4-in-the-worker-now-wasm-when-shadow-dimming-lands) | JavaScript SGP4 in the worker now; WASM when shadow dimming lands | Accepted | 2026-11-22 | [record](decisions/D-029-worker-engine-js-then-wasm.md) |
| [D-030](#d-030-filter-spec-field-names-are-the-objects-datasets-labels-come-from-dbt-meta) | Filter spec field names are the objects dataset's; labels come from dbt `meta` | Accepted | 2026-11-22 | [record](decisions/D-030-filter-spec-field-names-and-labels.md) |
| [D-031](#d-031-filter-spec-shape-a-versioned-flat-and-list-of-clauses) | Filter spec shape: a versioned flat AND list of clauses | Accepted | 2026-11-22 | [record](decisions/D-031-filter-spec-shape-flat-and-list.md) |
| [D-032](#d-032-missing-values-in-the-filter-spec-are-explicit) | Missing values in the filter spec are explicit | Accepted | 2026-11-22 | [record](decisions/D-032-filter-spec-missing-values.md) |
| [D-033](#d-033-filterable-fields-are-hand-picked-types-values-and-labels-generated-from-dbt) | Filterable fields are hand-picked; types, values and labels generated from dbt | Accepted | 2026-11-22 | [record](decisions/D-033-filter-spec-allowlist-generated-schema.md) |
| [D-034](#d-034-one-set-of-conformance-cases-for-every-filter-spec-implementation) | One set of conformance cases for every filter spec implementation | Accepted | 2026-11-22 | [record](decisions/D-034-filter-spec-shared-conformance-cases.md) |
| [D-035](#d-035-the-servers-sidebar-filters-the-objects-dataset-no-fallback) | The server's sidebar filters the objects dataset; no fallback | Accepted | 2026-11-22 | [record](decisions/D-035-sidebar-filters-the-objects-dataset.md) |
| [D-037](#d-037-pipeline-warnings-email-a-summary-without-failing-the-run) | Pipeline warnings email a summary without failing the run | Accepted | 2026-11-23 | [record](decisions/D-037-pipeline-warnings-email-without-failing.md) |
| [D-039](#d-039-celestrak-groups-at-most-once-a-day-and-no-request-for-20-hours-after-a-refusal) | CelesTrak groups: at most once a day, and no request for 20 hours after a refusal | Proposed | 2026-11-23 | [record](decisions/D-039-celestrak-group-fetch-cadence.md) |
| [D-040](#d-040-celestrak-groups-raw-tables-in-the-warehouse-replaced-all-or-nothing-never-holding-a-unit) | CelesTrak groups: raw tables in the warehouse, replaced all or nothing, never holding a unit | Proposed | 2026-11-23 | [record](decisions/D-040-celestrak-groups-storage-and-failure.md) |

---

## D-001 Count the 12-hour gate from the last promoted run
**Status:** Accepted, 2026-11-20 (#48). **Component:** pipeline state (`infra/state/sattrack_state.py`).

**Context.** The gate stops a run within 12 hours of the last one, to protect the Space-Track quota. It counted from
the last fully OK run, so after a run that promoted data with warnings, the next scheduled run could start again too soon.

**Decision.** Count from `last_promoted_at`: the last run whose data went live, OK or with warnings. Fall back to
`last_ok_at` for manifests written before the key existed.

**Why.** What should space runs out is new data going live, not a clean result. Counting from promotion keeps runs
apart whenever data actually changed.

**Consequences.** `--force` still skips the gate for manual runs. Lowering the gate for several runs a day is a
separate, deliberate change (plan 4.1).

## D-002 Keep the first row of a repeated GCAT JCAT
**Status:** Accepted, 2026-11-21 (#51). **Component:** dbt `int__jsr__launch_events`.

**Context.** GCAT's launch log gave two failed-launch Kuiper payloads each the same JCAT (F01824, F01834) on 15 Nov.
The primary-key test failed and the pipeline held all GCAT details for five days.

**Decision.** Keep the first row per JCAT in GCAT's own file order (`_source_row_number`). Report a repeated JCAT as a
warning; more than 10 still stop the update.

**Why.** GCAT's maintainer adds corrections after the original entry, so the first row is the valid one. A fixed rule
from source order needs no hand-maintained list and keeps details flowing.

**Rejected.** Dropping every duplicated row: it lost valid launches. A manual exclusion list: it breaks the rule that
the pipeline runs unattended.

## D-003 Carry OMM elements in the tracking mart only
**Status:** Accepted, 2026-11-21 (#50). **Component:** dbt `fct__gp_elements`.

**Decision.** The full OMM element set (mean motion derivatives, revolution number, element set number, ephemeris type,
classification) goes into the tracking mart, not `fct__satellite_master`.

**Why.** Since #42 the app takes elements from the tracking mart, which updates every run. The master is held whenever
GCAT enrichment fails, so elements there would go stale.

**Consequences.** A warning-level check flags any `ephemeris_type` other than 0 (SGP4).

## D-004 Propagate from OMM; keep TLE lines as a one-release fallback
**Status:** Accepted, 2026-11-21 (#54, #56). **Component:** app export and `helper__satellite_position.py`.

**Context.** TLE lines cannot hold catalogue numbers above 339,999 (Alpha-5's limit). SupGP is published only as OMM,
and the browser propagator planned for Phase 3 (satellite.js) reads OMM directly.

**Decision.** Export the OMM fields in `satcat_tle.csv` and build each propagator with `sgp4.omm.initialize`. TLE lines
are used only when a row has no complete OMM set, for one release. A satellite without TLE lines is still exported.
sgp4 refuses satellite numbers above 339,999, so those are built with number 0, which is only a label.

**Why.** It removes the catalogue-number ceiling and puts the app on the format every later phase uses.

**Evidence.** Across 19,736 satellites the position change is median 0.00 m, 99th percentile 5.6 m, maximum 236 m
(high-drag LEO two days after epoch, from OMM's extra digits of B* and eccentricity). For the ISS, TLE and OMM land
within 0.2 m of each other, both about 1.1 km from NASA's ephemeris.

## D-005 Build each propagator once per element set
**Status:** Accepted, 2026-11-21 (#56). **Component:** `helper__satellite_position.py`.

**Context.** Building a propagator costs about 15× more than propagating it, and every callback rebuilt all of them.

**Decision.** Cache the propagators in each worker process, keyed by the catalogue number plus every value they are
built from. Build them at start-up, and propagate all satellites in one vectorised `SatrecArray` call.

**Why.** Updating all ~19,700 satellites went from 188 ms to 116 ms per callback, and the 2D ground track from 71 ms
to 42 ms, for about 20 MB per worker. The full-value key means a corrected element set republished with the same
epoch can't be served from a stale propagator.

**Rejected.** Keying by (satellite, epoch) only (Copilot review). Fully vectorised construction: the sgp4 library builds
one propagator per call, and the cache already takes construction out of the callbacks.

## D-006 Show WGS 84 geodetic latitude and altitude
**Status:** Accepted, 2026-11-22 (#56). **Component:** `helper__satellite_position.py`.

**Context.** Positions were converted to latitude and altitude on a sphere. Checked against outside data, the ISS showed
about 19 km off on the map and up to 13 km low in altitude.

**Decision.** Geodetic latitude and height above the WGS 84 ellipsoid (Kelso's iteration, vectorised). Longitude is
unchanged. The 3D globe still draws a sphere.

**Why.** Maps and other trackers use WGS 84. With the same TLE as wheretheiss.at, SatTrack now gives identical
latitude, longitude and altitude. Against NASA's ISS ephemeris the displayed position went from 18.8 km to 0.97 km
(median).

## D-007 Stay on SGP4; improve accuracy through fresher elements
**Status:** Accepted, 2026-11-22. **Component:** propagation (server now, browser from Phase 3).

**Decision.** Keep SGP4. Improve accuracy with fresher element sets (several runs a day, plan 4.1) and SupGP
(plans 4.2–4.3), not with another propagator.

**Why.** Space-Track's GP elements are fitted for SGP4; another propagator would misread them. SGP4-XP needs its own
element sets and a licensed binary library. Operator ephemerides (OEM) cover only a few hundred objects for a few days.
The measured ISS error grows from 0.75 km in the first 12 h after epoch to about 2 km at 36–48 h, so element age is
the main source of error.

**Revisit.** OEM for a few objects (e.g. the ISS from NASA) in pass prediction (Phase 7).

## D-008 Fetch CelesTrak data only from the pipeline; never retry a refusal
**Status:** Accepted, 2026-11-21 (#55). **Component:** plan 4.2 SupGP ingest.

**Context.** CelesTrak blocked the owner's home IP after old local scripts fetched too often.

**Decision.** Only the pipeline on GitHub Actions downloads SupGP. Download each group at most once per CelesTrak
update, using the bulk files. Treat a 403, a 429 or an HTML body as "no SupGP this run": keep GP and don't retry. Warn
only after 3 refused days in a row, because GitHub's runners share IP addresses with other users.

**Why.** A block is hard to lift, and GP keeps the app working without SupGP.

## D-009 Browser data file: one record per object, with the warehouse's field names
**Status:** Accepted, 2026-11-22 (plan 2.1). **Component:** the app's browser data file and its reader in the browser.

**Context.** From Phase 3 the browser propagates every tracked object itself (32,652 on 21 Nov: payloads, rocket
bodies, debris). It needs one file holding each object's OMM element set and the fields the filters use. Planned uses
mix bulk work (propagating, filtering, grouping all objects) with single-object work (click, detail panel, pass
prediction, per-satellite pages, API).

**Decision.**
- The file holds one record per object, sorted by `satcat_id`, under a header with `schema`, `count`, `generated_at`
  and `run_id`.
- Field names are the dbt mart column names (`satcat_id`, `mean_motion`, `operational_status`, …), with no renaming
  and no lookup tables. The browser gets satellite.js's OMM names by uppercasing the element fields' names, a fixed
  rule rather than a table.
- On load the browser builds its own columns (typed arrays) and an id index, in a Web Worker. That form is derived
  each time and never stored.

**Why.**
- Each record stands on its own: a bad value affects one object, every record can be checked against a JSON Schema
  before publishing, and any older file can serve as the fallback.
- Bulk operations run equally fast once the browser has built its columns: filtering all objects takes about 1 ms
  either way.
- The columnar file's only advantage is first load: +26 ms on a laptop, +152 ms at 4× CPU (mid-range phone) and
  +0.33 MB to download with Brotli (1.70 against 1.37 MB). That's paid once per new dataset and stays off the page's
  main thread.

**Rejected.**
- One list per field with lookup codes (smallest, 1.61 MB gzip): the codes couple two structures that can drift
  apart, and a missing or reordered entry silently shifts values onto the wrong objects.
- One list per field with real names: the same alignment risk, and single-record work (clicks, pass prediction, the
  list view, debugging) needs a rebuild step.
- NDJSON (one record per line): slower to parse (+17 ms laptop, +35 ms at 4×), with no header for the object count.

**Evidence.** Measured on the warehouse of 21 Nov (32,652 objects, 27 fields) in headless Chromium, best of 3:

| | records | columns, real names | NDJSON |
|---|---|---|---|
| Raw / gzip / Brotli | 23.7 / 2.44 / 1.70 MB | 8.8 / 1.63 / 1.37 MB | 23.7 / ≈2.44 / ≈1.70 MB |
| Parse + build columns, laptop / 4× CPU | 43 / 271 ms | 17 / 119 ms | 60 / 306 ms |
| Browser memory once loaded | 15.1 MB | 13.4 MB | 15.1 MB |
| Filter all objects, 4× CPU | 1.2 ms | 1.0 ms | 1.5 ms |
| Read one full record, 4× CPU | 8 µs | 27 µs | 13 µs |

**Consequences.** The pipeline validates every record against a JSON Schema and checks the count and unique, sorted
ids. Lists stay JSON arrays (empty, not null, when there are none). Element numbers are never rounded. The format is
documented in `docs/app-data-contract.md`. Scope and delivery are separate decisions.

## D-010 Data contracts: two core datasets, feature datasets, one envelope
**Status:** Accepted, 2026-11-22 (plan 2.1). **Component:** every data file the pipeline publishes for the app.

**Context.** The roadmap and growth plan need many datasets over time: the globe, the detail panel, re-entries,
conjunctions, radio frequencies, element history, the replay and event pages. Defining them one by one risks
incompatible shapes and files that can drift between runs.

**Decision.**
- **Core datasets:** `objects` (every tracked object, loaded on every page) and `object_detail` (loaded per satellite
  on demand). `object_detail`'s shape is documented in 2.1; its file ships with the detail panel (3.4).
- **Feature datasets** are added with the feature that needs them: `reentries`, `conjunctions`, `transmitters`,
  `element_history`, `catalogue_history`, `launch_sites`, `organisations`, `events`.
- **The envelope every dataset shares:**
  - a header with `dataset`, `schema`, `count`, `generated_at`, `run_id`, `key`, `attribution` and `caution`;
  - records keyed by `satcat_id`, with the warehouse's field names;
  - lists as arrays and gaps as `null`;
  - additive changes only, so a renamed field or a changed meaning raises `schema`;
  - one JSON Schema per dataset in `app/contracts/`, every record validated before publishing.
- **One manifest:** `app/current.json` lists every dataset of a run with its path, SHA-256 and schema version, and the
  app loads all of a run's files or none.

**Why.** Datasets can be added and changed independently without breaking readers. `satcat_id` joins them without
relying on position. Each file carries its own licence, so SatNOGS's CC BY-SA data never mixes with CC BY or
Space-Track data. A run is always loaded as a consistent whole.

**Rejected.** One growing file with everything: it would slow the first load and mix licences. Separate ad-hoc formats
per feature: they drift apart and each needs its own reader.

## D-011 Objects file covers every tracked object; UNKNOWN hidden by default
**Status:** Accepted, 2026-11-22 (plan 2.1). **Component:** the `objects` dataset.

**Decision.** Include every object in the GP feed (32,652 on 21 Nov: 19,742 payloads, 10,179 debris, 2,219 rocket
bodies, 512 `UNKNOWN`), each with Space-Track's `object_type`. The 512 `UNKNOWN` objects are Space-Track analyst
objects named "TBA - TO BE ASSIGNED", with no international designator, GCAT match, launch year or owner. They are
included, and the UI hides them unless switched on. Display defaults for debris and rocket bodies are set by the
Cesium spike (3.1).

**Why.** The re-entry layer, conjunctions, statistics, the replay and bright passes all need rocket bodies and
debris. Including them costs 0.72 MB against payloads only (1.70 against 0.98 MB with Brotli). The `UNKNOWN` rule
comes straight from the source data, costs 0.03 MB, and keeps real tracked objects available.

**Consequences.** The filter spec (2.2) needs a fixed rule for missing values. It's needed anyway, for the 2 payloads
without a launch year and the 515 objects without an owner.

## D-012 The app serves the data files, with threaded workers; no extra CDN account
**Status:** Accepted, 2026-11-22 (plan 2.1). **Component:** delivery of the data files; `Procfile`.

**Context.** The S3 bucket is private and also holds the warehouse, logs and state. Heroku's router buffers only 1 MB
of each response; gunicorn's default sync workers (2) handle one request each, so a download the buffers can't
absorb holds a whole worker until the client has read it.

**Measured** (CI build check, 22 Nov, PR #59 control): with sync workers, four slow downloads of a 3 MB file
blocked nothing (the socket buffers took it all; pages answered in 1 ms), but a 24 MB file held both workers and a
page request timed out after 20 s. With `--threads 4`, pages answered in 1 ms during the 24 MB downloads. So at
today's 1.70 MB the risk is small; it grows with the data files (all `object_detail` records ≈ 8–15 MB).

**Decision.** The pipeline writes the pre-compressed file beside the CSV, listed in `app/current.json`. The app loads
it at start-up and serves it with an ETag. gunicorn runs threaded workers (`--threads 4`), so a slow download
occupies one thread and not the worker.

**Why.**
- No AWS changes, the bucket stays private, and the file always comes from the same run as the CSV.
- Local runs and CI use it the same way as the CSV.
- The threads remove the slow-client risk before the data files grow, at no memory cost, and CI's build check
  tests it at a size that does block sync workers.

**Rejected.**
- Cloudflare in front: one more account and a DNS move to maintain, which the owner rejected for its management overhead.
- A public S3 file or CloudFront now: new AWS resources, CORS and cache invalidation, with no need at today's traffic.
- Short-lived S3 links: CORS on the private bucket, links that break when the key is rotated, and awkward caching.
- Splitting the file below 1 MB: multi-part loads add failure modes.

**Revisit.** If traffic needs a CDN (e.g. the growth plan's launch posts), use AWS CloudFront in the existing account
through CloudFormation: no new account and no DNS change.


## D-013 Cesium runs as a JS module inside the Dash page
**Status:** Accepted, 2026-11-22 (plan 3.1). **Component:** the tracker page.

**Context.** Phase 3 replaces the Plotly 3D and 2D figures with a CesiumJS globe. The sidebar, list view and routing
stay in Dash. The viewer needs the filters from Dash and has to report clicks back.

**Decision.** Dash renders an empty `html.Div(id="globe")` that no callback ever writes to. Code in
`static/viewer/`, loaded only on the tracker page, mounts the Cesium viewer in it. Filters reach the viewer through
a `dcc.Store` and a clientside callback; a click goes back through `dash_clientside.set_props` on a second store,
which server callbacks read for the detail panel and list.

**Why.** The module has the whole Cesium API, so hover labels, orbit paths and every planned extension are possible.
No npm toolchain. Frame rate is the same as with the alternatives because the same Cesium code runs either way.

**Rejected.** A custom Dash component: adds an npm build to the repo, CI and Heroku for no feature the viewer needs.
A separate page in an iframe: a second document in memory on phones, and selection sync through `postMessage`.

**Consequences.** A test asserts that no callback outputs to the globe div. Viewer logic is tested with Playwright
against state the viewer exposes. Viewer code never goes in `assets/`, which Dash adds to every page.

## D-014 Self-host CesiumJS and satellite.js, fetched and hash-checked at build
**Status:** Accepted, 2026-11-22 (plan 3.1). Supersedes the roadmap's "load CesiumJS from a CDN".
**Component:** front-end dependencies; the Heroku and CI builds.

**Context.** Subresource Integrity covers only the script tag's file. Cesium then loads its workers, assets and
imagery from its base URL, which SRI doesn't check. The app serves Plotly itself today and has no CSP yet.

**Decision.** `vendor/cesium.lock` pins Cesium and satellite.js versions and their npm tarball hashes. A script run
by the Heroku build and CI's Heroku-identical build downloads each tarball, verifies the hash, extracts the files
the viewer uses (about 10.2 MB of Cesium's 22.8 MB build) and writes a manifest of per-file hashes. They're served
from a versioned `static/vendor/` path with long-lived caching. A hash mismatch fails the build and the live release
stays. No Cesium ion account or token.

**Why.** No third-party server at runtime; every file is verified, not just Cesium.js; the CSP stays `'self'`
(plus `worker-src 'self'`, and `'wasm-unsafe-eval'` once WASM is used, D-029); upgrades happen only through a PR.

**Rejected.** jsDelivr with SRI: unverified workers and assets, and a runtime dependency on the CDN. Committing the
files: about 10 MB of git history per upgrade. An npm bundle: a new toolchain.

**Consequences.** The slug grows by about 10 MB, so Phase 3's "slug not materially increased" check becomes a budget
(within 15 MB). Dependabot can't see the versions, so a weekly workflow (proposed in its PR) opens an issue for new
releases. CI fails on any off-site request and on CSP violations.

## D-015 Propagate in a Web Worker and interpolate on the main thread
**Status:** Accepted, 2026-11-23 (plan 3.1; provisional on 22 Nov until the real-phone run). **Component:** the viewer.

**Context.** Propagating all 32,652 objects takes 19–30 ms on a laptop's main thread; phones are 4–6× slower.

**Decision.** A Web Worker loads the data, builds the satellite.js records and computes positions on a fixed grid of
simulation time. The main thread interpolates linearly between the two samples around the current time. A small
controller widens the step (0.25–10 s of simulation time) when worker passes or frames are slow, or play speed is
high. The engine inside the worker is D-029.

**Why.** Linear interpolation over 1 s is off by about 1 m in low orbit (midpoint error s²/8R; 110 m at 10 s),
against ~15 km per pixel at a whole-globe view, so the calculation rate can drop freely. One code path degrades
gracefully on slow devices.

**Rejected.** Main thread every frame: 2–11 fps at 4–6× CPU. Worker at a fixed 1 Hz: fast play speeds and very slow
devices degrade badly. Two code paths: double testing for no visible gain.

**Evidence.** Laptop at 4–6× CPU: 20–32 fps and first positions in 1–1.7 s with the worker, against 2–11 fps and
3–12 s without. Real phone (Adreno 740), 23 Nov: 59–60 fps with payloads and with all 32,652 objects, main thread
1.6–2.8 ms a frame. Detail in `docs/cesium-architecture.md`.

## D-016 Payloads by default; rocket bodies and debris one switch away
**Status:** Accepted, 2026-11-22 (plan 3.1). Completes D-011's display defaults. **Component:** the viewer.

**Decision.** The globe opens with payloads (19,742). Rocket bodies and debris have their own toggles and a "space
junk mode" switch turns both on. UNKNOWN stays hidden (D-011).

**Why.** The owner's call: use cases vary, and people should switch space junk on rather than be met with a cluttered
first view. It also lightens first render on phones.

## D-017 Colour by object type, with a "Colour by" menu
**Status:** Accepted, 2026-11-22 (plan 3.1). **Component:** the viewer.

**Decision.** Points are coloured by type by default, matching the D-016 toggles. A menu switches to orbit class,
status, owner or constellation (D-026), with a legend that follows it.

**Rejected.** Type only (loses today's owner and status views); orbit class by default.

## D-018 Three information tiers: hover, click panel, full record
**Status:** Accepted, 2026-11-22 (plan 3.1). **Component:** the viewer and the list view.

**Decision.** Hover: name, type, orbit, owner. Click: a panel with altitude, speed, period, element age and launch.
"More" opens the full record in the list view. A tap replaces hover on touch screens. Hover picking is throttled to
about 20 a second. Every data string is written with `textContent`.

## D-019 Single selection with per-satellite toggles
**Status:** Accepted, 2026-11-22 (plan 3.1). **Component:** the viewer.

**Decision.** One selected satellite at a time. Its panel has three toggles: orbit path (one period, past faded; 3D),
follow camera (3D) and ground track (switches the view to 2D).

**Why.** The owner's call: each is the user's choice for the selected satellite, not a fixed behaviour.
Multi-select is left for later.

## D-020 Time scrubber of ±1 day
**Status:** Accepted, 2026-11-22 (plan 3.1). **Component:** the viewer.

**Decision.** Our own scrubber covering ±1 day from now, with a Now button, play/pause and speeds 1×–1000×. The panel
shows element age at the displayed time.

**Why.** SGP4 drifts by roughly 1–3 km a day from the element epoch in low orbit; the owner chose a window tighter than
the ±3 days proposed. Look-ahead stops at 24 h.

**Rejected.** Now-only controls (no replay); Cesium's timeline widget (dated, poor on phones, unbounded range).

## D-021 One viewer for 3D, 2D and Columbus; retire the Plotly 2D tab
**Status:** Accepted, 2026-11-22 (plan 3.1). **Component:** the tracker page.

**Decision.** Cesium's scene modes replace both Plotly tabs. Every satellite shows in 2D.

**Why.** One renderer and one position path; D-019's ground-track toggle needs it.

**Consequences.** PNG export is rebuilt from the Cesium canvas (D-028). Ground tracks split at ±180°.

## D-022 Natural-colour Earth from self-hosted imagery
**Status:** Accepted (provisional), 2026-11-22 (plan 3.1). **Component:** the viewer.

**Decision.** Natural Earth II, which ships with Cesium (public domain). No external tile servers and no Cesium ion.

**Why.** The owner's call, to revisit with point styling. Brightness and saturation are runtime layer settings, so a
muted look later is a small change or a user toggle.

**Rejected.** NASA GIBS tiles: a runtime third-party dependency, against D-014.

## D-023 Label the selected satellite and, close up, the nearest 20
**Status:** Accepted, 2026-11-22 (plan 3.1). **Component:** the viewer.

**Decision.** The selected satellite is always labelled. When zoomed in, the ~20 nearest objects are labelled too;
the worker finds them with each sample. N and the zoom threshold are set within the performance budget (D-027).

## D-024 Shareable links carry the core view in the URL hash
**Status:** Accepted, 2026-11-22 (plan 3.1). **Component:** the viewer.

**Decision.** The hash carries a format version, satellite, time, 2D/3D mode, colour mode and type toggles. The camera
follows from the selection. Each field is parsed against an allowlist, the hash is capped in length, nothing from it is
written as HTML, and the user's location is never included. A time outside the ±1-day window shows "now" with a
notice.

**Why.** Reproduces what matters with a small format that's easy to validate. The hash never reaches the server.

**Rejected.** Full state with camera (larger format to maintain); short links stored on the server (storage and
abuse handling).

**Consequences.** Check before release whether Google Analytics records the hash.

## D-025 Bottom sheet on phones
**Status:** Accepted, 2026-11-22 (plan 3.1). **Component:** the tracker page.

**Decision.** On phones the globe fills the screen and one bottom sheet holds time (peek), filters or the selected
satellite (half) and details (full). Desktop keeps the sidebar.

**Rejected.** Today's collapsible sidebar (covers the globe); floating buttons with separate overlays.

## D-026 Constellations from CelesTrak's group lists, credited
**Status:** Accepted, 2026-11-22 (plan 3.1). **Component:** pipeline; the `objects` dataset; the viewer's credits.

**Context.** Colouring by constellation (D-017) needs membership the data doesn't have. GCAT matches CelesTrak for
the broadband fleets but has no plane labels for Galileo, GLONASS or Globalstar and few for Iridium; CelesTrak's
groups reflect new launches within hours.

**Decision.** The pipeline downloads CelesTrak's groups under D-008 and CelesTrak's usage policy (CSV, compressed,
once per update, stop on any non-200, wait 15 minutes after a 5xx) and adds a `constellation` field to each object.
Groups come from a config list: constellations (starlink, oneweb, kuiper, qianfan, hulianwang, iridium-NEXT,
globalstar, orbcomm, gps-ops, glo-ops, galileo, beidou, tdrss, dmc), then operators (planet, spire, intelsat, ses,
eutelsat, telesat); every other group is excluded. An object in two groups takes the first in config order. Display
names are CelesTrak's group titles without "Operational". A test warns when CelesTrak's index shows a new group. The
viewer credits "Constellation groups: CelesTrak (Dr T.S. Kelso)". CLAUDE.md records this as the one exception to
"never republish another tracker's compiled data".

**Why.** Membership comes from the source rather than rules SatTrack writes, and it's current. CelesTrak's usage
policy (16 Nov 2026) covers download behaviour and is silent on redistribution; the owner treats that silence as
permission, with credit.

**Rejected.** GCAT families only (gaps above); name-prefix rules (a hand-maintained list); an automatic threshold on
name prefixes (misgroups COSMOS, OBJECT and USA).

**Consequences.** Risk accepted: the permission rests on an interpretation. If CelesTrak objects, fall back to the
GCAT rule (a family from the leading letters of psatcat's `Program`, counted when at least 50 active payloads carry
plane labels). Delivered as a pipeline task parallel to 3.2; a manual workflow (#62) provides the same files for
local testing, because the owner's IP is blocked by CelesTrak.

## D-027 A measured performance budget for the viewer
**Status:** Accepted, 2026-11-23 (plan 3.1; provisional on 22 Nov until the real-phone run). **Component:** the viewer;
its tests.

**Decision.** Laptop (reference: Intel Iris Xe): 60 fps, main thread ≤ 5 ms a frame, first positions ≤ 1.5 s, heap
≤ 80 MB. At 4× CPU with payloads: ≥ 24 fps and first positions ≤ 2 s. At 6× CPU with all objects: ≥ 20 fps. Phones
capped at 30 fps. If frames stay below 20 fps for 5 s with space junk mode on, the viewer suggests switching debris
off; it never switches it off itself.

**Why.** Set from the spike's numbers with a margin, so a regression shows as a failed check rather than an opinion.

**Evidence.** Spike matrix in `docs/cesium-architecture.md`. Real phone (Adreno 740, 23 Nov): 59–60 fps uncapped,
main thread 1.6–2.8 ms, first positions 0.9–1.2 s, with payloads and with all objects. A high-end phone, so the
throttled targets still stand in for mid-range and low-end.

**Consequences.** CI has no GPU: main-thread time, load time and heap are CI checks; frame rates are a release step on
the reference laptop (median of 3 runs, 2 fps tolerance). Each feature PR reports its main-thread cost; raising the
budget needs a decision entry.

## D-028 Phase 3 scope: the core plus four extensions
**Status:** Accepted, 2026-11-22 (plan 3.1). **Component:** the roadmap.

**Decision.** Phase 3 is the core (3.2–3.6 and D-013 to D-027) plus search and fly-to, save image (PNG), constellation
colouring (D-026) and day/night with shadow dimming. Re-estimated at ~55–65 h, split into core and extension tasks in
the roadmap.

**Why.** The owner's call: each fills a gap the review found (PNG export was the one feature that would be lost) or
uses data already in hand.

**Consequences.** Constellation colouring waits for the pipeline task that adds the `constellation` field. Shadow
dimming is the trigger to move the worker to WASM (D-029).

## D-029 JavaScript SGP4 in the worker now; WASM when shadow dimming lands
**Status:** Accepted, 2026-11-22 (plan 3.1). **Component:** the viewer's worker.

**Decision.** The worker hides the engine behind one interface, `compute(dates) → positions`. 3.2 ships satellite.js's
JavaScript `propagate()`. Switch to its WASM `BulkPropagator` when day/night shadow dimming is built (D-028), or
earlier if a real phone shows high-speed play degrading.

**Why.** JavaScript wins on safety and upkeep: failed objects come back as NaN (WASM returns a silent (0, 0, 0)), the
CSP needs no `'wasm-unsafe-eval'`, and it's easier to debug. WASM wins on bulk work: 2–3× faster (20 against 51 ms a
pass on the laptop), built-in sun and shadow calculators, less battery. Tally across 24 areas: JS 7, WASM 8, tie 9.

**Consequences.** The switch adds a zero-vector guard, a parity-test row and `'wasm-unsafe-eval'` in the CSP. In a
worker, import maps don't apply: import the WASM runtime and module by path.

## D-030 Filter spec field names are the objects dataset's; labels come from dbt `meta`
**Status:** Accepted, 2026-11-22 (plan 2.2). **Full analysis:** [decisions/D-030](decisions/D-030-filter-spec-field-names-and-labels.md).

Spec clauses use the `objects` dataset's field names (D-010). The label people see comes from the mart column's
`config: meta: label:` in the dbt YAML, written into the schema as the field's `title`; the build fails without one.
Users never see a snake_case name.

## D-031 Filter spec shape: a versioned flat AND list of clauses
**Status:** Accepted, 2026-11-22 (plan 2.2). **Full analysis:** [decisions/D-031](decisions/D-031-filter-spec-shape-flat-and-list.md).

`{"version": 1, "clauses": [{"field", "op", "value"}]}`, AND-ed; ops `eq`, `in`, `not_in`, `between`,
`contains_any`, `is_missing`. A nested tree waits for evidence: the analysis file lists the NL-query and UI
triggers that would justify a version 2.

## D-032 Missing values in the filter spec are explicit
**Status:** Accepted, 2026-11-22 (plan 2.2). **Full analysis:** [decisions/D-032](decisions/D-032-filter-spec-missing-values.md).

No clause matches a missing value unless it says so (`null` in an `in` or `contains_any` list, `include_missing` on
`between`, or `is_missing`); `not_in` is the exact complement of `in`. "Unknown" in the UI is `null` in the spec.

## D-033 Filterable fields are hand-picked; types, values and labels generated from dbt
**Status:** Accepted, 2026-11-22 (plan 2.2). **Full analysis:** [decisions/D-033](decisions/D-033-filter-spec-allowlist-generated-schema.md).

`app/contracts/filter_fields.yml` lists the nine filterable fields; `pipeline/scripts/build_filter_spec_schema.py`
generates `app/contracts/filter_spec.schema.json` from it and the mart YAML; a pipeline test fails CI if the committed
schema is stale.

## D-034 One set of conformance cases for every filter spec implementation
**Status:** Accepted, 2026-11-22 (plan 2.2). **Full analysis:** [decisions/D-034](decisions/D-034-filter-spec-shared-conformance-cases.md).

`tests/contracts/filter_spec_cases.json` (records, specs, hand-worked expected ids, invalid specs) is run by pytest
now and by the browser implementation in Phase 3.

## D-035 The server's sidebar filters the objects dataset; no fallback
**Status:** Accepted, 2026-11-22 (plan 2.2). **Full analysis:** [decisions/D-035](decisions/D-035-sidebar-filters-the-objects-dataset.md).

At start-up the app builds a filter table from the `objects` dataset and the sidebar selects the CSV's rows by
`satcat_id`: no name mapping. Measured on the full export: 0.86 s, ~81 MB peak and ~15 MB kept per worker. A missing
or bad dataset stops start-up with a `FATAL` log line (and fails CI's build check); there is no fallback. Rejected:
renaming the CSV's columns until 3.6, and falling back to that. Merged only after production published `objects.json`.

## D-037 Pipeline warnings email a summary without failing the run
**Status:** Accepted, 2026-11-23. **Component:** the run report and the `notify` job in `pipeline.yml`.

**Context.** Any result other than OK failed the job so GitHub would email the owner. On 23 Nov a run published all
its data but failed on a source-freshness warning: a misleading alert. Warn-severity checks didn't alert at all.

**Decision.** A unit not published, a non-zero exit or stale data is still a problem and fails the job. A warn check
or a stale source in a run with no problem is a warning: the job passes, and a separate `notify` job (only
`issues: write`) comments the public summary on the open "Pipeline warnings" issue, or opens it, so GitHub emails the
owner on every such run. The next run without warnings closes it. Each warning shows how long it has lasted, from
Elementary's per-run results and `audit.source_freshness`.

**Why.** A red run should mean data didn't go live. The issue needs no new account or AWS change.

**Rejected.** Email through AWS SES (new AWS resources); an annotation only (warnings go unseen); emailing only when
the warnings change (the owner chose every run).

**Consequences.** A permanent warning emails every run, so it gets fixed or its severity changed by decision (#65).

## D-039 CelesTrak groups: at most once a day, and no request for 20 hours after a refusal
**Status:** Proposed (owner to confirm), 2026-11-23. **Component:** `sattrack_ingest/celestrak_groups.py` and
`config.py`; reused by SupGP (4.2).

**Context.** D-026 and D-008 say once per update, stop on any non-200, wait 15 minutes after a 5xx, never retry a
refusal. They don't say how often the daily run downloads, or what "never retry" means across runs.

**Decision.** Download only when the landed copy is at least 20 hours old. Any refusal stops the download at once,
is recorded in `audit.source_refusal`, and blocks every CelesTrak request for 20 hours; the last copy stays.
A refusal that lasts 3 days shows as the source's freshness warning (D-008, D-037).

**Why.** Membership changes slowly; one download a day holds whatever the schedule becomes (4.1) and never repeats a
refusal the same day, which more than covers the 15-minute rule.

**Rejected.** Every 2-hour update (load for no gain); weekly (new batches uncoloured for days); a human reset after a
refusal (breaks the 14-day rule).

**Consequences.** Membership up to a day old; both limits are one-line config changes.

## D-040 CelesTrak groups: raw tables in the warehouse, replaced all or nothing, never holding a unit
**Status:** Proposed (owner to confirm), 2026-11-23. **Component:** `raw_celestrak`, the `celestrak` dbt source,
`fct__satellite_master`.

**Context.** D-026 says keep the last good copy; it doesn't say where, what a partial download does, or how a first
run with nothing to keep behaves.

**Decision.** Land the group CSVs (with CelesTrak's `GROUP` value in front), the index page's groups and titles, and
the config list (`config.py`) as `raw_celestrak.*` tables, like every other source, carried by the warehouse and
`raw_history`. Replace members and index only when the index and every configured group arrive and parse; a first run
with nothing creates empty tables. The models run in the enrichment unit and every CelesTrak check warns.

**Why.** No state-script or infra change; precedence always sees one snapshot; CelesTrak can never hold positions or
details.

**Rejected.** Files in S3 (infra change); per-group replacement (mixed snapshots); a dbt seed for the config
(breaks the layering rules).

**Consequences.** The index title parser is unverified against the live page until the owner archives it (see the PR).
