# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## PR Naming Convention

When creating pull requests, use the following prefixes to indicate the type of change:

- **`major/`** - Breaking changes that increment MAJOR version (e.g., `major/python-version-update`)
- **`feature/`** - New features that increment MINOR version (e.g., `feature/satellite-pass-predictor`)
- **`fix/`** - Bug fixes that increment PATCH version (e.g., `fix/csv-export-encoding`)
- **`docs/`** - Documentation updates (no version increment)
- **`refactor/`** - Code refactoring (no version increment unless bug fixes included)
- **`test/`** - Test additions or updates (no version increment)
- **`chore/`** - Maintenance tasks (no version increment)

## [Unreleased]

### Added
- Cesium globe (plan 3.2), behind a feature flag and off by default, so the live site is unchanged: with `SATTRACK_CESIUM_VIEWER=1` the tracker opens on a "Globe (beta)" tab, a CesiumJS globe with Natural Earth imagery showing every payload from `/data/objects.json`, propagated in the browser (satellite.js in a Web Worker, interpolated between samples) and coloured by type with a legend, toggles for rocket bodies and debris, and a "space junk mode" switch for both. Credits for USSPACECOM via Space-Track.org (with the conjunction caution), GCAT, CesiumJS, satellite.js and Natural Earth. CesiumJS 1.147.0 and satellite.js 7.1.0 are self-hosted: pinned with their npm hashes in `vendor/cesium.lock`, fetched and verified at build time by `vendor/fetch.py` (`bin/post_compile`), never committed, served pre-compressed with long-lived caching. No Cesium ion and no third-party requests from the viewer. With the flag on, pages also send a report-only Content-Security-Policy and HSTS. Browser tests check positions against the Python sgp4 library (within 50 m), the performance budget, CSP reports and off-site requests. Decisions D-038, D-041 and D-042
- Constellation field and space station flag (plan 3.8, D-026, D-043): the pipeline downloads CelesTrak's constellation and operator group lists and its "Space Stations" group (21 groups named in its config) at most once a day from GitHub's runners, following CelesTrak's usage policy (CSV, gzip, stop on any non-200, no request for 20 hours after a refusal; D-039). A refused or failed download keeps the last good copy and never fails or holds the run (D-040). Each object in the `objects` dataset gets `constellation`, the group's CelesTrak title without "Operational" (e.g. `Starlink`, `GPS`; null when none; the first group in config order wins), and `flag_space_station` (1 for the ISS and Tiangong modules and the spacecraft CelesTrak lists with them, else 0), and the dataset credits "Constellation groups: CelesTrak (Dr T.S. Kelso)". A check warns when CelesTrak lists a group the config doesn't know
- Filter spec (plan 2.2): the sidebar's filters now run through one JSON contract, `app/contracts/filter_spec.schema.json` (a versioned list of `{field, op, value}` clauses on nine allowed fields, with explicit rules for missing values). The schema is generated from the dbt mart YAML, including a readable label for every field (`config: meta: label:`), and CI fails if it's stale. Shared conformance cases in `tests/contracts/filter_spec_cases.json` hold the Python and (from Phase 3) browser implementations to the same results. What people see in the sidebar is unchanged. The app now needs the `objects` dataset at start-up and stops with a `FATAL` log line without it. Decisions D-030 to D-035
- Browser data file (plan 2.1): the pipeline publishes `objects`, every tracked object (payloads, rocket bodies, debris, and Space-Track's `UNKNOWN` analyst objects) with its full OMM element set and the fields the filters use, as one record per object with the warehouse's field names. The app serves it at `/data/objects.json`: pre-compressed (1.7 MB Brotli, 2.4 MB gzip), with an ETag so a repeat visit downloads nothing. Every record is validated against `app/contracts/objects.schema.json` before publishing. The format and the planned datasets are in `docs/app-data-contract.md`; the reasons in `docs/DECISIONS.md` (D-009 to D-012). Ready for the Cesium viewer (Phase 3)
- App data: `satcat_tle.csv` carries each satellite's full OMM element set from Space-Track GP (`Epoch`, `RaOfAscNode`, `ArgOfPericenter`, `MeanAnomaly`, `Bstar`, `MeanMotionDot`, `MeanMotionDdot`, `RevAtEpoch`, `ElementSetNo`, `EphemerisType`, `ClassificationType`, `ObjectId`, after the existing columns), ready for the app to propagate from OMM (plan 1.3). `MeanMotion`, `Eccentricity` and `Inclination` now come from the element columns at full precision (eccentricity to 8 decimals instead of the TLE's 7; inclination no longer rounded to 2). A satellite is exported when its element set is complete; TLE lines are still required until plan 1.3. The CI sample `tests/app_data` has the same 29 columns
- Pipeline: the tracking table `fct__gp_elements` carries the remaining OMM elements from Space-Track GP (mean motion derivatives, revolution number, element set number, ephemeris type, classification), so the app can propagate from OMM fields instead of TLE lines (plan Phase 1); a warning flags any element set not meant for SGP4
- PR checks (`pr.yml`), required on `main`: a Heroku-identical build and run of the app, and the pipeline's tests and dbt checks
- Deploy on merge (`merge.yml`): the same checks, then a Heroku Build API deploy and live checks when app files changed
- App tests (`tests/app`, CI job `app tests / unit + integration` on PRs and before each deploy): 32 unit tests (positions, coordinates, filters, orbit paths, routing) and 31 integration tests (server, wiring, every callback over HTTP), on the sample with a frozen clock. Two known bugs are marked as expected failures until fixed: longitudes outside ±180° in hover labels and the table, and `dropna()` hiding a satellite with any blank field
- Browser tests (`tests/e2e`, Playwright + headless Chromium, CI job `app e2e / browser journeys` before each deploy): home → tracker, 3D view draws the selected satellites, one satellite's 2D ground track, list view; fail on any JS/console error or failed request to the app. Playwright is a separate `e2e` dependency group, never installed on Heroku
- `SATTRACK_APP_DATA_DIR`: run the app from a local folder of the pipeline's app CSVs; `tests/app_data` holds a small sample

