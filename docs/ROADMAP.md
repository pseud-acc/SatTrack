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
| 0 | Housekeeping & guardrails | 12 (0.2 done; incl. 0.5, 0.6) | 2–3 |
| 1 | OMM propagation | 8 | 2 |
| 2 | Client data contract + filter spec | 11.5 (incl. 2.4) | 2–3 |
| 3 | Cesium migration | 30 (+25% buffer → ~37) | 6–8 |
| 4 | Freshness & SupGP | 12 | 3 |
| 5 | Detail enrichment | 12 (incl. 5.4) | 2–3 |
| 6 | Natural-language query | 20 (+25% buffer → 25) | 4–5 |
| 7 | Backlog (pick as wanted) | — | — |

Roughly **22 weeks (~114 h, ~5 months)** to the end of Phase 6 with the buffers and the tasks added by the review (93 h as originally written). Phases 4 and 5 are independent of 3 and can be swapped in if Cesium work stalls.

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

---

## Phase 0 — Housekeeping & guardrails (~12 h)

**Goal:** a clean base for agent-driven work.

0.1 `chore/claude-md` — Add `CLAUDE.md` at repo root summarising architecture, commands (`uv sync`, `dbt build`, run app locally, run pipeline locally with a dev profile), and the Working rules above. Commit this roadmap as `docs/ROADMAP.md`.

0.2 `chore/retire-legacy-pipeline` — **Done** in PR #30 (16 Nov 2026): `src/`, `dat/` and root `run_pipeline.py` deleted; the app reads S3 or a local folder (`SATTRACK_APP_DATA_DIR`); CI uses `tests/app_data`.

0.3 `test/app-ci` — Add an app pytest job to the PR and merge checks, running app tests against `tests/app_data`. Without it, 1.4 (parity) and 2.3 (filter spec) would never run in CI.

0.4 `chore/cleanup` — Open clean-up items: Dependabot alerts (app lockfile), archive the two expected IAM Access Analyzer findings, delete stale branches, laptop clean-up (Task Scheduler entry, `SPACETRACK_*` in the local env file, leftover untracked files).

