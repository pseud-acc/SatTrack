# D-056 Filtering by constellation and satellite system

**Status:** Accepted (owner, 28 Nov 2026: "a high priority to show constellations and systems") · **Date:** 2026-11-28
· **PRs:** this PR (`feature/constellation-system-filters`)
**Component:** the filter spec's field list (`app/contracts/filter_fields.yml`, the generated schema), the panel's
"More filters" rows, the spec builder (`helper__app_data.sidebar_filter_spec`), the globe's worker · **Tier:** light
**Builds on:** D-047 (the three grouping fields), D-030 to D-034 (the filter spec), D-044 and D-051 (the panel).

## Context
D-047 put `satellite_constellation_name`, `primary_satellite_system_name` and `satellite_system_names` on every
object, with labels ready for the panel, and roadmap 3.14 planned their filters. The home page's hero (agreed
28 Nov 2026) says the catalogue can be explored "by owner, mission, constellation and orbit", so the filter has to
exist before that page ships.

## Options
| Option | For | Against |
|---|---|---|
| **Two rows at the top of "More filters": Constellation, Satellite systems (chosen)** | Same pattern as owner and purpose, so nothing new to learn; the panel's top stays as it is | "More filters" grows to six rows |
| A "Groups" section of its own above Search | More prominent | Another section in an already long panel |
| One combined "Constellation or system" control | One row | Mixes two things D-047 separated on purpose |
| **System matches every member, with a switch for "built for the system" (chosen)** | "GPS" finds the GPS satellites; "Search & Rescue" finds the weather satellites that carry its repeaters; the switch gives the strict reading | One extra control inside the row |
| Two system rows (primary; all) | Explicit | Two near-identical rows |

## Decision
- The three fields join the filter spec's allowed fields (so natural-language query can use them later, D-033).
- **Constellation:** a multi-select; `satellite_constellation_name in [...]`.
- **Satellite systems:** a multi-select; `satellite_system_names contains_any [...]`. With "Only satellites built for
  the system" on, `primary_satellite_system_name in [...]` instead; the chip's label says which.
- The options are the objects dataset's own values, so a grouping the pipeline adds appears with no code change.
- The two rows sit first in "More filters", each with one line saying what it is, in D-047's words. Chips, the live
  count, "Clear all" and the type counts work as for the other rows.
- The globe's worker keeps `satellite_system_names`; the browser's filter code needs no change (it reads the
  generated rules).

## Deviation from the roadmap item
3.14 also listed info popovers with each grouping's definition and source link. Those texts live in
`dim__satellite_constellation` and `dim__satellite_system`, which the app doesn't load; they need a small published
dataset. That is left for the home page work, whose summary tiles need the same dataset (roadmap 3.14b).

## Evidence
Shared conformance cases (7 valid, 1 invalid added) run by the Python and browser implementations;
`tests/app/test_callback_filters.py` (spec clauses, counts with plain pandas, chips, rows, chip removal);
`tests/e2e/test_production_controls.py` (each new control changes the globe as asked). On the 28 Nov 2026 data,
Constellation: Starlink shows 11,173 active payloads.

## Consequences
- Every server worker's filter table holds three more columns.
- The dropdowns list every grouping in the data, including ones with no active member (the count then says 0).

## Revisit when
- The groupings dataset lands (add the definition and source popovers).
- "More filters" gets a seventh row (regroup the panel).

## Related
D-047, D-049, D-051; roadmap 3.14, 3.14b, 5.3.
