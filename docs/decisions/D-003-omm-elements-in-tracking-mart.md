# D-003 Carry OMM elements in the tracking mart only

**Status:** Accepted · **Date:** 2026-11-21 · **PRs:** #50 (plan 1.1)
**Component:** dbt `fct__gp_elements` · **Tier:** light

## Context
Plan 1.1 carried the remaining OMM fields (`mean_motion_dot`, `mean_motion_ddot`, `rev_at_epoch`, `element_set_no`,
`ephemeris_type`, `classification_type`) from Space-Track GP into the marts. The plan text said
`fct__satellite_master`. Since #42 the app takes elements from the tracking mart, which updates every run; the master
is held whenever GCAT enrichment fails, as it was from 16 Nov.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Tracking mart only** (`fct__gp_elements`) | Elements always from the current run | Consumers must join two marts for elements plus details | The browser dataset (D-009) and SupGP (4.2) both read elements from tracking |
| Master only (the plan text) | One mart for everything | Elements go stale whenever enrichment is held | – |
| Both | Convenient | Two copies; a stale one could be picked up by mistake | – |

## Decision
The OMM fields go into `fct__gp_elements` only. A warning-level check flags any `ephemeris_type` other than 0 (SGP4).

## Evidence
Local copy of the live warehouse: 32,676 rows, no nulls in the six fields; `ephemeris_type` 0 and `classification_type`
U on every row; the ISS (25544) matches its TLE lines (mean motion dot 0.00011176, revolution 59,586).

## Consequences
Every consumer takes elements from tracking and descriptive fields from the master (as `app__objects.sql` does, with a
left join so new objects appear at once).

## Revisit when
- A propagator other than SGP4 is considered (the `ephemeris_type` check fires), see D-007.
- The master stops being held on enrichment failures.

## Related
D-004, D-007, D-009.