0.5 `test/app-e2e` — A small browser (E2E) test set: Playwright + headless Chromium on the sample, four journeys (home → tracker, 3D draws the selected satellites, one satellite's 2D track, list view), failing on any JS/console error. Checks by counts and rows so they carry over to Cesium; Phase 3 extends them. Runs before each deploy.

0.6 `major/dash-4` — Planned major upgrade: Dash 2.18 → 4.5 (the current release; Dash 3 is skipped), which allows the patched Flask and Werkzeug and clears the last 5 Dependabot alerts (the other 123 were cleared in #45). Upgrade only; new Dash features are separate tasks. Known changes: `app.run_server` becomes `app.run` (`run_app.py`, `run_app_dev.py`); dash-bootstrap-components 1.x → the 2.x release that supports Dash 4 (confirm first); Dash 4's redesigned core components (Dropdown, RangeSlider, Checklist) change how the sidebar looks, so compare screenshots before and after; `dash_table.DataTable` (list view) is deprecated but still works, so it stays; review deprecated component props. The app unit, integration and browser tests are the safety net; check the 3D payload size again (PR #37). About 4.5 h. Do it before Phase 3, which builds the Cesium viewer into the Dash shell.

**Done when:** `CLAUDE.md` exists, legacy code is removed, app unit/integration and E2E tests run in CI, clean-up items closed or listed, the app is on Dash 4.5 with no open Dependabot alerts, CI green.

---

## Phase 1 — OMM propagation (~8 h)

**Why first:** a prerequisite, not an emergency. Space-Track already gives objects above 99,999 TLE lines in Alpha-5 format and the app reads them correctly, but Alpha-5 ends at 339,999, SupGP data for new objects is OMM-only (Phase 4), and the browser propagator reads OMM directly (Phase 3).

1.1 `feature/omm-fields-in-marts` — Carry `mean_motion_dot`, `mean_motion_ddot`, `rev_at_epoch`, `element_set_no`, `ephemeris_type`, `classification_type` from `stg__spacetrack__gp` through `int__spacetrack__satellite_catalogue` into `fct__gp_elements` (tracking). Not into `fct__satellite_master`: since #42 the app export takes elements from the tracking mart, which updates every run, and only descriptive fields from the master, which is held when GCAT enrichment fails. Schema YAML + doc blocks (reused from staging). Keep TLE columns. A warn-level check flags any `ephemeris_type` other than 0 (SGP4).

1.2 `feature/omm-app-export` — In `app__satcat_tle.sql`: add OMM columns; take `mean_motion`/`eccentricity` from columns instead of `substr(tle_line_2, …)`; replace `tle_line_1/2 is not null` filter with a check on the element columns; format epoch explicitly as `%Y-%m-%dT%H:%M:%S.%f`. Add new columns to `APP_COLUMNS["satcat_tle.csv"]` in `export_app_csvs.py`. Update the CI sample `tests/app_data` to the new columns.

1.3 `refactor/omm-propagation` — In `compute_satloc`, build `Satrec` via `sgp4.omm.initialize(Satrec(), fields)` (available in pinned `sgp4>=2.21`). Update callers in `helper__app_data.py` (lines ~111, ~140). Also build the `Satrec` once outside the time loop in the orbit-path branch. Keep a TLE fallback for one release. Building `Satrec` once per satellite also speeds up the 2D/3D callbacks until Cesium replaces them.

1.4 `test/omm-parity` — Test propagating a sample of objects via TLE and via OMM over ±24 h; assert position difference under a small tolerance (expect metres, OMM carries more precision). Include objects above 99,999 (Alpha-5) in the sample. Runs in CI via 0.3.

**Done when:** app runs entirely off OMM fields, parity test passes, no object is dropped for lacking TLE lines.

---

## Phase 2 — Client data contract + filter spec (~11.5 h)

**Goal:** define what the browser receives and how selections are expressed, so Cesium (Phase 3) and NL query (Phase 6) plug into the same contracts.

2.1 `feature/app-data-json` — New export alongside the CSV: a compact JSON (or gzipped JSON) of all exported objects with OMM fields + display fields + `object_type`. Widen scope to include `ROCKET BODY` and `DEBRIS` (flagged so the UI can toggle them). Keep file size in check: short keys, rounded floats, only fields the client needs; put detail-panel fields in a separate file loaded on demand (e.g. per-object or a second JSON). Document the schema in `docs/app-data-contract.md`. **Decide delivery here:** the bucket is private, so serve the JSON from the app (gzip, ETag). Measure dyno memory with ~32,700 objects (each of the 2 workers holds the data; 512 MB) and set a deterministic rule for the ~320 objects of type `UNKNOWN`.

2.2 `feature/filter-spec` — Define a **filter spec** as a JSON Schema (`app/contracts/filter_spec.schema.json`): a list of `{field, op, value}` clauses with an allowlist of fields and ops, generated from dbt schema YAML + `accepted_values` where possible (script in `pipeline/scripts/`). Write a Python function that applies a spec to the app dataframe and refactor the existing sidebar callbacks to build a spec and call it. Behaviour must be unchanged. This is also the NLQ safety boundary in Phase 6, so keep the allowlist strict.

2.3 `test/filter-spec` — Unit tests: each existing sidebar filter → spec → same result set as before. Runs in CI via 0.3.

2.4 `feature/list-view-ag-grid` — Replace the list view's `dash_table.DataTable` (deprecated in Dash 3.3, to be removed in a future major) with AG Grid (`dash[ag-grid]`): virtual scrolling instead of 20-row pages, column filters, built-in CSV export. Keep the export's columns, order, hidden columns and the ±180° longitudes (#41); restyle for the dark theme; update `callback_table.py`, its integration tests and the E2E list journey (which reads table rows). About 3.5 h; independent of 2.1–2.3.

**Order:** run the Cesium spike (3.1) straight after 2.1; it needs only the JSON export, not the filter spec, so the biggest risk is tested early.

**Done when:** sidebar filters run through the spec; JSON export produced by the pipeline; contracts documented.

---

## Phase 3 — Cesium migration (~30 h, plan for ~37 h)

**Goal:** replace Plotly 3D/2D with a CesiumJS viewer, propagating in the browser.

**Architecture decision (task 3.1 confirms it):**
- Keep **Dash** as the shell (sidebar, table, routing).
- Mount Cesium in a `div` from JS in `assets/` (or a small custom Dash component if that proves cleaner). Dash ↔ Cesium communication through `dcc.Store` (selected filter spec / matching IDs, clicked object) and **clientside callbacks**.
- Load CesiumJS from a CDN (keeps the Heroku slug small). Use the imagery bundled with Cesium (e.g. NaturalEarthII) by default so no Cesium ion token is required; make an ion token optional via env var.
- Propagate client-side with **satellite.js**, which creates satellites straight from OMM JSON (`json2satrec`, verified 17 Nov 2026; its recommended route for new apps). Run propagation in a **Web Worker** at ~1 Hz and render with `PointPrimitiveCollection` (not Entities) for 10k–30k objects.
- Use Cesium scene modes for 3D, 2D and Columbus view: one viewer replaces both Plotly tabs.

3.1 `docs/cesium-spike` — Time-boxed spike (≤ 3 h): minimal page rendering all exported objects from the Phase 2 JSON, client-side propagated, measure FPS/CPU with and without debris. Write findings + final architecture in `docs/cesium-architecture.md`. Stop for owner review. Run it straight after 2.1. The spike decides whether debris is shown by default (WebGL on phones with ~30,000 points).

3.2 `feature/cesium-viewer` — Cesium viewer mounted in the visualisation area behind a feature flag (env var), reading the JSON export; points coloured by orbit class / status; play/pause and time multiplier using the Cesium clock.

3.3 `feature/cesium-filters` — Sidebar filter spec → `dcc.Store` → clientside callback that shows/hides points without reloading data.

3.4 `feature/cesium-selection` — Click a point → highlight, draw orbit path (one period, propagated client-side), open detail panel (Dash side, fed by on-demand detail data). Ground track in 2D mode. Keep the current behaviour: the camera survives updates and click-to-track keeps working.

3.5 `feature/cesium-modes` — 3D / 2D / Columbus switch; camera presets (Earth, LEO close-up, GEO belt).

3.6 `refactor/remove-plotly-viz` — Once at parity, remove Plotly 3D/2D callbacks, `dcc.Interval` position refresh and server-side propagation from the request path (keep `compute_satloc` only if still used, e.g. tests). Flip the feature flag default, then remove it. This retires the 3D payload stopgap (PR #37).

**Done when:** Cesium is the only viewer; filters, selection, orbit paths, 2D/3D all work; smooth on a mid-range laptop with payloads + debris; Heroku slug size not materially increased.

---

## Phase 4 — Freshness & SupGP (~12 h)

**Goal:** positions as fresh and accurate as the best free trackers.

4.1 `feature/pipeline-cadence` — Propose (do not apply) a schedule change to several runs per day within Space-Track limits, and a lighter "GP-only" run mode that skips GCAT (GCAT updates ~monthly). Make the app pick up new data **without redeploying** (e.g. app reads the export from S3/HTTPS with cache invalidation keyed on `last_data_update`). Infra changes need owner sign-off. Three changes: the pipeline's 12-hour gate (`--min-hours` in `infra/state/sattrack_state.py`), the EventBridge schedule (`sattrack-scheduler` stack update), and the app reloading `app/current.json` while it runs. GP stays at most once an hour; lower the gate deliberately.

4.2 `feature/supgp-ingest` — Ingest CelesTrak SupGP (OMM JSON) per source group (start with SpaceX, OneWeb, Kuiper, Planet, Iridium, GPS). Respect CelesTrak's usage policy (no more than needed; one fetch per group per run). Design a fetch budget first: CelesTrak enforces download limits on large sets such as Starlink. If a fetch is refused, GP stays the fallback (4.3). Staging model `stg__celestrak__supgp`.

**CelesTrak access risk (Nov 2026).** CelesTrak blocks IP addresses that download more than its usage policy allows; the owner's home IP was blocked after old local scripts (no longer run) fetched too often. Rules for 4.2:
- **Never fetch locally.** SupGP is downloaded only by the pipeline on GitHub Actions. Development and tests use a saved sample file, not live requests.
- **One download per group per CelesTrak update.** Skip a group whose data has not changed since the last run (check the update time first), and use the bulk group files, never one request per satellite.
- **No retries on refusal.** A 403/429 or a tiny/HTML body means "no SupGP this run": record it, keep GP for those objects, don't fail the run.
- **Shared runner IPs.** GitHub-hosted runners share IP addresses with other users, so a block may not be caused by us. Warn (report, not a failed run) only when SupGP has been refused for 3 days in a row; lifting a lasting block needs an email to CelesTrak, which is acceptable because GP keeps the app working without it.

4.3 `feature/element-source-precedence` — Intermediate model choosing one element set per object: SupGP if newer than GP epoch and within a sanity bound of GP, else GP. Add `element_source` (`spacetrack_gp` / `celestrak_supgp:<source>`) and `element_epoch` to `fct__gp_elements` and the export. Note: SupGP can have multiple rows per object (multiple sources/epochs) — pick deterministically and document the rule.

4.4 `feature/freshness-ui` — Show element age and source in the detail panel; optional legend/colour mode by element age.

**Done when:** most active payloads propagate from SupGP; data refreshes several times a day; UI shows age/source.

---

## Phase 5 — Detail enrichment (~10 h)

**Goal:** deep per-object detail, using data already ingested from GCAT where possible.

5.1 `feature/gcat-physical-fields` — (Pipeline-only, no dependency on Cesium: a good task to swap in if Phase 3 stalls.) From GCAT satcat/psatcat: `bus`, `shape`, `length_m`, `diameter_m`, `power`, `payload`, `equipment`, `motor`, design life where available, with precision/uncertainty handling consistent with existing columns. Add to `fct__satellite_master`.

5.2 `feature/detail-panel` — Detail panel sections: identity, mission, ownership (all co-owners with roles), manufacture, launch (vehicle, site with map pin), physical, orbit, data quality (uncertainty flags, sources, element age). Surface uncertainty visibly — this is a differentiator.

5.3 `feature/rollup-views` (optional) — Simple views by owner, manufacturer, bus, constellation that set the filter spec and fly the camera to the selection.

5.4 `feature/satellite-page` — A shareable page per satellite (`/satellite/<id>`) built from the detail panel, linkable from search results and the globe, and indexable by search engines (README planned item "Satellite informational page"). Do it before 5.3.

**Done when:** detail panel covers the fields above with sources/uncertainty shown; each satellite has its own page.

---

## Phase 6 — Natural-language query (~20 h, plan for ~25 h)

**Goal:** "Ask in plain English → see it on the globe", reliable and safe for a public app. The owner has built a self-serve analytics tool before — ask for their learnings at the start of 6.1 and fold them into the design.

6.1 `docs/nlq-design` — Design doc: LLM returns a **filter spec** (Phase 2 schema), never raw SQL. Context = field allowlist + descriptions generated from dbt doc blocks + accepted values. Ambiguity policy (e.g. "Chinese satellites": owner vs manufacturer vs launch site — default + show interpretation, or ask). Model choice (small/cheap: a small, fast model such as Claude Haiku is enough for producing specs), daily spending cap, caching, rate limits per session, server-side API key (Heroku config), prompt-injection considerations.

6.2 `test/nlq-eval-set` — Build ~50 question → expected-satcat-ID-set cases (include ambiguous ones and ones that need SatTrack's multi-org and status data: built in one country/operated by another, co-owned, launched outside owner's country, stopped transmitting but in orbit). Scorer reports precision/recall per case. Run in CI with recorded responses; live runs on demand. Labelling is the expensive part: start with 25 cases and grow the set.

6.3 `feature/nlq-backend` — Endpoint: question → LLM → spec → JSON-Schema validation → (retry once with validation errors) → apply spec. Return spec + interpretation text + counts + uncertainty summary (e.g. "4 matches have uncertain ownership").

6.4 `feature/nlq-ui` — Query box above the sidebar; resulting spec rendered as editable filter chips in the existing sidebar; globe updates via the same store as Phase 3; example prompts.

**Done when:** eval suite ≥ agreed threshold (set in 6.1), costs capped, interpretation always shown and editable.

---

## Phase 7 — Backlog (pick as wanted)

Recommended order: passes first (README planned items; the main feature for people watching from the ground), then element history and radio.

- **7.1 Passes & visibility**: observer location (browser geolocation, opt-in), client-side pass prediction; add standard magnitude (McCants) for visual passes. (~10 h)
- **7.2 Pass export**: a pass list as CSV and as calendar events (`.ics`). README planned item. (~2 h)
- **7.3 Element history**: append-only GP snapshot table (incremental model) → altitude/decay and manoeuvre plots per object. `raw_history` already keeps 90 days of GP in S3 to seed it. (~8 h)
- **7.4 Radio**: SatNOGS DB frequencies/transmitters in the detail panel. SatNOGS DB data is CC BY-SA. (~4 h)
- **7.5 Re-entry**: Space-Track decay/TIP predictions as a "re-entering soon" layer. (~4 h)
- **7.6 Conjunctions**: CelesTrak SOCRATES close approaches visualised between pairs; check CelesTrak's usage policy, show with the conjunction caution. (~8 h)
- **7.7 Deep-space view** (optional): JWST and other L1/L2/lunar/interplanetary craft from JPL Horizons, at a scale where L2 fits (SGP4 can't propagate these). (~8 h)
- **7.8 Operator ephemerides direct** (optional; Starlink files on Space-Track) — only if independence from CelesTrak SupGP is wanted; check licensing before republishing. (~6 h)

---

## Licensing & attribution checklist

- GCAT: CC-BY — cite "data from GCAT (J. McDowell, planet4589.org/space/gcat)" in the app footer/about page.
- Space-Track and CelesTrak: follow their user agreement / usage policy; attribute in the about page.
- Take data only from its original publishers; never republish another tracker's compiled data.
- CesiumJS: Apache 2.0. Cesium ion (if used): check free-tier terms.
- Space-Track fields in public outputs: cite "USSPACECOM via Space-Track.org" and keep the caution that public TLEs must not be used for conjunction assessment.
- CelesTrak SupGP and SOCRATES: CelesTrak's usage policy.
- SatNOGS DB (radio, 7.4): CC BY-SA, attribute.
- Not yet verified: "SupGP covers ~77% of active satellites". Check it before quoting it anywhere public.
