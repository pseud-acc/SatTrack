# SatTrack

**Version:** 1.0.0

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
- TODO:
  - Automate pipeline with airflow

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

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Option 1: Using Poetry (Recommended)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd SatTrack
   ```

2. Install Poetry if you haven't already:
   ```bash
   pip install poetry
   ```

3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```
   This will create a virtual environment and install all dependencies specified in `pyproject.toml`.

4. Activate the Poetry shell:
   ```bash
   poetry shell
   ```

### Option 2: Using pip (Legacy)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd SatTrack
   ```

2. Create and activate a virtual environment with Python 3.12:
   ```bash
   py -3.12 -m venv venv
   source venv/Scripts/activate  # On Windows Git Bash
   # or
   venv\Scripts\activate  # On Windows CMD
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ``` 

## Dependency Management

This project uses Poetry for dependency management. The `requirements.txt` file is automatically generated from `pyproject.toml` for Heroku deployment compatibility.

### Updating Dependencies

When you add, update, or remove dependencies in `pyproject.toml`:

1. **Locally:** Update `requirements.txt` manually:
   ```bash
   poetry export -f requirements.txt --output requirements_temp.txt --without-hashes --without dev
   python -c "import re; content = open('requirements_temp.txt').read(); open('requirements.txt', 'w').write(re.sub(r' ;.*', '', content))"
   rm requirements_temp.txt
   ```

2. **CI/CD:** The GitHub Action workflow automatically updates `requirements.txt` when you push changes to `pyproject.toml` or `poetry.lock`. The updated file will be committed to your PR automatically.

## Run Pipeline

Run the data pipeline to extract, clean and dump satellite catalogue and TLE data:

**Using Poetry:**
```bash
poetry run python run_pipeline.py
```

**Using pip:**
```bash
python run_pipeline.py
```

## Run App

**Using Poetry:**
```bash
poetry run python run_app.py
```

**Using pip:**
```bash
python run_app.py
```

The app will be available at http://127.0.0.1:8050/

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and release notes.

### Current Version: 1.0.0

#### Key Features
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
