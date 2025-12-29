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
- Track work in progress here

### Changed
- Track modifications here

### Fixed
- Track bug fixes here

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
- Configured Poetry for local development only:
  - Added `poetry.lock` to `.gitignore` for Heroku compatibility
  - Heroku uses `requirements.txt` (auto-synced via GitHub Actions)
  - Poetry used for local dependency management and development

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