# D-043 Flag space stations from CelesTrak's `stations` group

**Status:** Accepted (owner, 2026-11-24) · **Date:** 2026-11-24 · **PRs:** #69
**Component:** pipeline (`sattrack_ingest/config.py`, `int__celestrak__space_station`, `fct__satellite_master`); the
`objects` dataset · **Tier:** full (changes an accepted decision and a published data contract)
**Partly supersedes:** D-026's "every other group is excluded" (for this one group).

## Context
D-026 takes constellation and operator groups from CelesTrak and excludes every other group, `stations` among them.
The owner wants the space stations: CelesTrak's "Space Stations" group (`stations`, under "Special-Interest
Satellites" on its GP index page) lists the ISS and Tiangong modules and the spacecraft visiting them. On 22 Nov 2026
(fetch run 45061938995) it had 17 members: ISS (ZARYA), POISK, ISS (NAUKA), CSS (TIANHE), CSS (WENTIAN),
CSS (MENGTIAN), Soyuz, Progress, Crew Dragon, Dragon CRS, Shenzhou and Tianzhou spacecraft, and small satellites
listed with them.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **A separate flag: download `stations` too and add `flag_space_station` (1/0) to `objects`** | The constellation field keeps its meaning; the flag works whatever the colour mode | One more field in the data contract | 3.4 can always label stations (e.g. the ISS); 3.9's search can offer them; a "Space stations" filter later |
| `stations` as a constellation value (first in precedence) | Simplest | Mixes "is a station" with constellation membership; a Dragon docked to the ISS would show as a "constellation" | Colour by constellation would paint a handful of station objects |
| Later, in its own PR | Keeps #69 small | A second contract change soon after the first | – |

## Decision
A separate flag.

- `sattrack_ingest/config.py` gains `CELESTRAK_STATION_GROUPS = ["stations"]`, downloaded with the other included
  groups under D-008, D-039 and D-040 (one more CSV per run), with group kind `station`, after the operators in
  config order. `stations` leaves the excluded list.
- `int__celestrak__space_station`: one row per object in a `station` group, `flag_space_station = 1`.
- `fct__satellite_master.flag_space_station` (integer 1/0, never null: objects CelesTrak doesn't list get 0) and the
  same field in the `objects` dataset and `app/contracts/objects.schema.json` (required, 0 or 1).
- Station groups never name a constellation: `int__celestrak__satellite_constellation` counts only kinds
  `constellation` and `operator` (its unit test covers it).
- The credit stays "Constellation groups: CelesTrak (Dr T.S. Kelso)"; CLAUDE.md's exception covers the station group.

## Evidence
- The `stations` CSV from fetch run 45061938995 (22 Nov 2026, GitHub runner): 17 rows; its first three rows are the
  test fixture `pipeline/ingestion/tests/fixtures/celestrak/stations.csv`.
- CelesTrak's GP index page as served on 23 Nov 2026 (run 45099334610) titles the group "Space Stations".
- Unit tests: `ut__int__celestrak__space_station__station_groups_only`; the constellation rules test now includes a
  station group that must not name a constellation. dbt-bouncer: all checks pass.

## Consequences
- One more request per CelesTrak download (21 groups instead of 20), well inside D-039's once a day.
- A new published field; the committed `objects` sample carries it (0 everywhere: the sample has no station object).
- If CelesTrak drops or renames the group, the existing warning check (`groups_in_config`) reports it and the flag
  goes to 0 for everything until the config is fixed.

## Revisit when
- CelesTrak changes what the `stations` group covers (e.g. drops visiting vehicles).
- The viewer wants station modules apart from visiting vehicles: GCAT's object categories could split them.

## Related
D-008, D-026, D-039, D-040; roadmap 3.4, 3.8, 3.9.
