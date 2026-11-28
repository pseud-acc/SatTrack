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
| [D-016](#d-016-payloads-by-default-rocket-bodies-and-debris-one-switch-away) | Payloads by default; rocket bodies and debris one switch away | Accepted; amended by D-049 | 2026-11-22 | [record](decisions/D-016-payloads-by-default.md) |
| [D-017](#d-017-colour-by-object-type-with-a-colour-by-menu) | Colour by object type, with a "Colour by" menu | Accepted; default superseded by D-050 | 2026-11-22 | [record](decisions/D-017-colour-by-type.md) |
| [D-018](#d-018-three-information-tiers-hover-click-panel-full-record) | Three information tiers: hover, click panel, full record | Accepted | 2026-11-22 | [record](decisions/D-018-three-information-tiers.md) |
| [D-019](#d-019-single-selection-with-per-satellite-toggles) | Single selection with per-satellite toggles | Accepted | 2026-11-22 | [record](decisions/D-019-single-selection-toggles.md) |
| [D-020](#d-020-time-scrubber-of-1-day) | Time scrubber of ±1 day | Accepted | 2026-11-22 | [record](decisions/D-020-time-scrubber-one-day.md) |
| [D-021](#d-021-one-viewer-for-3d-2d-and-columbus-retire-the-plotly-2d-tab) | One viewer for 3D, 2D and Columbus; retire the Plotly 2D tab | Accepted | 2026-11-22 | [record](decisions/D-021-one-viewer-retire-plotly-2d.md) |
| [D-022](#d-022-natural-colour-earth-from-self-hosted-imagery) | Natural-colour Earth from self-hosted imagery | Provisional; point outline updated by D-050 | 2026-11-22 | [record](decisions/D-022-natural-colour-earth.md) |
| [D-023](#d-023-label-the-selected-satellite-and-close-up-the-nearest-20) | Label the selected satellite and, close up, the nearest 20 | Accepted | 2026-11-22 | [record](decisions/D-023-labels-selected-and-nearest.md) |
| [D-024](#d-024-shareable-links-carry-the-core-view-in-the-url-hash) | Shareable links carry the core view in the URL hash | Accepted | 2026-11-22 | [record](decisions/D-024-shareable-links-url-hash.md) |
| [D-025](#d-025-bottom-sheet-on-phones) | Bottom sheet on phones | Accepted | 2026-11-22 | [record](decisions/D-025-mobile-bottom-sheet.md) |
| [D-026](#d-026-constellations-from-celestraks-group-lists-credited) | Constellations from CelesTrak's group lists, credited | Accepted; partly superseded by D-043; amended by D-046; `constellation` field and operator groups superseded by D-047 | 2026-11-22 | [record](decisions/D-026-constellations-from-celestrak-groups.md) |
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
| [D-038](#d-038-fetch-the-self-hosted-viewer-files-in-the-buildpacks-binpost_compile-hook) | Fetch the self-hosted viewer files in the buildpack's `bin/post_compile` hook | Accepted | 2026-11-24 | [record](decisions/D-038-vendor-fetch-in-post-compile-hook.md) |
| [D-039](#d-039-celestrak-groups-at-most-once-a-day-and-no-request-for-20-hours-after-a-refusal) | CelesTrak groups: at most once a day, and no request for 20 hours after a refusal | Accepted | 2026-11-23 | [record](decisions/D-039-celestrak-group-fetch-cadence.md) |
| [D-040](#d-040-celestrak-groups-raw-tables-in-the-warehouse-replaced-all-or-nothing-never-holding-a-unit) | CelesTrak groups: raw tables in the warehouse, replaced all or nothing, never holding a unit | Accepted | 2026-11-23 | [record](decisions/D-040-celestrak-groups-storage-and-failure.md) |
| [D-041](#d-041-security-headers-ship-with-the-viewer-flag-cesium-needs-a-decision-before-the-csp-is-enforced) | Security headers ship with the viewer flag; Cesium needs a decision before the CSP is enforced | Accepted | 2026-11-24 | [record](decisions/D-041-security-headers-report-only.md) |
| [D-042](#d-042-ci-checks-the-viewers-start-up-with-fixed-budgets-and-a-same-runner-comparison-against-the-target-branch) | CI checks the viewer's start-up with fixed budgets and a same-runner comparison against the target branch | Accepted | 2026-11-24 | [record](decisions/D-042-ci-first-positions-threshold.md) |
| [D-043](#d-043-flag-space-stations-from-celestraks-stations-group) | Flag space stations from CelesTrak's `stations` group | Accepted | 2026-11-24 | [record](decisions/D-043-space-station-flag-from-celestrak.md) |
| [D-044](#d-044-app-design-direction-deep-navy-left-filter-panel-own-design-tokens-on-plain-bootstrap-5) | App design direction: deep navy, left filter panel, own design tokens on plain Bootstrap 5 | Accepted | 2026-11-24 | [record](decisions/D-044-app-design-direction.md) |
| [D-045](#d-045-colour-by-menu-gets-its-own-task-straight-after-33) | "Colour by" menu gets its own task straight after 3.3 | Accepted | 2026-11-24 | [record](decisions/D-045-colour-by-menu-own-task.md) |
| [D-046](#d-046-tdrss-keeps-only-relay-satellites-constellation-membership-checked-against-names) | TDRSS keeps only relay satellites; constellation membership checked against names | Accepted; amended by D-047 | 2026-11-24 | [record](decisions/D-046-tdrss-relay-satellites-and-name-check.md) |
| [D-047](#d-047-constellations-and-satellite-systems-celestrak-first-completed-from-gcat) | Constellations and satellite systems: CelesTrak first, completed from GCAT | Accepted | 2026-11-25 | [record](decisions/D-047-constellations-and-satellite-systems.md) |
| [D-048](#d-048-one-filter-spec-store-drives-every-view-the-browser-filters-in-the-worker) | One filter-spec store drives every view; the browser filters in the worker | Accepted | 2026-11-26 | [record](decisions/D-048-one-filter-spec-store-drives-every-view.md) |
| [D-049](#d-049-the-tracker-opens-on-every-active-satellite-space-junk-mode-adds-inactive) | The tracker opens on every active satellite; Space junk mode adds Inactive | Accepted | 2026-11-26 | [record](decisions/D-049-tracker-defaults-active-satellites-junk-mode-adds-inactive.md) |
| [D-050](#d-050-the-globe-is-coloured-by-status-by-default-with-no-point-outline) | The globe is coloured by status by default, with no point outline | Accepted | 2026-11-26 | [record](decisions/D-050-globe-coloured-by-status-no-outline.md) |
| [D-051](#d-051-the-filter-panel-shows-its-own-state-count-segments-rows-and-chips) | The filter panel shows its own state: count, segments, rows and chips | Accepted | 2026-11-26 | [record](decisions/D-051-filter-panel-behaviour.md) |

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
**Status:** Accepted, 2026-11-22 (plan 3.1); partly superseded by D-043 (the `stations` group is downloaded as a flag); amended by D-046 (`tdrss` counts only members named TDRS); the `constellation` field and the operator groups superseded by D-047. **Component:** pipeline; the `objects` dataset; the viewer's credits.

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

## D-038 Fetch the self-hosted viewer files in the buildpack's `bin/post_compile` hook
**Status:** Accepted, 2026-11-24 (owner, after comparing the process flows of each option). **Component:** the Heroku build and CI's Heroku-identical build.

**Context.** D-014 has the builds download, verify and extract Cesium and satellite.js but not how a build runs the
script. The pinned classic `heroku/python` buildpack (v362) runs an app's `bin/post_compile` after installing the
dependencies with uv, from the app root, with the app's Python on `PATH` and `CACHE_DIR` set; a non-zero exit fails
the build.

**Decision.** `bin/post_compile` runs `python vendor/fetch.py --cache "$CACHE_DIR/sattrack-vendor"`: npm registry only,
sha512 checked against `vendor/cesium.lock`, listed files only, pre-compressed copies, a manifest of SHA-256s. The app
re-verifies the manifest at start-up and leaves the viewer off if anything differs.

**Why.** Supported by the pinned buildpack with uv; no Heroku config change; CI's build check runs it unchanged.

**Rejected.** A second (Node) buildpack (config change, npm toolchain); fetching at start-up (runtime registry
dependency); release phase (files don't reach the slug); committing the files (D-014).

**Consequences.** About +6.8 MB of compressed slug (limit 15 MB, enforced by the build check). A registry outage fails
a build and the live release stays.

## D-039 CelesTrak groups: at most once a day, and no request for 20 hours after a refusal
**Status:** Accepted, 2026-11-23. **Component:** `sattrack_ingest/celestrak_groups.py` and
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
**Status:** Accepted, 2026-11-23. **Component:** `raw_celestrak`, the `celestrak` dbt source,
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

**Consequences.** The index title parser is tested on a trimmed copy of the live page (23 Nov 2026, run 45099334610).

## D-041 Security headers ship with the viewer flag; Cesium needs a decision before the CSP is enforced
**Status:** Accepted, 2026-11-24 (owner; B chosen after a prototype). **Component:** response headers
(`app/core/viewer.py`) and `vendor/cesium.lock`.

**Context.** 3.2 asks for a report-only CSP (`'self'`, `worker-src 'self'`, no `'wasm-unsafe-eval'`) and HSTS. The
page shell already loads Google Analytics, the Bootswatch theme, Font Awesome, Google Fonts and (2D tab) USGS tiles.
Measured: Cesium 1.147.0 compiles five WebAssembly modules and runs `(0,eval)("this")` as it loads; under an enforced
policy without `'unsafe-eval'` Cesium doesn't load.

**Decision.** With `SATTRACK_CESIUM_VIEWER` on only: `Content-Security-Policy-Report-Only` (same origin, inline scripts
by hash, the shell's existing third parties listed, `'wasm-unsafe-eval'`, never `'unsafe-eval'`) and
`Strict-Transport-Security: max-age=86400` (no subdomains, no preload). Cesium's one `(0,eval)("this")` is patched to
`globalThis` at vendoring (a `[[package.patch]]` in the lock; the build fails unless it matches exactly once). The
policy is enforced at roadmap 3.6, when Plotly's `blob:` workers go.

**Why.** Production unchanged until the flag flips; report-only can't break a page; a one-day HSTS is reversible.

**Rejected.** Headers on every page now (changes production in a flag-off release); allowing `'unsafe-eval'`
(weaker for every script; the patch works: prototype 24 Nov); enforcing before 3.6 (breaks the Plotly 2D map).

**Consequences.** Browser tests fail on any CSP violation except the Plotly map's `blob:` workers (removed in 3.6).
Each Cesium upgrade re-checks the patch; 3.7 lists the patched file in the notices.

## D-042 CI checks the viewer's start-up with fixed budgets and a same-runner comparison against the target branch
**Status:** Accepted, 2026-11-24 (owner). **Component:** `tests/e2e/test_viewer.py`, `.github/workflows/app-e2e.yml`.

**Context.** D-027: first positions <= 1.5 s on the reference laptop, checked in CI. GitHub's runners render the globe in
software on the CPUs the worker needs (CI 1.40-1.98 s, laptop 0.84-1.48 s), so raw time on a runner is a weak signal;
a fixed 3.0 s limit would let start-up degrade by up to 50% unseen.

**Decision.** Fixed budgets that don't depend on runner speed (bytes before first positions <= 5 MB, only the shown
types' records built first, heap <= 80 MB, main thread <= 5 ms a frame, first positions <= 3.0 s as a backstop), plus,
on pull requests, three cold visits each to this branch and the target branch (checked out by CI), interleaved on the
same runner and compared phase by phase: a phase fails when over 20% and over 150 ms slower. Both tables go to the
job summary. 1.5 s stays the laptop release check.

**Why.** Runner speed cancels out in the comparison, the fixed budgets catch extra work and downloads directly, and a
failure names the phase.

**Rejected.** 3.0 s alone (drift unseen); 1.5 s in CI (flaky); warn only (ignorable); a calibration benchmark
(approximate); two workers (optimises for CI).

**Consequences.** ~2 minutes more CI on pull requests. #70 has no baseline (main has no viewer). Issue #72: anchored
baseline for gradual drift, data-growth checks, #70's laptop figures as the first anchor.

## D-043 Flag space stations from CelesTrak's `stations` group
**Status:** Accepted, 2026-11-24 (owner). Partly supersedes D-026 ("every other group is excluded"). **Component:**
pipeline (`sattrack_ingest/config.py`, `int__celestrak__space_station`, `fct__satellite_master`); the `objects` dataset.

**Context.** D-026 excludes CelesTrak's "Space Stations" group (`stations`: the ISS and Tiangong modules and the
spacecraft visiting them, 17 objects on 22 Nov 2026). The owner wants it.

**Decision.** Download `stations` with the other included groups, as its own kind `station`, and add
`flag_space_station` (integer 1/0, never null) to `fct__satellite_master` and the `objects` dataset. Station groups
never name a constellation.

**Why.** The constellation field keeps its meaning, and the flag works whatever the colour mode (labels, search, a
filter later).

**Rejected.** `stations` as a constellation value (mixes the two; a docked Dragon would be a "constellation"); a later
separate PR (a second contract change).

**Consequences.** One more CelesTrak request per download; a new required field in `objects.schema.json`.

## D-044 App design direction: deep navy, left filter panel, own design tokens on plain Bootstrap 5
**Status:** Accepted, 2026-11-24 (owner, from mock-ups of three looks, three filter layouts and three build
approaches). **Component:** every app page: the Dash shell, the tracker's filter panel and the viewer's chrome.

**Context.** The viewer (3.2) and its filters (3.3) are about to go into the Dash shell. An audit of the live site on
24 Nov found two Bootstrap versions on every page (Dash auto-loads `assets/bootstrap.css` and `bootstrap.min.css`, an
old Bootstrap 4.5 Cyborg build, beside `dbc.themes.CYBORG`, Bootstrap 5.3 from the jsDelivr CDN), five accent colours,
white inputs on black, inline font sizes in Python, a header pushing the viewer down ~240 px (globe 958 × 530 px in a
1366 × 900 window, from Plotly's `calc(70vh - 100px)`), and filters with no match count.

**Decision.** Look B "Deep navy": blue-black chrome, one teal accent `#2bb3a3` kept clear of the data colours (payloads
`#56B4E9`, rocket bodies `#E69F00`, debris `#CC79A7`, D-017), 6 px corners, hairline borders, no card shadows. Filters
F1: a left panel, collapsible to a thin strip, with a live match count, changes applied at once, type toggles with
swatches and counts, segmented status and orbit controls, "More filters" rows showing their value, active-filter chips
with "Clear all", and no "Clear Orbits" (D-019); phones keep the bottom sheet (D-025). Any satellite search offers a
browsable list as well as typing (users include children and casual visitors; PR #73 closed). Build: plain Bootstrap 5
plus SatTrack's own `tokens.css` (colours, type scale, spacing, radius) shared by the shell and the viewer; remove the
two `assets/` Bootstrap files and `dbc.themes.CYBORG`; commit Bootstrap 5.3's CSS and the font under `assets/`, each
pinned by a SHA-256 unit test; inline SVGs replace Font Awesome. Tokens (`--st-*`, full table in the record): Source Sans
3, 15 px app base and 16 px reading text, type sizes 12–28 px, 4 px spacing steps, text and accent at least 6.3:1 on the
panel, `#04201c` text on teal. A new task 3.12 before 3.3 (~8–10 h), which also makes the globe fill the window below a
compact top bar, with a full-screen button.

**Why.** One accent can't be mistaken for data; a left panel has room for the filters phases 4–6 add without covering
the globe; one Bootstrap and one tokens file end the conflicts and give the viewer the same colours as the shell.

**Rejected.** Look A neutral graphite and C light shell (two themes to maintain); filters F2 floating on the globe
(covers it) and F3 top bar (crowds as filters grow); keeping Cyborg and overriding it (keeps the conflict and
`!important` chains); another component library such as Mantine (rewrites every layout); an empty type-to-search box;
fonts Inter and IBM Plex Sans; a 14 px app base; fetching the CSS and font through `vendor/cesium.lock` (with the
viewer flag off the app reads no vendor files); self-hosting Font Awesome or keeping its CDN.

**Consequences.** Phase 3 grows by ~10–12 h (3.12, and 3.3 from ~4 h to ~6 h). Every page changes look in one release.
The CSP drops the theme, font and icon hosts (D-041 option E). ~330 KB of committed CSS and font, upgraded by hand.

## D-045 "Colour by" menu gets its own task straight after 3.3
**Status:** Accepted, 2026-11-24 (owner). **Component:** roadmap Phase 3 (the viewer's "Colour by" menu and legend).

**Context.** D-017 asks for a "Colour by" menu (orbit class, status, owner, constellation), but only the constellation
option was scheduled (3.10).

**Decision.** A new task, 3.13 `feature/cesium-colour-by` (~3 h), straight after 3.3: the menu and legend with object
type (default), orbit class, status and owner. 3.10 then adds constellation to it.

**Why.** The core ships the menu D-017 asks for, in the 3.3 panel's look, as a PR small enough for one week.

**Rejected.** Folding it into 3.10 (an extension; ties the menu to CelesTrak work); folding it into 3.3 (too big for
one week).

**Consequences.** Phase 3 core grows by ~3 h; 3.10 depends on 3.13.

## D-046 TDRSS keeps only relay satellites; constellation membership checked against names
**Status:** Accepted, 2026-11-24 (owner); amended by D-047 (no prefix is needed any more, the dmc exception is gone, and the name check
excludes members of system groups). Amends D-026 (membership is the group's CSV, except for groups with a
member-name prefix). **Component:** pipeline (`sattrack_ingest/config.py`, `stg__celestrak__group_config`,
`int__celestrak__satellite_constellation`, a warning check); `constellation` values in the `objects` dataset.

**Context.** CelesTrak's `tdrss` group ("Tracking and Data Relay Satellite System (TDRSS)") lists the 8 TDRS relay
satellites and 17 spacecraft that use them (HST, ISS (ZARYA), TERRA, AQUA, MMS 1-4, NOAA 20, ...; fetch run
45061938995), so the first run with #69 gave those 17 the TDRSS constellation. An audit of all 20 constellation and
operator groups found no other group mixing in other spacecraft.

**Decision.** The config gives a group an optional member-name prefix (`CELESTRAK_MEMBER_NAME_PREFIX`; only
`tdrss`: `TDRS`), landed in `raw_celestrak.group_config` and staged as `celestrak_group_member_name_prefix`; the
intermediate model counts a member of such a group only when its CelesTrak `OBJECT_NAME` starts with the prefix. A
warning check (D-037) flags constellation memberships whose name lacks the group's prefix, else the group's most
common leading word, and a prefix that matches no member. Operator groups are not name-checked. The check's
exceptions (owner, 24 Nov 2026) live in one logic macro, `helper__flag_member_name_fits_group`, a `case when` with one
branch each: dmc is not checked (CelesTrak's "Disaster Monitoring" group spans several programmes; its 5 non-DMC
members keep the constellation), and hulianwang also accepts names starting GUOWANG. Remove the GUOWANG branch when
Space-Track renames those objects; revisit dmc if CelesTrak narrows the group.

**Why.** The owner keeps TDRSS but only for the relay satellites; one config entry, visible in the warehouse, is
deterministic and needs no list of NORAD ids. The data-derived leading word handles COSMOS (GLONASS) and GSAT
(Galileo) without exceptions.

**Rejected.** Dropping `tdrss` (the owner wants it); a hand list of the 17 NORAD ids (goes stale); the title's first
word as the check's expected string (76 warnings today and a list of exceptions); checking operator groups (~125
warnings on legitimate fleet names); accepting 13 known warnings a day (they would hide new ones).

**Consequences.** 17 objects lose the TDRSS name at the next CelesTrak download; no contract change. With the macro's
exceptions the check is quiet on today's data (it would otherwise warn on 8 GUOWANG-30 objects and 5 dmc members);
dmc is not name-checked while its exception stands.

## D-047 Constellations and satellite systems: CelesTrak first, completed from GCAT
**Status:** Accepted, 2026-11-25 (owner). Supersedes D-026's `constellation` field and its operator groups; amends
D-046. **Component:** pipeline (config, the ad-hoc seed `manual_satellite_grouping`, the constellation and system
models, `dim__satellite_constellation`, `dim__satellite_system`, `fct__satellite_system`, `fct__satellite_master`); the
`objects` dataset (schema 2). Record: [D-047](decisions/D-047-constellations-and-satellite-systems.md).

**Context.** `constellation` mixed constellations (Starlink), systems (GPS, TDRSS) and operator fleets (SES). The
owner's definitions: a constellation is near-identical satellites working together; a system is non-identical
satellites working together, and a satellite can belong to several.

**Decision.** Three fields replace `constellation`: `satellite_constellation_name`, `primary_satellite_system_name`,
`satellite_system_names` (primary first). CelesTrak is the golden source: constellations are its constellation groups;
systems are its system groups, keeping members whose names fit the group (exclusion) and completed with every own GCAT
payload sharing a kept member's programme family; `sarsat` gives hosted Cospas-Sarsat memberships; `sbas` is an
umbrella term whose members name their system before "/PRN" (EGNOS, WAAS, GAGAN, SDCM, SOUTHPAN). An ad-hoc seed holds
the few CelesTrak lacks, each with its publisher's quote: PlanetScope, Sentinel-1/2/3; NavIC, QZSS, JPSS, GOES,
Copernicus Sentinels; hosted MSAS and BDSBAS (GPS.gov PRN register). `gnss` and the operator groups are not downloaded.
Accepted-values warnings flag new names.

**Why.** The owner's rule (25 Nov 2026): the publisher's grouping first, no hand-maintained list beyond a handful of
sourced rows, deterministic SQL, new values flagged by tests. GCAT keeps retired members a CelesTrak list drops.

**Rejected.** A seed of every grouping (drifts; owner rejected it); systems from GCAT alone (no system field); systems
split from CelesTrak's `gnss` (it lists SBAS hosts; GNSS is an umbrella term); one "SBAS" system (also an umbrella term).

**Consequences.** `objects` schema 1 → 2. 17 CelesTrak groups downloaded instead of 21. System names are CelesTrak's
titles. Dev build on 21 Nov data: GPS 80 (37 active), GLONASS 142, Galileo 33, BeiDou 63, TDRSS 12, DMC 12, Starlink
11,203, PlanetScope 120.

## D-048 One filter-spec store drives every view; the browser filters in the worker
**Status:** Accepted, 2026-11-26 (owner's 3.3 answers of 24 Nov 2026; built in 3.3a). **Component:** the filter panel,
the Cesium viewer and worker, the Plotly 3D/2D and list callbacks. Record:
[D-048](decisions/D-048-one-filter-spec-store-drives-every-view.md).

**Decision.** A page-level `filter-spec` store, built and validated in Python from the panel's controls and rendered
with the starting spec, is the one input of the globe (through the clientside bridge), Plotly 3D, 2D and the list.
Object types are panel switches and an `object_type` clause; the globe's overlay toggles go. The browser's
`static/viewer/filter_spec.js` (no imports, no eval; rules generated from the schema) runs in the worker, which masks
its records without reloading; it passes the shared conformance cases in Chromium. Q8 (search S2), Q4 (server count),
Q9 (flag via config var at the end of 3.3b), Q10 (Clear Orbits into Plotly 3D) are for 3.3b.

**Why.** One spec builder; every view agrees; filtering off the main thread; no data reload; D-042 unchanged.

**Rejected.** A JavaScript spec builder (no conformance cases); eight inputs per Plotly callback; main-thread
filtering; Ajv (needs `new Function`, blocked by D-041's policy).

## D-049 The tracker opens on every active satellite; Space junk mode adds Inactive
**Status:** Accepted, 2026-11-26 (owner). Amends D-016; replaces the 24 Nov 3.3 answer Q1. Record:
[D-049](decisions/D-049-tracker-defaults-active-satellites-junk-mode-adds-inactive.md).

**Decision.** Opens on status Active, every orbit class, payloads, the whole launch-year range (16,576 objects on the
21 Nov data). Space junk mode on also ticks Inactive and off restores the status, because almost all rocket bodies
and debris are Inactive (all but 6 of 12,398); a note under the type switches says so.

**Rejected.** Active + LEO + GEO (hides the MEO navigation systems); all payloads in any status (24 Nov Q1);
status for payloads only (OR across fields, D-031's version-2 trigger).

## D-050 The globe is coloured by status by default, with no point outline
**Status:** Accepted, 2026-11-26 (owner's choice of 24 Nov 2026; built in 3.3a). Supersedes D-017's default; updates
D-022's provisional outline. Record: [D-050](decisions/D-050-globe-coloured-by-status-no-outline.md).

**Decision.** Points take `--st-active` (soft red) and `--st-inactive` (grey) from the design tokens, with no
outline. Colour by type becomes an option of 3.13's "Colour by" menu.

## D-051 The filter panel shows its own state: count, segments, rows and chips
**Status:** Accepted, 2026-11-26 (owner's 3.3 answers of 24 Nov 2026; details built in 3.3b). **Component:** the filter
panel. Record: [D-051](decisions/D-051-filter-panel-behaviour.md).

**Decision.** One server callback turns the panel's control values (through the spec's own builder) into the live
count, "matching / total" per type, zero-match hints, chips and "More filters" summaries. Status is one choice
(Active / Inactive / All); orbit any combination. A chip's remove button widens its control; the type chip has none;
"Clear all" restores the opening values (D-049). "More filters" rows are native `<details>`. One callback owns chip
removal, Clear all and junk mode. No Update button; search lists set once (Q8 S2); Clear orbits in the Plotly 3D tab.

**Why.** The count can't disagree with the spec; nothing runs at load; no callback per row; no property set twice.

**Rejected.** Summaries from the `filter-spec` store (empty when no type or orbit is on); chips that reset to the
default; collapse components with a callback per row.

## D-052 The globe goes on in production now, Plotly 3D goes, and the tracker is made usable on phones
**Status:** Accepted, 2026-11-27 (owner, after #84 went live and the tracker was close to unusable on a phone).
**Component:** the tracker page, the Cesium viewer, the filter panel, search. Record:
[D-052](decisions/D-052-globe-on-and-usable-on-phones.md).

**Decision.** The globe is on unless `SATTRACK_CESIUM_VIEWER` switches it off (kept as an off switch until 3.6);
Plotly 3D is removed; only the open tab holds a view (the 2D map built on open, the list not re-sent unchanged).
Search is a browsable list drawn in the page from `/data/search.json`, derived by the app from the objects dataset
(stations first, newest launches first; type to narrow), replacing both dropdowns. Filters open in the browser. The
globe draws on demand (request-render mode, ~4 draws a second untouched), with a dimmed Earth (the owner's "shade 2"),
a navy base colour, 3 px distance-scaled dots in a darker red (#e8564a), hover/tap labels (3.4's first tier) and a
loading bar rendered with the page in `div#globe` (amends D-013's empty div). The panel's type swatches give way to an
Active/Inactive key.

**Why.** Measured on full data at phone size with a 4x-slowed CPU: the main thread was busy 98% of the time (every
frame drawn, every tab rendered), the dropdowns cost 5 s, a filter change took 5.7 s and opening Filters 2.5 s;
after: 32%, 0.2 s, 1.1-1.5 s and 0.8-0.9 s. A Plotly zoom fix was tried and dropped (little effect at full scale).

**Rejected.** Keeping Plotly 3D beside the globe (keeps the slowest view); more Plotly fixes (redraw cost of ~16,600
points); type-only search (owner rejected in #73); full dropdown lists loaded on first open (still freezes on a phone).


## D-053 Rocket bodies and debris are always Inactive
**Status:** Accepted, 2026-11-27 (owner). Updates D-049's note. Record:
[D-053](decisions/D-053-rocket-bodies-and-debris-always-inactive.md).

**Decision.** In `fct__satellite_master`, Space-Track's `ROCKET BODY` and `DEBRIS` objects are always
`operational_status = 'Inactive'`; where GCAT had said Active, `operational_status_source` is
`space_track_object_type`. The panel note says "always" instead of "almost all".

**Why.** Status came from GCAT only and fell through to its current catalog for non-payloads, making 6 of 12,398
rocket bodies and debris Active (26 Nov data). One deterministic rule; no manual list.

**Rejected.** Keeping GCAT's status (junk shown as working satellites); a manual exceptions list (breaks the
unattended pipeline rule).

## D-054 Selecting a satellite: a sourced detail panel, the object_detail file, and search that follows the filters
**Status:** Accepted, 2026-11-28 (owner, after trying each part on a laptop and a phone). Updates D-010, D-018, D-019,
D-024 and D-052. Record: [D-054](decisions/D-054-selection-panel-and-object-detail.md).

**Decision.** A click, tap, search pick or shared link (`#v=1&sat=25544`) selects one object: a ring and name label,
and a panel with a plain headline (status with operating/transmitting dates, owner, operator, manufacturer, live
height with orbit type, speed, GEO longitude, launch, constellation count; exact values only) and "More details"
sections that each show their source and date, with uncertainty marked in place. Link and Cite copy a share link and
a citation; Orbit, Ground track and Follow toggles; "–" minimises to a pill, "×" clears. On phones a small card that
expands and drags, its top always in view. The details come from a new `object_detail` dataset (same keys as
`objects`), fetched once by the worker on the first selection: 0.72 MB Brotli on 28 Nov 2026. On the globe a search
pick selects and flies without changing the filters (an object the filters hide is pinned); browsing the search list
shows what the filters show, typing finds the rest under "Hidden by your filters", and group headings with jump links
reach the debris in one tap.

**Why.** Two audiences (children and casual visitors; analysts and journalists who need facts they can cite); every
UX choice tried by the owner on a phone first. The whole-file fetch reuses D-012's delivery and keeps the server's
memory flat; a per-object route would make each worker hold ~33k parsed records.

**Rejected.** A per-object route; comparisons ("as heavy as 3 cars"); the full card at once on phones; an unlabelled
"Clear"-only control; the search list following the filters strictly; type buttons inside the search; junk first in
junk mode.