### Changed
- New look (plan 3.12, D-044, in progress): a deep navy theme on Bootstrap 5.3 with the Source Sans 3 font, both self-hosted (no stylesheet or font from another site; Font Awesome replaced by inline icons). A compact top bar shows when the data was last updated; the tracker's views fill the window, with the data credits and the conjunction caution in a footer under them; the view tabs are underlined text tabs
- The app's web server runs 4 threads per worker (gunicorn `--threads 4`), so a slow download of the data file can't hold up other visitors' updates
- Satellite positions are calculated from each satellite's OMM element set (`sgp4.omm.initialize`) instead of its TLE lines, so satellites Space-Track gives no TLE lines for (catalogue numbers above 339,999) can be shown; the pipeline no longer drops them. A file without the OMM columns still works from its TLE lines for one release. Each element set's propagator is built once and reused, so updating the views is faster (all ~19,700 satellites: 188 → 116 ms per update; a 2D ground track: 71 → 42 ms). Satellites with catalogue numbers above 339,999 propagate too (sgp4 can't label them, so they are built with a placeholder number)
- Dash 2.18 → 4.5.1 and dash-bootstrap-components 1.7 → 2.0.4, which brings the patched Flask 3.1.3 and Werkzeug 3.1.9 (the last 5 Dependabot alerts). The sidebar keeps its look: Dash 4's redesigned checklists and launch-year slider are styled to the app's theme. The filter dropdowns now open a panel with a search box and Select all / Deselect all
- Security updates for the app (Dependabot): Pillow 10.4 → 13.0, gunicorn 20.1 → 23.0, urllib3 2.8, requests 2.34, certifi, idna and setuptools; dev tools pytest 9 and black 26. Werkzeug and Flask followed with the Dash 4 upgrade
- 3D view traffic: responses are compressed, hover labels use one shared template, and the 20-second refresh sends only the moved positions (28.7 MB → 0.31 MB per refresh with ~16,000 satellites); labels and click-to-track unchanged
- The app reads only the pipeline's Space-Track + GCAT data (S3 or a local folder) and credits only those sources; with no data source set it stops with an error instead of falling back to GitHub
- Scheduled pipeline runs: the run title in the Actions list shows the trigger, e.g. `sattrack-pipeline (eventbridge)` or `sattrack-pipeline (manual) dry run`, since GitHub labels every dispatch "Manually run by" the owner

### Removed
- The legacy pipeline (`src/`, root `run_pipeline.py`) and its CSVs in `dat/` (CelesTrak, UCS, space.skyrocket); the app no longer reads raw GitHub CSVs

### Fixed
- Latitude and altitude are now geodetic on the WGS 84 ellipsoid, as on maps and other trackers, instead of on a spherical Earth: the 2D map, hover labels and list view could put a satellite up to ~0.19° (about 20 km) off and show its altitude up to ~21 km low at high latitudes (the ISS read ~400 km instead of ~413 km). Checked against wheretheiss.at with the same TLE (now identical) and NASA's ISS ephemeris (about 1 km, SGP4's own accuracy)
- A satellite that decays partway through its plotted orbit no longer breaks the 2D view: points SGP4 can't compute are left out of the path
- A satellite with any blank field (for example an unknown launch mass) was hidden from the views: the app now drops only satellites SGP4 cannot place
- Satellite details stopped updating from 16 Nov because GCAT gave two IDs (F01824, F01834) to two payloads each from the failed Vulcan launch of 15 Nov; the pipeline held back all GCAT details. A repeated ID in GCAT's launch log now keeps its first row in GCAT's file order and is reported as a warning; more than 10 repeated IDs still stop the update
- Satellite positions froze whenever the pipeline held its GCAT enrichment step (as on 17–18 Nov, when GCAT gave two failed-launch Kuiper payloads the same ID): the app export now takes element sets and "Last updated" from the tracking tables, which update every run, and only the descriptive fields from enrichment
- Longitudes in the hover labels, the list view and its CSV export could show values below −180° (down to −405°); they now stay within ±180°. Positions on the 3D globe and the 2D map were already right

