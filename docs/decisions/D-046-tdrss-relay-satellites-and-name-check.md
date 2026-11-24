# D-046 TDRSS keeps only relay satellites; constellation membership checked against names

**Status:** Accepted (owner, 2026-11-24) · **Date:** 2026-11-24 · **PRs:** this PR (`fix/tdrss-constellation`)
**Component:** pipeline (`sattrack_ingest/config.py`, `stg__celestrak__group_config`,
`int__celestrak__satellite_constellation`, a warning check); the `objects` dataset's `constellation` values ·
**Tier:** full (amends an accepted decision; changes published values)
**Amends:** D-026's "membership is CelesTrak's group list" (for groups with a member-name prefix; today only `tdrss`).

## Context
D-026 takes each configured CelesTrak group's CSV as its membership. The first run with #69 (live `objects.json`,
24 Nov 2026) showed that CelesTrak's `tdrss` group, titled "Tracking and Data Relay Satellite System (TDRSS)" on its GP
index page, lists the TDRS relay satellites **and** spacecraft that use the relay system. In fetch run 45061938995
(22 Nov 2026) it had 25 members: 8 named "TDRS n" (TDRS 3, 5, 6, 7, 8, 11, 12, 13) and 17 others: HST (NORAD 20580),
ISS (ZARYA) (25544), TERRA, AQUA, AURA, SORCE, TIMED, THEMIS A/D/E, FGRST (GLAST), GPM-CORE, MMS 1-4 and NOAA 20
(JPSS-1). Those 17 were published with `constellation` = "Tracking and Data Relay Satellite System (TDRSS)".

The owner decided (main chat, 24 Nov 2026): keep TDRSS as a constellation, but only the TDRS satellites get it;
audit the other 19 constellation and operator groups the same way; add a check that flags a satellite whose name
doesn't contain the constellation's string.

## Audit of the 20 groups (fetch run 45061938995, 22 Nov 2026)
Leading word = the letters before the first non-letter of CelesTrak's `OBJECT_NAME`.

| Group (kind) | Members | Members whose name doesn't fit the group's usual leading word | Verdict |
|---|---|---|---|
| starlink (c) | 11,203 | none (all STARLINK) | fits |
| oneweb (c) | 651 | none | fits |
| kuiper (c) | 391 | none | fits |
| qianfan (c) | 275 | none | fits |
| hulianwang (c) | 248 | 8: GUOWANG-30 OBJECT A, C-H, J (101416, 101418-101424) | legitimate members under another name (inference: "Guowang" is the operator's name for the network; "OBJECT x" is Space-Track's name before identification) |
| iridium-NEXT (c) | 80 | none (all IRIDIUM) | fits |
| globalstar (c) | 36 | none | fits |
| orbcomm (c) | 14 | none | fits |
| gps-ops (c) | 32 | none (all GPS) | fits |
| glo-ops (c) | 27 | none: all COSMOS, which is how GLONASS satellites are named | fits (not "GLONASS", by design) |
| galileo (c) | 32 | none: all GSAT0nnn (GALILEO n) | fits (not "GALILEO" as leading word) |
| beidou (c) | 37 | none | fits |
| **tdrss** (c) | 25 | **17 users of the relay system** (list above) | **not the constellation: fixed here** |
| dmc (c) | 9 | 5 of 9 lack "DMC": BEIJING 1 (28890), HUANJING 1A/1B (33320/33321), YAOGAN-4 (33446), DEIMOS-1 (35681); UK-DMC 2 and DMC3-FM1-3 fit | open question (CelesTrak titles the group "Disaster Monitoring", not "DMC") |
| planet (o) | 136 | 27 not FLOCK: SKYSAT (14), PELICAN (9), TANAGER-1/-2, EDDA-1, PROJECT SUNCATCHER M1 | an operator's fleet: fits (inference for EDDA-1, PROJECT SUNCATCHER M1) |
| spire (o) | 72 | 2 not LEMUR: OTTER SDM (66678), TWILIGHT-1 OBJECT B (67364) | operator fleet / hosted payloads (inference) |
| intelsat (o) | 55 | 30 not INTELSAT: GALAXY (15), DIRECTV (7), HORIZONS, FM-5/6, XM-5, SKY MEXICO-1, AZERSPACE 2 (IS-38), AT&T T-16 | operator fleet incl. satellites it operates for others (inference) |
| ses (o) | 71 | 51 not SES: O3B (32), ASTRA (11), NSS (4), AMC (2), QUETZSAT 1, 03B MPOWER F12 (zero, not O: as published) | operator fleet |
| eutelsat (o) | 29 | 2: EXPRESS-AT1/AT2 | operator fleet (inference: Eutelsat capacity on RSCC satellites) |
| telesat (o) | 17 | 13 not TELESAT: NIMIQ, ANIK, TELSTAR, TERRESTAR-1, SKYTERRA 1, VIASAT-2, LEO 1, AMOS-17 | operator fleet (inference for VIASAT-2, AMOS-17, TERRESTAR-1, SKYTERRA 1) |

