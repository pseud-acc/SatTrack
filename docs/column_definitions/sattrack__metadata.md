# Column definitions: load and audit metadata

Part of the SatTrack column definitions; see `00_overview.md` for the rules and decisions.

## Batch 8b: load metadata (ingestion) and audit fields (dbt)

Source: SatTrack-derived. Rows #27–#29 of batch 8, moved here on 2026-11-08 when the definitions were split by origin.

| # | Column | Model / macro | Definition (SatTrack-derived) | Primitives & decision |
|---|---|---|---|---|
| 27 | `_loaded_at`, `_run_id`, `_source_url`, `_source_updated_at`, `_source_row_number`, `_source_file` | `sattrack_ingest.raw_writer` (every raw table) | Load details SatTrack's ingestion writes on every raw row: when it was loaded (`_loaded_at`), the run (`_run_id`), the source file or URL, the publisher's update time and the row number. E.g. `run_2026-11-09T193917Z`. | **Detail:** Load metadata written by `sattrack_ingest` on every raw table (as text; staging casts it): `_loaded_at` = when the run loaded the data; `_run_id` = the run identifier; `_source_url` = the URL fetched (for pinned packages, `pycountry==<version>` or `geonamescache==<version>`); `_source_updated_at` = the publisher's own update time, from GCAT's `# Updated` row (NULL for other sources); `_source_row_number` = the row position in the landed data; `_source_file` = the file or table landed (e.g. `satcat.tsv`, `satcat100k.tsv`, `gp`, `pcols.html`, `pycountry-<version>`), which tells unioned GCAT files apart. Plan §3. `_source_updated_at` drives freshness (D10). |
| 28 | `inserted_date_time` | macro `helper__audit_fields` (every model) | When dbt built this row, set by SatTrack's models at build time. E.g. 2026-11-09 19:40:33 UTC. | **Detail:** When dbt built the row: the build's current timestamp, set by the model's `cte_final`. Audit field (user, 2026-10-25). Non-deterministic, so parity checks exclude it. |
| 29 | `inserted_by` | macro `helper__audit_fields` (every model) | Which pipeline run built this row: the run ID, or `manual` for a local dbt run. Set by SatTrack. E.g. `run_2026-11-09T193917Z`. | **Detail:** Which job built the row: the pipeline run id (`SATTRACK_RUN_ID`, set by `run_pipeline.py`), or `manual` for a local or ad hoc dbt run. Audit field (user, 2026-10-25). Joins to `ops.audit.pipeline_run`. |
