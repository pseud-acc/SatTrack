# App test data

A small fixed sample of the pipeline's app files, used to run the app without AWS access:

- `satcat_tle.csv`: 341 satellites (up to 40 per status and orbit class) from the pipeline run
  `run_2026-11-15T124939Z`, in the same 29-column shape the pipeline publishes to S3. That run predates the
  OMM columns (`Epoch` ... `ObjectId`), so they were added later from each row's own `TLE1`/`TLE2` with
  `sgp4.exporter.export_omm`, rounded to the TLE's printed precision, and `Inclination` set to the TLE value
  (the export no longer rounds it). The OMM and TLE fields describe the same element set: positions from
  either agree to about 1 cm.
- `last_data_update.csv`: that run's freshness rows.

CI's Heroku build check (`.github/scripts/heroku_build_check.sh`) starts the app with
`SATTRACK_APP_DATA_DIR` pointing here. For a local run without S3:

```bash
SATTRACK_APP_DATA_DIR=tests/app_data uv run python run_app.py
```

The folder is in `.slugignore`, so it never ships to Heroku. The positions drift as the element sets age;
that doesn't matter for the checks.

**Sources:** orbital data (GP element sets, SATCAT) from USSPACECOM via
[Space-Track.org](https://www.space-track.org/); launch, owner and mission details from
[GCAT](https://planet4589.org/space/gcat/) (J. McDowell). Public element sets must not be used for
conjunction (collision) assessment.
