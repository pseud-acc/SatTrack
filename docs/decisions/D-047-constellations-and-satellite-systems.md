# D-047 Constellations and satellite systems: CelesTrak first, completed from GCAT

**Status:** Accepted (owner, 2026-11-25) · **Date:** 2026-11-25 · **PRs:** #81 (`fix/tdrss-constellation`)
**Component:** pipeline (`sattrack_ingest/config.py`, the ad-hoc seed `manual_satellite_grouping`,
`int__celestrak__satellite_group_membership`, `int__xsrc__satellite_constellation`,
`int__xsrc__satellite_system_membership`, `int__xsrc__satellite_group_names`, `dim__satellite_constellation`,
`dim__satellite_system`, `fct__satellite_system`, `fct__satellite_master`); the `objects` dataset (schema 1 → 2) ·
**Tier:** full (renames a published field; changes what is downloaded)
**Supersedes:** D-026's `constellation` field and its operator groups. **Amends:** D-046 (the tdrss prefix and the dmc
exception are no longer needed; the name check becomes the exclusion rule for system groups).

## Context
D-026's `constellation` mixed three things: constellations (Starlink), systems of different satellites (GPS, TDRSS,
DMC) and operator fleets (SES, Intelsat). D-046 patched one symptom (TDRSS listing the spacecraft that use it). The
owner's definitions (25 Nov 2026):

- **Constellation**: near-identical satellites working together toward an objective.
- **System**: non-identical satellites working together; it may contain constellations, single satellites or both.
  A satellite can belong to several systems (a hosted payload, e.g. a Cospas-Sarsat repeater on a Galileo satellite).

The owner's rules for building them (main chat, 25 Nov 2026, during the build): **CelesTrak is the golden source**;
no file of every constellation or system to keep up by hand; an ad-hoc seed only for the handful CelesTrak has no
group for, each with its publisher's quote; exclusions as deterministic SQL; an accepted-values test that flags a new
name arriving from the source. Systems combine CelesTrak (which says a system exists) and GCAT (which completes its
membership). "GNSS" and "SBAS" are umbrella terms, never systems.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| Keep one `constellation` field (D-026) | No contract change | Mixes three kinds of group; a satellite gets one | Colour by "constellation" would mix GPS with SES |
| Seed every constellation and system with its rule and publisher text (the plan approved earlier on 25 Nov) | Rich details for each | A hand-maintained list that drifts; owner rejected it mid-build | Popovers get text for every row |
| **CelesTrak groups, completed from GCAT, plus a small ad-hoc seed (chosen)** | Golden source; retired members kept through GCAT; deterministic; new names flagged by a test | Names are CelesTrak's titles ("Tracking and Data Relay Satellite System (TDRSS)", "Beidou"); only seed rows carry descriptions | 3.3b filters and 3.10 colouring read the three fields; popovers show seed details where present |
| Systems from GCAT alone | No second source | GCAT has no system field: `Program` "identifies groups of related satellites", mixing systems, constellations and series; any rule needs an invented threshold | — |
| Systems from CelesTrak's `gnss` group split by GCAT family | No manual NavIC/QZSS | `gnss` also lists SBAS host satellites (SES-5, GALAXY 30, ...): 8 comms families became "systems"; GNSS is an umbrella term (owner) | — |

## Decision
**Fields** on `fct__satellite_master` and `objects` (schema 2): `satellite_constellation_name` (≤1),
`primary_satellite_system_name` (≤1), `satellite_system_names` (list, primary first then by name; `[]` when none).
The satellite × system table is `fct__satellite_system` (`flag_primary_system`, `system_source`); the definitions are
`dim__satellite_constellation` and `dim__satellite_system` (origin `celestrak` or `manual`, member counts).

**Constellations**
1. CelesTrak groups of kind `constellation` (starlink, oneweb, kuiper, qianfan, hulianwang, iridium-NEXT,
   globalstar, orbcomm), named by CelesTrak's title without "Operational"; first in config order wins.
