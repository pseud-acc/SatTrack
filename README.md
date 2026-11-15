# SatTrack

**Version:** 2.0.1

## Description

This repository contains python scripts to run the SatTrack App - an open-source real-time satellite tracking app - for visualising active and inactive satellites orbiting the Earth. The latest version of the app is hosted at [https://sattrackapp.herokuapp.com/](https://sattrackapp.herokuapp.com/).

The project consists of two parts - (1) data pipeline; (2) interactive app. In the data pipeline, satellite catalogue and TLE data is pulled from CelesTrak, UCS (Union of Concerned Scientists) and space.skyrocket via web scrapers and API calls into a SQLite database. The interactive app is a Dash app (which can be hosted on Heroku) in which satellite TLE data is converted into a real-time satellite position and satellite catalogue data is used to filter 2d and 3d visualisations. The app also allows satellite position data to be exported in tabular form (to a csv).

## Pipeline/App Features

- Checks CelesTrak and UCS webpages for most recent update
- Downloads satellite catalogue and TLE data from CelesTrak website
- Downloads satellite catalogue data from UCS website
- 3D visualisation of (current) active/inactive satellite positions
- 3D visualisation of satellite orbital path
- 2D real-time satellite tracker (shows latitude, longitude and altitude)
- Tabular export (to csv) of satellite details and position

## Requirements

### Python Version
- Python 3.12 or higher

### Dependencies
Key dependencies (see [pyproject.toml](pyproject.toml) for full list):
- Dash 2.12.1
- Plotly 5.7.0
- Dash Bootstrap Components 1.1.0
- Astropy 5.0.4
- NumPy 1.22.3
- Pandas 1.4.2
- SGP4 2.21

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. The app (repo root) and the
data pipeline (`pipeline/`) are separate uv projects, each with its own `pyproject.toml` and `uv.lock`, so the
Heroku app only ever installs the app's own dependencies.

1. Clone the repository:
   ```bash
   git clone https://github.com/pseud-acc/SatTrack.git
   cd SatTrack
   ```

2. Install uv if you haven't already (see https://docs.astral.sh/uv/getting-started/installation/), e.g.:
   ```bash
   winget install --id=astral-sh.uv -e   # Windows
   ```

3. Create the virtual environment (`.venv/`) with the locked app dependencies and the dev tools:
   ```bash
   uv sync
   ```

## Dependency Management

`pyproject.toml` lists what the app imports, plus gunicorn (the Procfile's web server). `uv.lock` pins
every package, with hashes. Heroku detects `uv.lock` and installs from it with
`uv sync --locked --no-default-groups`, i.e. the app dependencies only, never the `dev` group.

### Updating Dependencies

```bash
uv add <package>            # add an app dependency (updates pyproject.toml and uv.lock)
uv add --dev <package>      # add a dev-only tool (pytest, black, ...)
uv remove <package>
uv lock --upgrade-package <package>   # upgrade one package within its range
```

Commit `pyproject.toml` and `uv.lock` together. `uv lock --check` fails if they're out of step.
Don't add a `requirements.txt` or `poetry.lock` at the repo root: Heroku's Python buildpack stops the
build when it finds more than one package manager file.

## Run Pipeline

Run the data pipeline to extract, clean and dump satellite catalogue and TLE data:

**Using uv:**
```bash
uv run python run_pipeline.py
```

**Using pip:**
```bash
python run_pipeline.py
```

## Run App

**Using uv:**
```bash
uv run python run_app.py
```

**With the virtual environment activated:**
```bash
python run_app.py
```

The app will be available at http://127.0.0.1:8050/

## Testing Heroku Deployment

Before deploying to Heroku, test your app locally to ensure it works with the production environment.

### Local Testing on Windows

**Note:** Gunicorn (Heroku's production server) doesn't work on Windows because it requires Unix-specific modules. Use one of these alternatives:

#### Option 1: Test with Development Server (Current Method)
```bash
python run_app.py
```
Visit http://127.0.0.1:8050/ - If this works, your app should work on Heroku.

#### Option 2: Use Waitress (Windows-Compatible Production Server)
```bash
# Install waitress
pip install waitress

# Run with waitress (production-quality server that works on Windows)
waitress-serve --listen=*:8000 run_app:server
```
Visit http://localhost:8000 to test.

#### Option 3: Deploy to Heroku Staging App (Most Accurate)
```bash
# Create a staging app
heroku create sattrack-staging

# Deploy your branch
git push heroku your-branch:main

# Check logs
heroku logs --tail --app sattrack-staging

# Open the app
heroku open --app sattrack-staging
```

### Local Testing on Linux/Mac

If you're on Linux or Mac, you can test with gunicorn directly:

```bash
# Install dependencies (app only, as on Heroku)
uv sync --locked --no-default-groups

# Test with gunicorn (same as Heroku)
gunicorn run_app:server
```
Visit http://localhost:8000 to verify.

### Pre-Deployment Checklist

Before deploying, verify:
- ✅ App runs locally with Python 3.12 (`python --version`)
- ✅ `uv lock --check` passes (`uv.lock` matches `pyproject.toml`)
- ✅ `.python-version` specifies `3.12`
- ✅ `Procfile` contains `web: gunicorn run_app:server`
- ✅ No errors in the app functionality

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and release notes.

### Current Version: 2.0.1

#### Latest Updates (2.0.1)
- Fixed Heroku deployment issue with Poetry
- Configured for Python 3.12 compatibility
- Improved responsive text sizing for mobile devices

#### Key Features (2.0.0)
- Upgraded to Python 3.12
- Modern dependency management with Poetry
- Automated requirements.txt synchronization
- Real-time satellite position tracking using TLE data
- 3D visualisation of active and inactive satellites
- 2D visualisation of satellite path
- Interactive filters and mobile-optimized interface
- CSV export functionality

#### Planned Improvements (Future Versions)
- Satellite pass predictor visualisation
- Satellite pass predictor export
- Enhanced logging for data pipeline
- Satellite informational page
- S3 migration
- DuckDB migration
- Airflow automation

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version (`major/` prefix) for incompatible API changes (breaking changes)
- **MINOR** version (`feature/` prefix) for new functionality in a backward-compatible manner
- **PATCH** version (`fix/` prefix) for backward-compatible bug fixes

### PR Naming Convention

Pull requests should be prefixed with the change type:
- `major/` - Breaking changes (e.g., `major/python-version-update`)
- `feature/` - New features (e.g., `feature/satellite-pass-predictor`)
- `fix/` - Bug fixes (e.g., `fix/csv-export-encoding`)
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates
- `chore/` - Maintenance tasks

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## Contributors

**Developer:** Francis Nwobu


## Visualisations

- Screenshots taken from app:

<img src="./static/3d_active_LEO_GEO.png" alt="3d visualisation: Active LEO and GEO satellites" width="400"/>

<img src="./static/3d_active_inactive.png" alt="3d visualisation: Active & Inactive satellites" width="400"/>

<img src="./static/3d_active_inactive_owner_filter.png" alt="3d visualisation: Active & Inactive USA satellites" width="400"/>

<img src="./static/3d_orbit_beidou.png" alt="3d visualisation: BEIDOU orbit" width="400"/>

<img src="./static/2d_iss_zarya.png" alt="2d visualisation: ISS orbit path" width="400"/>
