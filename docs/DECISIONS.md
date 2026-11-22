# Architecture decisions

Why SatTrack's components are built the way they are. Each entry records the context, the decision, why it was
made, the options that were rejected and what follows from it. Add an entry in the PR that makes an architecture
decision. Don't rewrite an accepted entry: when a decision changes, add a new one that supersedes it and mark the
old one **Superseded by D-NNN**.

Entries D-001 to D-008 were recorded retrospectively on 22 Nov 2026 from the PRs that made them.

| ID | Decision | Status | Date |
|---|---|---|---|
| [D-001](#d-001-count-the-12-hour-gate-from-the-last-promoted-run) | Count the 12-hour gate from the last promoted run | Accepted | 2026-11-20 |
| [D-002](#d-002-keep-the-first-row-of-a-repeated-gcat-jcat) | Keep the first row of a repeated GCAT JCAT | Accepted | 2026-11-21 |
| [D-003](#d-003-carry-omm-elements-in-the-tracking-mart-only) | Carry OMM elements in the tracking mart only | Accepted | 2026-11-21 |
| [D-004](#d-004-propagate-from-omm-keep-tle-lines-as-a-one-release-fallback) | Propagate from OMM; keep TLE lines as a one-release fallback | Accepted | 2026-11-21 |
| [D-005](#d-005-build-each-propagator-once-per-element-set) | Build each propagator once per element set | Accepted | 2026-11-21 |
| [D-006](#d-006-show-wgs-84-geodetic-latitude-and-altitude) | Show WGS 84 geodetic latitude and altitude | Accepted | 2026-11-22 |
| [D-007](#d-007-stay-on-sgp4-improve-accuracy-through-fresher-elements) | Stay on SGP4; improve accuracy through fresher elements | Accepted | 2026-11-22 |
| [D-008](#d-008-fetch-celestrak-data-only-from-the-pipeline-never-retry-a-refusal) | Fetch CelesTrak data only from the pipeline; never retry a refusal | Accepted | 2026-11-21 |
| [D-009](#d-009-browser-data-file-one-record-per-object-with-the-warehouses-field-names) | Browser data file: one record per object, with the warehouse's field names | Accepted | 2026-11-22 |

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
