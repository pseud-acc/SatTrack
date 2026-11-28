# D-057 The List View shows every object type, from the objects dataset

**Status:** Accepted (owner request, 27 Nov 2026; built 28 Nov 2026) · **Date:** 2026-11-28 · **PRs:** this PR
(`feature/list-view-all-types`)
**Component:** the List View (`callback_table`, `helper__app_data.list_objects`, `helper__table_display`), the
server's propagators (`helper__satellite_position.satrecs_for`), `app/core/state.py` · **Tier:** light
**Builds on:** D-011 (every object type in `objects`), D-035 (the sidebar filters on `objects`), D-052 (the list is
built only while its tab is open).

## Context
The globe draws payloads, rocket bodies and debris, but the List View was built from the app CSV, which holds
payloads only: with Debris switched on, the list stayed empty of debris. The owner asked for rocket bodies and debris
in the list.

## Options
| Option | For | Against |
|---|---|---|
| **Build the list from the objects dataset, with a Type column (chosen)** | The list and the globe show the same objects; no pipeline change; payloads reuse the propagators they already have | Each server worker holds ~12,850 more propagators |
| Widen the app CSV to every type | No app change to the list | The CSV is being retired (roadmap 3.6); a pipeline change for a file with no future |
| Build the list in the browser from the worker's records | No server memory | A second table implementation; the server-side list and its tests would go |

## Decision
`list_objects` selects with the filter spec on the filter table, takes the rows from the objects dataset's list
columns and places them with the same SGP4 code, using the dataset's own field names (`OMM_FIELDS_OBJECTS`: the OMM
keywords in lower case). The table gains a "Type" column (Payload / Rocket body / Debris) and names an object
Space-Track hasn't named yet "Not yet named (designator)", as the search list does. Objects SGP4 can't place are
left out, as on the globe. The 2D map still reads the app CSV until roadmap 3.6.

## Evidence
**Measured** on the 28 Nov 2026 full data (one process, Windows laptop): at rest 271 MB against 268 MB on `main`;
peak during start-up 356 MB against 312 MB; start-up 4.8 s against 3.4 s; the propagator cache holds 32,631 entries
(payloads share theirs with the CSV's: 19,776 before); listing all 32,120 placeable objects takes 0.31 s. CI's Heroku
build check runs the app within the dyno's memory.
Tests: position parity for every sample object of every type against the sgp4 library (1 mm);
`tests/app/test_table_display.py` (the helpers), `tests/app/test_callback_table.py` (rows per filter, from plain
pandas and sgp4), the list journey in `tests/e2e/test_journeys.py` (Space junk mode adds junk rows).

## Consequences
- With every type and status All, the list holds ~32,000 rows (it held up to ~19,700): a larger response when that
  tab is open (it is sent only while open and only when the filters change, D-052).
- The list's rows no longer depend on the app CSV; one less user of it before 3.6.

## Revisit when
- The list's response is slow on phones with every type shown (page the rows on the server).
- Roadmap 3.6 removes the CSV (the 2D map moves to the objects dataset too).

## Related
D-011, D-035, D-052, D-053; roadmap 3.6, 5.5 (CSV download of the list).
