# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [Unreleased]

### Planned
- Automated pipeline with Airflow