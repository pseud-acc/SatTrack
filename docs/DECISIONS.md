# Architecture decisions

Why SatTrack's components are built the way they are. Each entry records the context, the decision, why it was
made, the options that were rejected and what follows from it. Add an entry in the PR that makes an architecture
decision. Don't rewrite an accepted entry: when a decision changes, add a new one that supersedes it and mark the
old one **Superseded by D-NNN**.

Entries D-001 to D-008 were recorded retrospectively on 22 Nov 2026 from the PRs that made them.

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
| [D-037](#d-037-pipeline-warnings-email-a-summary-without-failing-the-run) | Pipeline warnings email a summary without failing the run | Accepted | 2026-11-23 | [record](decisions/D-037-pipeline-warnings-email-without-failing.md) |

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
