# D-002 Keep the first row of a repeated GCAT JCAT

**Status:** Accepted · **Date:** 2026-11-21 · **PRs:** #51
**Component:** dbt `int__jsr__launch_events` · **Tier:** light

## Context
GCAT's launch log gave one JCAT to two payloads from the failed Vulcan launch 2026-F07 (15 Nov): F01824 to Kuiper-00655
and -00658, F01834 to Kuiper-00672 and -00673 (F01825 and F01835 missing from the sequence). The primary-key test
failed as an error, so enrichment was held from 16 Nov: details frozen, 140 tracked objects without details, a failure
email every day. GCAT's file of 19 Nov still had the error.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| Keep the **first row in GCAT's file order** | Fixed rule from source order; the maintainer adds corrections after the original entry; same rule `int__jsr__launch_vehicles` already uses | Keeps the wrong object if an error is ever inserted before the valid row | Unattended pipeline (CLAUDE.md) |
| Drop every duplicated row | Never keeps a wrong row | Lost valid launches | – |
| A manual exclusion list | Exact | Needs a human; breaks the unattended rule | – |
| Keep failing closed | Safest data | Enrichment frozen until GCAT fixes the file (days or weeks) | Conflicts with "nothing needs a human more often than every 14 days" |

## Decision
Keep the first row per JCAT by `_source_row_number`. The staging key test warns on any repeated JCAT and becomes an
error above 10, so a broken file still fails closed. The row-count test changes from `equal` to `lte` with
`min_ratio: 0.999`. When GCAT corrects the IDs, the dropped rows come back on their own.

## Evidence
Full `dbt build` on a local copy of the live warehouse (`run_2026-11-20T031744Z`): 272 pass, 2 known warnings; launch
events 32,213 → 32,211; `fct__satellite_master` covers all 32,676 tracked objects (it was 140 short). Kept rows:
F01824 → Kuiper-00655, F01834 → Kuiper-00672.

## Consequences
Repeated JCATs stay visible as a warning in the run report. The next run promoted enrichment and the daily failure
emails stopped.

## Revisit when
- More than 10 repeated JCATs appear (the error threshold fires): a structural GCAT change, not a typo.
- GCAT documents a different correction convention.

## Related
D-001 (the gate exposed by the warn runs).
