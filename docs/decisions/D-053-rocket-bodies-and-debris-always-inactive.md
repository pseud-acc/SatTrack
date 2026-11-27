# D-053 Rocket bodies and debris are always Inactive

**Status:** Accepted (owner, 27 Nov 2026) · **Date:** 2026-11-27 · **PRs:** this PR (`fix/junk-inactive-https`)
**Component:** `fct__satellite_master` (`operational_status`, `operational_status_source`), the panel's type note · **Tier:** light
**Updates:** D-049 (its note "almost all rocket bodies and debris are inactive" becomes "always").

## Context
`operational_status` came from GCAT only (`int__jsr__satellite_status`). For non-payloads GCAT's payload catalog has
no record, so `flag_gcat_active` is null and the status falls through to the current catalog's `Ac = 'A'`. On the
26 Nov data that made 6 of 12,398 rocket bodies and debris Active (SATCAT 41847, 43012, 43656, 44909, 52085 CZ-x and
Breeze-KM upper stages; 65544 CZ-6A DEB), which showed them as working satellites on the globe and in Active filters.
The object type comes from Space-Track, the status from GCAT, so the two sources disagree.

## Options
| Option | For | Against |
|---|---|---|
| **Space-Track's type wins: rocket bodies and debris are Inactive (chosen)** | One deterministic rule, no manual list; matches what visitors expect of "junk"; the panel note can say "always" | Hides the rare upper stage GCAT counts as working (stages used as platforms) |
| Keep GCAT's status | No new rule | Junk shows as Active satellites; the note stays "almost all" |
| A manual exceptions list | Exact | Breaks the unattended, deterministic pipeline rule |

## Decision
In `fct__satellite_master`, an object whose Space-Track `object_type` is `ROCKET BODY` or `DEBRIS` gets
`operational_status = 'Inactive'`. When GCAT had said Active, `operational_status_source` is
`space_track_object_type`, so the override stays traceable; otherwise the source is unchanged. The rule sits inline in
the join CTE because it reads two upstreams (MRT-01 allows that). The panel note says rocket bodies and debris are
always inactive.

## Evidence
Owner request, 27 Nov 2026. Singular test `assert__fct__satellite_master__junk_inactive` fails on any Active rocket
body or debris; an accepted_values test covers `operational_status_source`.

## Consequences
- The 6 objects turn Inactive at the next daily pipeline run; the app needs no data change of its own.
- A genuinely working upper stage (hosted payloads, stages used as platforms) shows as Inactive.

## Revisit when
- GCAT or Space-Track publish a working rocket body that visitors would expect to see as Active.
- Space-Track changes its object types (e.g. a new type for hosted platforms).

## Related
D-016, D-049; `col__operational_status`, `col__operational_status_source`.
