# D-040 CelesTrak groups: raw tables in the warehouse, replaced all or nothing, never holding a unit

**Status:** Accepted (owner, 2026-11-23) · **Date:** 2026-11-23 · **PRs:** #69 (plan 3.8)
**Component:** `raw_celestrak` schema, `celestrak_groups.py`, the `celestrak` dbt source, `fct__satellite_master`
· **Tier:** light (contained in the pipeline; no state-script, AWS or workflow change)

## Context
D-026 says keep the last good copy when a fetch fails, and the task says the fetch must never fail or hold the run.
It doesn't say where the raw files live, what happens when some groups arrive and others don't, how a first run with
nothing to keep behaves, where the group config lives, or which swap unit carries the field.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Raw tables `raw_celestrak.*` in the warehouse (+ `raw_history` Parquet), like every other source** | The state script already carries the warehouse and raw history between runs: "keep the last copy" is "don't replace the table"; no infra change | The warehouse grows by ~13,000 rows a day of history | SupGP (4.2) lands the same way |
| Group CSVs as files in S3 (`celestrak/`) | Byte-for-byte copies | New state-script keys and IAM paths (infra change); a second way of keeping sources | – |
| **All or nothing: replace members and index only when the index and every configured group arrive and parse** | Precedence always sees one consistent snapshot | One bad group delays all for a day | – |
| Replace each group as it arrives | Fresher on partial success | Precedence could mix days; a refusal mid-way leaves a half-updated set | – |
| **First run with nothing to keep: create empty tables** | Models build; `constellation` is null for everyone; freshness warns | – | – |
| **Config list in `sattrack_ingest/config.py`, landed as `raw_celestrak.group_config` every run** | "The pipeline's source config", one list for the downloader and the dbt rules | A config table among raw sources | – |
| A dbt seed | dbt-native | Seeds break the layering rules (LIN-05) and the downloader would read dbt files | – |
| **Enrichment unit; every CelesTrak check at warn severity** | A CelesTrak problem never holds positions or details | A broken rule shows as a warning, not a held unit | – |

## Decision
The options in bold. The group CSVs land unchanged in `raw_celestrak.gp_group_member` with CelesTrak's `GROUP` query
value as the first column; the index page's groups and titles in `raw_celestrak.gp_group_index`. Display names come
from the index titles, so a configured group without a parsed title counts as a layout change: nothing is replaced.

## Evidence
Tests in `pipeline/ingestion/tests/test_celestrak_groups.py` (refusal mid-way keeps every group's last copy; a
layout change keeps it without counting as a refusal; a first refused run leaves empty tables and the models build);
local `dbt build` of the CelesTrak models on the committed sample (all tests pass; the new-group check warns).

## Consequences
- Constellation membership is at most a day old in normal running and stays at the last good copy otherwise.
- The title parser is checked against the live index page as served on 23 Nov 2026 (fetch run 45099334610; a
  trimmed copy is a test fixture). It found all 47 groups and titles; a first version keyed on table rows missed the
  28 groups that share a row with another, which the fixture now guards against.

## Revisit when
- The index page's layout changes (the stage logs "layout changed" and the 3-day freshness warning fires).
- SupGP (4.2) needs per-group replacement.

## Related
D-008, D-026, D-037, D-039; roadmap 3.8, 3.10, 4.2.
