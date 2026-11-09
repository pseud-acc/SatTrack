# SatTrack column definitions: draft for review (D2)

Status: **batches 1–8 drafted 2026-10-25; batches 1–2 reviewed 2026-10-25.** On 2026-11-08 the file was split by source origin, Batch 9 was added (columns in the model ymls that had no definition of their own), and Batches 7–8 were corrected against the current SQL. Batches 3–9 are awaiting column-by-column review. No manual seeds remain (plan §15): GCAT's code labels are parsed from its documentation page at ingestion (`ingestion/sattrack_ingest/gcat_docs.py`).

Rules (user, 2026-10-25):
- Every definition comes from the publisher's own documentation and is cited.
- Wording is quoted or closely paraphrased from that documentation.
- A column with no published definition is marked **UNSOURCED** instead of guessed.
- Each block becomes `{% docs col__<name> %}` in `transform/docs/columns/*.md`, with the source at the end of the block.
- If two sources share a column name, they must share the meaning; otherwise the names are made distinct.

`*` in "SatTrack note" marks a transformation SatTrack applies, which is not a GCAT definition.

**Layout (2026-11-08).** One file per source origin, named `<publisher>__<entity>.md` like the dbt models (`stg__<source>__<entity>`):

| File | Batches | Origin |
|---|---|---|
| `gcat__satcat_psatcat.md` | 1, 2 | GCAT object and payload catalogs |
| `gcat__currentcat.md` | 3 | GCAT current catalog |
| `gcat__launchlog.md` | 4 | GCAT orbital launch log |
| `gcat__orgs_sites_lv.md` | 5 | GCAT organisations, launch sites, launch vehicles |
| `spacetrack__gp.md` | 6, 9b | Space-Track GP (9b: GP values kept beside a resolved value) |
| `spacetrack__code_tables.md` | 6b | Space-Track boxscore and launch_site classes |
| `reference__labels_countries_cities.md` | 7 | GCAT code labels, pycountry (ISO 3166), GeoNames |
| `sattrack__derived.md` | 8, 9a | SatTrack-derived columns (intermediate and marts) |
| `sattrack__metadata.md` | 8b | Load metadata (ingestion) and audit fields (dbt) |

`scripts/build_docs_registry.py` reads these files in the order above and writes one registry file per origin to `transform/docs/columns/` (same file name). A column name gets exactly one block: the first row that defines it (not a "(shared block …)" row) in that order wins, and the block goes into the registry file of that row's origin. `--check` regenerates in memory and fails on drift.

Every section starts with a `Source:` line, or `- \`key\`: …` bullets that a row selects with the prefix of its source column (e.g. `orgs.Code`). Sections whose table has a "Model / macro" column are SatTrack-derived, and their blocks cite that model.

**Decisions on batches 3–8 (2026-10-25):**
- **Undocumented values become NULL in intermediate; staging keeps the raw value.** "If the meaning cannot be explained then it should be excluded." A warn-level test reports every value outside the documented code list. The 2026-10-24 audit found 162 rows: satcat Status `R?`/`L?` 15, satcat Type `Z…` 28, psatcat Mvr `N` 2, Att `D` 1, Discipline `GEO` 1 (the only one on an app object), launchlog Launch_Code category `N` 15, lv Class `B` 99.
- **Vague dates are stored as written** in `<date>` (changed 2026-11-08; first decided as the interval start), plus the GCAT interval in `<date>_start` and `<date>_end` (a `?` widens it by one unit each side) and `<date>_precision` (batch 8 #24; the planned uncertainty/scheduled flag columns were not built, see the correction there). Mainly affects `end_operation_date` (52% of app values coarser than a day) and `end_transmission_date` (51%). Launch dates ≈ 0%.
- **Columns the publisher doesn't document stay in staging only**, with an "undocumented by publisher" doc block and observed values. They are never used downstream. Exception: `lv_generic_name`, kept as a reference column.
- **Disposal-orbit fields** (GCAT: "should not be relied upon at present") go to staging and intermediate only, not marts.
- **Renames approved:** `org_country_code` → `org_state_code`, `site_country_code` → `site_state_code`. **v3 placeholders dropped:** `source_priority`, `record_quality_score`.