## [2.1.0] - 2026-11-15

### Added
- New data pipeline in `pipeline/` (#17): Space-Track GP + GCAT ingestion, dbt models on DuckDB, health report and data summary per run, with its history kept
- AWS infrastructure in `infra/` (CloudFormation stacks, S3 state helper) and workflows for the scheduled pipeline run and the docs site (#17)
- Column documentation site on GitHub Pages: https://pseud-acc.github.io/SatTrack/ (#19 fixed its diagram build)
- `.slugignore`, so `pipeline/` and `infra/` stay out of the Heroku build
- `main` branch ruleset: no force pushes, no branch deletion

### Changed
- App dependencies managed with uv instead of Poetry + `requirements.txt` (#20)
  - Heroku installs from `uv.lock` (`uv sync --locked --no-default-groups`)
  - Only what the app imports, plus gunicorn: dash, dash-bootstrap-components, numpy, pandas, pillow, plotly, sgp4; versions unchanged
  - Heroku slug 275 MB → 111 MB
- Pipeline dependencies managed as a separate uv project, `pipeline/pyproject.toml` + `pipeline/uv.lock`, one group per environment (#21)
- Dependabot covers both uv projects; app updates are minor/patch only, major upgrades are planned separately
- Improved responsive text sizing for better mobile experience
  - Home page stats now use Bootstrap responsive font-size utilities (fs-2 on mobile, fs-md-1 on tablets/desktop)
  - 3D plot annotations now use CSS clamp() for fluid typography (8px-12px range)
- Updated "Launch Tracker" button on home page to link directly to satellite visualization page

### Fixed
- Launch-year filter slider stopped at 2025 while the data runs to 2026; its maximum is now the current year (#23)

### Removed
- Packages the app doesn't import: astropy, beautifulsoup4, dash-vtk/vtk, matplotlib, nltk, openpyxl, unidecode, whitenoise, xlrd (23 packages including their dependencies)
- `requirements.txt`, `sync_dependencies.sh` and the `sync-requirements` workflow (Heroku accepts only one package manager file)

## [2.0.1] - 2025-12-29

### Fixed
- Heroku deployment failure due to multiple package manager files
  - Added `poetry.lock` to `.gitignore` for Heroku compatibility
  - Heroku now uses only `requirements.txt` (auto-synced via GitHub Actions)
  - Poetry remains available for local dependency management

### Changed
- Configured Poetry for local development only
  - `poetry.lock` no longer tracked in git
  - Prevents Heroku buildpack conflicts
- Migrated from `runtime.txt` to `.python-version` (Heroku recommendation)
  - Removed deprecated `runtime.txt`
  - Created `.python-version` with `3.12`

## [2.0.0] - 2025-12-29

### Breaking Changes
- **MAJOR**: Upgraded Python from 3.9 to 3.12
  - Minimum Python version is now 3.12
  - Updated all dependencies to Python 3.12-compatible versions
- **MAJOR**: Upgraded pandas from 1.x to 2.x
  - Fixed pandas 2.x compatibility issues (dict indexing in table display)
- **MAJOR**: Updated core dependencies:
  - numpy: 1.22.3 → 1.26.0+
  - pandas: 1.4.2 → 2.1.0+
  - astropy: 5.0.4 → 6.0.0+
  - Pillow: 9.1.0 → 10.0.0+
  - whitenoise: 5.2.0 → 6.0.0+

### Added
- Poetry dependency management with `pyproject.toml`
  - Replaced requirements.txt-only workflow with Poetry
  - Added `package-mode = false` for application-style projects
  - Development dependencies (pytest, black, flake8, mypy)
  - Code quality tools configuration (black, mypy)
- GitHub Actions workflow for automated requirements.txt synchronization
  - Auto-updates requirements.txt when pyproject.toml or poetry.lock changes
  - Commits changes automatically to PRs via github-actions bot
- Convenience script `sync_dependencies.sh` for local dependency management
  - Install dependencies with Poetry
  - Update requirements.txt locally
  - Show git diff of changes
- Heroku deployment testing documentation
  - Windows-specific testing instructions (Waitress alternative to Gunicorn)
  - Pre-deployment checklist
  - Staging app deployment guide

### Changed
- Updated `runtime.txt` from `python-3.9.21` to `python-3.12`
- Restructured README.md with:
  - Poetry installation instructions (Option 1 - Recommended)
  - Legacy pip installation (Option 2)
  - Dependency management section with automation details
  - Heroku deployment testing section
  - Updated dependency versions in documentation
- Fixed table display helper to use list indexing instead of dict indexing (pandas 2.x compatibility)

### Fixed
- Pandas 2.x compatibility: Changed `dff[dict]` to `dff[list(dict.keys())]` in table display helper
- Python 3.12 compatibility for all dependencies

## [1.0.0] - 2024-12-28

### Added
- Real-time satellite position tracking using TLE data
- 3D visualization of active and inactive satellites
- 3D visualization of satellite orbital paths
- 2D real-time satellite tracker with latitude, longitude, and altitude display
- Interactive filters for satellite visualization
- Tabular export of satellite details and positions to CSV
- Mobile pinch-to-zoom functionality for better mobile user experience
- Filter toggle drop-down interface
- Automated data pipeline pulling from CelesTrak and UCS sources
- Web scrapers and API calls for satellite catalogue and TLE data
- SQLite database for satellite data storage

### Changed
- Refactored layouts and callbacks to enforce modularity
- Updated satellite catalogue and TLE data sources

### Fixed
- Filter toggle drop-down functionality
- Mobile zoom interactions