2. Ad-hoc seed rows (kind constellation): PlanetScope (GCAT programme family Flock; Planet: "Planet had upgraded the
   constellation by replacing the original Dove satellites"), Sentinel-1, -2, -3 (name pattern; ESA: "designed as a
   two-satellite constellation", "based on a constellation of two satellites"). A CelesTrak group beats a seed row.

**Systems**
1. CelesTrak groups of kind `system` (gps-ops, glo-ops, galileo, beidou, tdrss, dmc), named by CelesTrak's title.
   **Exclusion**: a member counts only when its name fits the group (D-046's name check, now a filter: the most
   common leading word of the group's member names, e.g. TDRS). **GCAT completion**: every payload with its own GCAT
   payload record that shares a programme family with a kept member joins. Primary.
2. CelesTrak's `sarsat` (kind `system_hosted`), named by its title. Hosted (`flag_primary_system` 0).
3. CelesTrak's `sbas` (kind `system_hosted_umbrella`): never a system itself; each member's hosted system is the token
   CelesTrak writes before "/PRN" in its name (EGNOS, WAAS, GAGAN, SDCM, SOUTHPAN).
4. Ad-hoc seed rows (kind system): NavIC (IRNSS), QZSS, JPSS, GOES (incl. SMS-1/2, NASA's quote), Copernicus
   Sentinels, by GCAT programme family (primary); MSAS (QZS-3, -6, -7 by name) and BDSBAS (sbas members with PRN 130,
   143, 144), hosted, both quoting GPS.gov's L1 C/A PRN Code Assignments (Jan 2026).
   A system reached both ways keeps one row, primary; at most one primary per satellite (a failing test).

**Downloads**: 8 constellation + 6 system + `sarsat` + `sbas` + `stations` = 17 groups (21 before). The operator
groups (planet, spire, intelsat, ses, eutelsat, telesat) and `gnss` are excluded.

**Tests**: accepted-values warnings on both dims' names (a new CelesTrak title or SBAS token shows up in the D-037
email); one primary per satellite (error); system list starts with the primary (error); relationships master → dims
and bridge → master/dim; seed: unique names and rule values, https source URL, every detail non-null; a warning when a
definition names no satellite; unit tests for the membership, constellation and system rules.

## Evidence
Dev build, 25 Nov 2026: the 21 Nov live warehouse plus CelesTrak fetch run 45061938995 (artifact from GitHub, never
fetched locally), `dbt build --selector enrichment`: 338 passed, 2 existing warnings, 0 errors.

| Constellation | Objects (active) | | System | Objects (primary) | Active |
|---|---|---|---|---|---|
| Starlink | 11,203 (11,189) | | GLONASS | 142 (142) | 29 |
| OneWeb | 651 (651) | | Search & Rescue (SARSAT) | 82 (0) | 82 |
| Kuiper | 391 (391) | | GPS | 80 (80) | 37 |
| Qianfan | 275 (253) | | Beidou | 63 (63) | 55 |
| Hulianwang Digui | 241 (240) | | Galileo | 33 (33) | 32 |
| PlanetScope | 120 (116) | | GOES | 21 (21) | 6 |
| Iridium NEXT | 80 (80) | | Copernicus Sentinels | 13 (13) | 11 |
| Globalstar | 36 (33) | | TDRSS | 12 (12) | 8 |
| Orbcomm | 14 (14) | | Disaster Monitoring | 12 (12) | 6 |
| Sentinel-1 | 4 (2) | | NavIC | 11 (11) | 9 |
| Sentinel-2 | 3 (3) | | QZSS | 7 (7) | 6 |
| Sentinel-3 | 3 (3) | | JPSS | 3 (3) | 3 |
| | | | EGNOS, WAAS, GAGAN, SDCM, BDSBAS, MSAS | 3 each (0) | 3 each |
| | | | SOUTHPAN | 1 (0) | 1 |

32,652 objects: 13,021 with a constellation, 397 with a primary system, 423 with any system, 10 with both (the
Sentinels). Only payloads have systems (498 rows). Spot checks: HST and ISS (ZARYA) no TDRSS; BEIJING 1 in Disaster
Monitoring, HJ-1A not; SES 5 hosted EGNOS only; METEOSAT 9 hosted SARSAT only; QZS-3 QZSS + MSAS; BEIDOU 3G1 Beidou +
BDSBAS; GALILEO-PFM Galileo + SARSAT; rocket bodies (SMS 1 AKM, GOES 4 AKM) none; OPS 5111 (NAVSTAR 1, retired) GPS.

DMC sources: SSTL lists AlSat-1B, BilSat-1, UK-DMC1, NigeriaSat-1, Beijing-1, UK-DMC2, Deimos-1, NigeriaSat-2, S1-4
(https://sstl.co.uk/space-portfolio/the-disaster-monitoring-constellation); HJ-1A/1B are China's separate
"Environment & Disaster Monitoring Constellation"; GCAT files YAOGAN-4 under JB-6. GCAT has no SBAS information (no
psatcat field names a hosted payload). Share of each `gnss` family's active payloads in the group: navigation families
83–100 %, SBAS hosts 6–17 % (measured, then the umbrella rule was dropped).

## Consequences
- `objects` schema 2: `constellation` is gone; the viewer and app read none of the three fields yet (3.3b, 3.10).
- System names are CelesTrak's titles, some long ("Tracking and Data Relay Satellite System (TDRSS)") or in its case
  ("Beidou", "SOUTHPAN"). Owner, 26 Nov 2026: keep CelesTrak's names as they are, in the data and the UI.
- SBAS systems whose satellites CelesTrak doesn't list (KASS, ANGA, UK SBAS, Pak-SBAS, A-SBAS) are left out until it
  does (owner, 26 Nov 2026), although GPS.gov's register names their satellites.
- Only manual rows carry operator, purpose and description; CelesTrak rows carry the title only.
- A new CelesTrak title or SBAS token warns (accepted values) until someone adds it to the expected list.
- The first seed in the project: `raw_sattrack`, built with the enrichment unit; `run_pipeline.drop_orphans` treats
  seeds like sources.
- CelesTrak lists LUCH 5A as PRN 140 and LUCH 5V as PRN 141; GPS.gov has the reverse. Both are SDCM, so no effect.

## Revisit when
- CelesTrak adds, renames or drops a group, or an SBAS token appears that isn't expected (the warnings fire).
- GCAT publishes programme mission logs or a system field (GCAT's release notes plan programme logs).
- CelesTrak adds a group for a seed row (PlanetScope, Sentinels, NavIC, QZSS, JPSS, GOES, Copernicus, MSAS, BDSBAS):
  drop the row and use the group.
- GPS.gov republishes the PRN assignments with different MSAS or BDSBAS satellites.
- 3.3b builds the filters and info popovers.

## Related
D-026 (superseded field), D-043 (space station flag, unchanged), D-046 (amended), D-008 and D-039/D-040 (CelesTrak
download rules, unchanged), roadmap 3.3b and 3.10.
