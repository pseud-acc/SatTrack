# Column definitions: GCAT current catalog

Part of the SatTrack column definitions; see `00_overview.md` for the rules and decisions.

## Batch 3: GCAT current catalog (`currentcat.tsv` → `stg__jsr__currentcat`)

Source: GCAT "Current Object Catalog Column Descriptions", https://planet4589.org/space/gcat/web/cat/curcols.html. In GCAT's words, currentcat "gives information on the current status of each object, including the most recent orbital data for those objects still in orbit". It is derived from the main catalogs. 2026-10-24 file: 83,576 rows, 0 duplicate JCATs. **Several columns mean something different here than in satcat** (current owner, most recent orbit, first separation, descent), so they get their own names.

| # | GCAT col | Proposed name | Proposed definition (from source) | SatTrack note |
|---|---|---|---|---|
| 1 | JCAT | `jcat` | (shared block, batch 1 #1) | PK. 0 duplicates in the 2026-10-24 file. |
| 2 | DeepCat | `deepcat_jcat` | **UNSOURCED.** Not described on curcols.html. The values are deepcat JCATs (`D00009`…), and the JCAT page defines the D prefix as the deep space catalog. | **Staging only** (undocumented by GCAT). Filled on 1,210 of 83,576 rows. |
| 3 | Satcat | `satcat_ref` | (shared block, batch 1 #2) | |
| 4 | Piece | `cospar_id` | (shared block, batch 1 #4) | |
| 5 | Active | `activity_type` *(existing)* | Single-letter object type: A active satellite, C component, D debris, P inactive payload, R rocket stage, Z spurious entry. Except for A, usually the same as the first letter of Type. (The source page labels this column `Ac`.) | Data: D 29,190; A 16,955; C 14,975; P 14,145; R 8,303; Z 8. **The current test accepts `S`, which GCAT doesn't define and which never occurs.** Accepted values become A, C, D, P, R, Z. |
| 6 | Type | `sat_type` | (shared block, batch 1 #5) | |
| 7 | Name | `gcat_name` | (shared block, batch 1 #6) | |
| 8 | LDate | `gcat_launch_date` | (shared block, batch 1 #8) | |
| 9 | Parent | `parent_ref` | (shared block, batch 1 #9) | |
| 10 | Owner | `current_owner_code` | OrgCode of the organisation that **currently** owns the object if it's still in space, otherwise the owner at re-entry. In the primary catalogs, by contrast, the owner is the one at the start of the listed phase. | Not the same as satcat `owner_code`, hence the new name. |
| 11 | State | `current_state_code` | Country (or equivalent) associated with the current owner. | |
| 12 | SDate | `first_separation_date` | UTC time when the object **first** separated from its parent, in Vague Date format. Later phases (dockings, undockings) aren't given here. Useful for telling when debris appeared in orbit. | Not the same as satcat `phase_start_date`. |
| 13 | ExpandedStatus | `current_status` *(existing)* | Current status of the object, derived from the Status and Dest fields of its most recent phase in the object catalogs. Meant to be self-explanatory, e.g. "In Earth orbit", "Reentered Earth atmosphere", "Attached to A08069 ISS Generic Cargo". | Free text, so no accepted-values test. |
| 14 | DDate | `descent_date` | UTC time when the object re-entered the atmosphere or landed, in Vague Date format. **Blank = the object is still in orbit.** | Not the same as satcat `phase_end_date`. GCAT's documented in-orbit signal; see `flag_in_orbit` below. |
| 15 | — (composite) | `flag_in_orbit` *(existing)* | (shared block, batch 8 #5) The GCAT-only in-orbit signal (DDate blank) is `flag_gcat_in_orbit` (batch 9a). | **Corrected 2026-11-08:** the master holds only objects in the GP feed, so `flag_in_orbit` is TRUE on every row and the DDate fallback no longer applies. **v3 bug (history):** v3 used Active in A/P/S. That marked 10,516 re-entered payloads as in orbit and left out every in-orbit debris object, rocket body and component. |
| 16 | ODate | `current_orbit_epoch` | UTC epoch of the most recent orbital data, in Vague Date format. | Not the same as satcat `canonical_orbit_epoch`. |
| 17 | Period | `current_period_min` | **UNSOURCED.** Not described on curcols.html. The values look like an orbital period in minutes (e.g. 89.768). | **Staging only** (undocumented by GCAT). Filled on 36,091 rows. Orbital period comes from GP `PERIOD` instead. |
| 18 | Perigee | `current_perigee_km` | Conventional perigee height of the most recent orbit in km: perigee radius minus the central body's equatorial radius. | |
| 19 | PF | `current_perigee_flag` | Named on curcols.html but not defined there. In the object catalog, PF `?` = the value is a guess (cols.html). | Definition taken from cols.html. |
| 20 | Apogee | `current_apogee_km` | Conventional apogee height of the most recent orbit in km: apogee radius minus the central body's equatorial radius. | |
| 21 | AF | `current_apogee_flag` | As PF: `?` = the value is a guess (cols.html). | |
| 22 | Inc | `current_inclination_deg` | Inclination of the most recent orbit in degrees. Earth orbits are relative to the equator of date (TEME), heliocentric orbits to the J2000 ecliptic, and other bodies to their IAU equator. | |
| 23 | IF | `current_inclination_flag` | As PF: `?` = the value is a guess (cols.html). | |
| 24 | OpOrbit | `current_orbit_type_raw` | Not described on curcols.html. In the object catalog it is the orbit type of the canonical orbit, with values from https://planet4589.org/space/gcat/web/intro/orbits.html. Here it presumably describes the current orbit. | **Staging only.** Its meaning in currentcat (current vs canonical orbit) isn't documented. `orbit_type` uses satcat `OpOrbit` (documented). |
