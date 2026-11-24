# D-026 Constellations from CelesTrak's group lists, credited

**Status:** Accepted; partly superseded by D-043 (2026-11-24: the `stations` group is downloaded as `flag_space_station`); amended by D-046 (2026-11-24: `tdrss` counts only members whose name starts with TDRS; a warning check compares member names with their group) · **Date:** 2026-11-22 · **PRs:** #68 (decision), #62 (fetch workflow)
**Component:** pipeline; the `objects` dataset; the viewer's credits · **Tier:** full

## Context
Colouring by constellation (D-017) needs membership the data doesn't carry. CLAUDE.md says to take data only from its
original publishers and never republish another tracker's compiled data. The owner's IP is blocked by CelesTrak, so
CelesTrak is fetched only from GitHub's runners (D-008).

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **CelesTrak groups via the pipeline, with a visible credit** | Membership from the source; current within hours; complete for GNSS and Iridium | A new daily fetch; permission rests on reading a silent policy | Constellation colouring and filters |
| GCAT families (leading letters of psatcat `Program`, plane labels) | Original publisher (CC-BY), already in the warehouse | No plane labels for Galileo, GLONASS, Globalstar; few for Iridium | The fallback |
| Name-prefix rules | No new source | A hand-maintained list | – |
| Automatic threshold on name prefixes | No list | Misgroups COSMOS (1,159), OBJECT (676), USA | – |

## Decision
- The pipeline downloads the groups under D-008 and CelesTrak's usage policy: CSV, compressed, once per update, stop on
  any non-200 (including 301), wait 15 minutes after a 5xx. It keeps the last good copy if a fetch fails.
- Groups from a config list. Constellations: starlink, oneweb, kuiper, qianfan, hulianwang, iridium-NEXT, globalstar,
  orbcomm, gps-ops, glo-ops, galileo, beidou, tdrss, dmc. Operators: planet, spire, intelsat, ses, eutelsat, telesat.
  Every other group is excluded.
- An object in two groups takes the first in config order (constellations first). Display names are CelesTrak's group
  titles without "Operational". A test warns when CelesTrak's index lists a new group.
- Each object gets a `constellation` field. The viewer credits "Constellation groups: CelesTrak (Dr T.S. Kelso)".
- CLAUDE.md records this as the one exception to "never republish another tracker's compiled data".

## Evidence
GCAT vs CelesTrak comparison (22 Nov, `constellation_compare.json`): GCAT covers 98.3% of tracked payloads (with the
`*100k` files) and matches the broadband fleets, but lacks plane labels for Galileo, GLONASS and Globalstar and has few
for Iridium. CelesTrak's groups list operational satellites only. CelesTrak's usage policy (16 Nov 2026) covers download
behaviour and says nothing on redistribution. Fetch workflow runs 45061938995 (47 groups, no refusals) and 45065085216
(the policy page).

## Consequences
Risk accepted: the permission is an interpretation of silence. If CelesTrak objects, switch to the GCAT rule (a family
from the leading letters of psatcat's `Program`, counted when at least 50 active payloads carry plane labels).
Delivered as a pipeline task parallel to 3.2; colouring waits for it (D-028).

## Revisit when
- CelesTrak publishes terms on redistribution, or asks SatTrack to stop.
- GCAT adds plane labels for the missing constellations.
- A new group appears that belongs in the config (the warning test fires).

## Related
D-008, D-017, D-028; #62; CLAUDE.md "Security and data".
