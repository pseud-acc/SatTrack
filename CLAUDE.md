# CLAUDE.md

Guidance for Claude Code (and anyone else) working in this repo. Keep it short; the READMEs hold the detail.

## What this is

SatTrack (`pseud-acc/SatTrack`, live at https://www.sattrackapp.com) is a free, open-source satellite tracker.
**One repo** holds the app, the pipeline and the infrastructure. Never split it or propose a second repo.

| Path | What | Docs |
|---|---|---|
| `app/`, `run_app.py`, `run_app_dev.py`, `assets/`, `static/`, root `pyproject.toml` + `uv.lock` | Dash + Plotly web app on Heroku (`sattrackapp`, 2 gunicorn workers, 512 MB) | `app/README.md` |
| `pipeline/` | Space-Track GP + GCAT ingestion → dbt on DuckDB → app CSVs. Separate uv project | `pipeline/README.md`, `pipeline/transform/README.md` |
| `infra/` | AWS CloudFormation (`sattrack-core`, `sattrack-scheduler`) and the S3 state helper `infra/state/sattrack_state.py` | `infra/aws/README.md` |
| `.github/` | PR checks, deploy on merge, scheduled pipeline run, docs site | comments at the top of each workflow |
| `tests/app_data/` | 341-row sample of the app CSVs, used locally and in CI | `tests/app_data/README.md` |
| `docs/ROADMAP.md` | The feature roadmap, phases 0–7. Work through it in order unless told otherwise | |
| `docs/DECISIONS.md` | Architecture decisions and why they were made | |
| `docs/architecture.md` | How the pipeline, AWS, GitHub, Heroku and the data publishers connect (diagram) | |

Data flow: EventBridge (daily) → GitHub Actions `pipeline.yml` (OIDC role, Space-Track login from Secrets Manager)
→ `pipeline/run_pipeline.py` → private S3 bucket (`app/` CSVs, warehouse, manifest, logs) → the app reads `app/`
at start-up with a read-only key. No data is ever committed to the repo.

## Commands

App (repo root):

```bash
uv sync                                                        # app + dev tools
SATTRACK_APP_DATA_DIR=tests/app_data uv run python run_app_dev.py   # local, hot reload, sample data
uv lock --check                                                # pyproject.toml and uv.lock in step
uv run pytest tests/app -q                                     # unit + integration (sample data, frozen clock)
uv run --group e2e playwright install chromium                 # once
uv run --group e2e pytest tests/e2e -q                         # browser journeys (offline, headless Chromium)
```

The repo lives in Dropbox, which locks files while uv rewrites them. Keep virtual environments outside it, e.g.
`export UV_PROJECT_ENVIRONMENT="$LOCALAPPDATA/sattrack-venvs/app" UV_LINK_MODE=copy`.

Pipeline (`pipeline/`):

```bash
uv sync                                                        # `pipeline` group: dbt, DuckDB, ingestion
UV_PROJECT_ENVIRONMENT=.venv-bouncer uv sync --only-group bouncer
.venv-bouncer/Scripts/python -m pytest ingestion/tests -q -p no:cacheprovider     # bin/ on Linux
cd transform && ../.venv-bouncer/Scripts/python -m pytest bouncer/tests -q -p no:cacheprovider
.venv-bouncer/Scripts/python -m pytest ../infra/state/tests -q -p no:cacheprovider    # state script (fake S3)
cd transform && uv run dbt parse --profiles-dir . && ../.venv-bouncer/Scripts/dbt-bouncer --config-file bouncer/dbt-bouncer.yml
SATTRACK_DATA_DIR=/path/outside/repo uv run python run_pipeline.py   # a real run: calls Space-Track (see quota)
```

`.github/workflows/pipeline-checks.yml` and `app-build.yml` are the reference for what CI runs.

## Working rules

**Git and review**
- Branch names per `CHANGELOG.md`: `feature/`, `fix/`, `refactor/`, `chore/`, `docs/`, `test/`, `major/`.
  One roadmap task per PR, small enough for a 5-hour week including review.
- `main` is protected: merge only through a PR with the required checks green ("app / Heroku build",
  "pipeline / tests + dbt checks"). No manual Heroku test apps; the CI build is Heroku-identical.
- Merging app files to `main` deploys to Heroku automatically (`merge.yml`). Pipeline-, infra-, test-, CI- and
  docs-only merges don't.
- Add a `CHANGELOG.md` entry under `[Unreleased]` for every user-visible change.
- Commit only verified work. When an assumption turns out wrong, stop and write up options in the PR rather
  than working around it.
- Record every architecture decision in `docs/DECISIONS.md` (context, decision, why, rejected options,
  consequences, evidence) in the PR that makes it. Never rewrite an accepted entry; supersede it with a new one.
- Each decision also gets `docs/decisions/D-NNN-<slug>.md` with the full trade-off analysis (options against planned
  features, evidence, revisit triggers); template in `docs/decisions/README.md`. **Before scoping or building a
  feature, read the records for the components it touches** and raise any "Revisit when" trigger that fires.

**Dependencies**
- uv only. App: root `pyproject.toml`; pipeline: `pipeline/pyproject.toml`. Commit `uv.lock` with its
  `pyproject.toml`. Heroku installs `uv sync --locked --no-default-groups`, so test-only packages go in `dev`.
- App majors (dash, numpy, pandas, plotly, ...) are planned upgrades, not routine Dependabot merges.

**Security and data**
- Never print, log or commit credentials. No credentials in code, the public Actions log or test fixtures.
- Space-Track: GP at most once an hour. Never add loops or retries that could exceed it; keep the login backoff.
- `infra/` and `.github/workflows/`: propose changes in the PR description. Don't deploy or change AWS
  resources, GitHub settings or Heroku config without the owner's explicit go-ahead.
- Actions are pinned to full commit SHAs from the repo's allow-list; workflows use `pull_request`, never
  `pull_request_target`.
- Public outputs carrying Space-Track fields cite "USSPACECOM via Space-Track.org" and keep the caution that
  public TLEs must not be used for conjunction assessment. GCAT (J. McDowell, planet4589.org) is CC-BY: cite it.
  Take data only from its original publishers; never republish another tracker's compiled data. One recorded
  exception (D-026, D-043): CelesTrak's constellation, operator and space station group lists, fetched only by the pipeline (D-008) and
  credited "Constellation groups: CelesTrak (Dr T.S. Kelso)" wherever shown.

**Pipeline design**
- Unattended and deterministic: no hand-maintained lists, manual reviews or rate-limited external lookups.
  Rules come from source data. Unknown values degrade gracefully. A failing build keeps the last good data.
- Nothing the app depends on day to day may need a human more often than every 14 days.

**dbt style** (enforced by dbt-bouncer, `pipeline/transform/bouncer/dbt-bouncer.yml`)
- Staging: one `cte_final` that renames and casts from the source. Intermediate and marts: `cte_<ref'd model>`
  per `ref()` with explicit columns, named transform CTEs, then `cte_final` with `{{ helper__audit_fields() }}`,
  then `select * from cte_final`.
- Write every column out. Never generate column lists or casts from contracts or YAML by macro. Marts cast every
  column explicitly. Contracts and `access: public` on marts only; the committed YAML is the source of truth.
- Leading commas, one item per line, no subqueries in `FROM`/`JOIN`, block-style YAML.
- Names: surrogate keys end `_sk`; yes/no columns are `flag_*` integers 1/0; names describe the content, not
  the transform. App CSV headers stay fixed (the export aliases).
- Every new or changed column gets a schema YAML entry and a doc block. Definitions come from the publisher's
  documentation (GCAT, Space-Track, CelesTrak) and cite it: about 30 words, one or two real examples
  (e.g. the ISS, NORAD 25544), the source field named. Never write definitions from general knowledge.

**Tests**
- Add or extend tests with every change. Anything that changes satellite positions needs a parity test.
- Layers: unit (`tests/app/test_satellite_position.py`, `test_filters.py`: helpers called directly),
  integration (`tests/app/test_app.py`, `test_callback_*.py`: the server and each callback over HTTP), E2E
  (`tests/e2e`: browser journeys). Every callback needs a test (`test_every_callback_has_a_test` enforces it).
- Expected results come from independent code (plain pandas, the sgp4 library), never from the app's helpers.
- Known bugs are strict `xfail`s naming the fix; remove the mark in the PR that fixes it.