Only `tdrss` mixes in spacecraft that are not the constellation. Operator groups list a company's fleet under its own
satellite names, so "name contains the group's title" doesn't apply to them.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Member-name prefix per group in the config (`tdrss`: `TDRS`), carried into the warehouse** | Deterministic, one entry, visible in `raw_celestrak.group_config` and staging; the filter lives in the intermediate model | A config entry SatTrack maintains (D-026 rejected name-prefix rules as a list; this is one entry, for one group, by owner decision) | Colour by constellation (3.8) shows 8 TDRS satellites, not HST or the ISS |
| Exclude `tdrss` altogether | Simplest | The owner wants TDRSS as a constellation | - |
| Use GCAT's programme/owner to filter | Original publisher | A cross-source rule for one group; GCAT's TDRS programme names would need their own matching | - |
| Hand list of the 17 NORAD ids | Exact today | A hand list that goes stale with every new TDRSS user (CLAUDE.md: no hand lists) | - |

For the name check:

| Option | For | Against |
|---|---|---|
| **Expected string = the group's prefix, else its most common leading word (from the data each run); constellation groups only** | No list; passes glo-ops (COSMOS) and galileo (GSAT) without exceptions | Can't see a group whose majority is misnamed |
| Expected string = the first word of CelesTrak's title | Simple | Would warn on every glo-ops, galileo and dmc member and need a list of exceptions (76 rows today) |
| Also check operator groups | Complete | ~125 warnings a day on legitimate fleet names (SKYSAT, ASTRA, GALAXY, ...) |

For the exceptions the check needs (owner, 24 Nov 2026):

| Option | For | Against |
|---|---|---|
| **One logic macro, `helper__flag_member_name_fits_group`, a `case when` with one branch per exception** | Every exception in one documented place, with its reason and removal trigger; the check reads as the rule | A short hand-kept rule set (two branches today) |
| Accept the daily warnings | No exceptions to keep | 13 warnings every day on rows the owner has accepted hide new ones |
| A config list of excepted groups or names | Visible in the warehouse | Another config table for a check-only rule |

## Decision
- `CELESTRAK_MEMBER_NAME_PREFIX = {"tdrss": "TDRS"}` in `sattrack_ingest/config.py`, landed every run as
  `raw_celestrak.group_config.GROUP_MEMBER_NAME_PREFIX` → `stg__celestrak__group_config.celestrak_group_member_name_prefix`.
- `int__celestrak__satellite_constellation` counts a member of a group with a prefix only when CelesTrak's
  `OBJECT_NAME` starts with it (case-insensitive). A member it drops can still take a later group in config order.
  The ISS keeps `flag_space_station` = 1 (D-043 reads the `stations` group, not `tdrss`).
- Warning check (D-037: emailed, never fails) `assert__int__celestrak__satellite_constellation__names_fit_group`:
  a constellation-kind membership whose CelesTrak name doesn't contain the group's prefix, else the group's most
  common leading word; and a prefix that matches none of its group's members (CelesTrak renamed them).
- No other group gets a prefix (the audit shows none mixes in other spacecraft).
- Exceptions to the check (owner, 24 Nov 2026) live only in the macro `helper__flag_member_name_fits_group`
  (`pipeline/transform/macros/celestrak/`), a `case when` the check calls, each branch with its reason and removal
  trigger:
  - **dmc is not checked.** CelesTrak's "Disaster Monitoring" group lists satellites of several programmes (BEIJING 1,
    HUANJING 1A/1B, YAOGAN-4, DEIMOS-1 beside UK-DMC 2 and DMC3); the owner keeps CelesTrak's membership, so those 5
    keep the "Disaster Monitoring" constellation.
  - **hulianwang also accepts names starting GUOWANG** (GUOWANG-30 OBJECT A..J on 22 Nov 2026).
  - Operator groups stay outside the check (by group kind, not in the macro).

## Evidence
- Group CSVs of fetch run 45061938995 (GitHub runner artifact, 22 Nov 2026), all 20 groups; audit above.
- The first six rows of `tdrss` are the test fixture `pipeline/ingestion/tests/fixtures/celestrak/tdrss.csv`.
- On those CSVs the models give `tdrss` 8 members (the TDRS satellites); HST, the ISS and NOAA 20 get no
  constellation. Without exceptions the check would warn on 13 rows (8 GUOWANG-30 objects in hulianwang, 5 dmc
  members); with the macro's exceptions it warns on none.
- Unit test `ut__int__celestrak__satellite_constellation__member_name_prefix`; the station test includes the ISS's
  tdrss membership; ingestion tests run the models and the check (with the macro rendered from its file) on the
  fixtures, including `test_name_check_exceptions_live_in_the_macro`: GUOWANG and the dmc members raise no warning,
  an unrelated name (HST) in hulianwang still does.

## Consequences
- 17 objects lose "Tracking and Data Relay Satellite System (TDRSS)" in `objects.json` on the next CelesTrak
  download; no contract change (`constellation` was already nullable).
- The check is quiet on today's data; a warning means a new misfit, not a known one.
- dmc is never name-checked while its exception stands: a non-disaster satellite CelesTrak added there would not be
  flagged.
- If CelesTrak renames the TDRS satellites, the prefix matches nothing, TDRSS disappears from the data and the
  check warns.

## Revisit when
- The name check flags a new group mixing in other spacecraft (it would need its own prefix, decided against this
  record).
- CelesTrak splits `tdrss` into relay satellites and users, or renames the TDRS satellites.
- Space-Track renames the GUOWANG objects (names starting HULIANWANG): remove the GUOWANG branch of the macro.
- CelesTrak narrows `dmc` to DMC-named satellites, or adds satellites that clearly aren't for disaster monitoring:
  remove or revisit the dmc branch.
- Any new exception is a new `when` in the macro, decided against this record.

## Related
D-026 (amended), D-037, D-043; #69.
