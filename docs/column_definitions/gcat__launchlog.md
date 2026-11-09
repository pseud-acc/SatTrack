# Column definitions: GCAT orbital launch log

Part of the SatTrack column definitions; see `00_overview.md` for the rules and decisions.

## Batch 4: GCAT orbital launch log (`launchlog.tsv` → `stg__jsr__launchlog`)

Source: GCAT "Orbital Launch Log Column Descriptions", https://planet4589.org/space/gcat/web/cat/llog.html. Its columns "are copied from the basic GCAT files, combining data from the Launch Lists with data from the Object Catalogs". 2026-10-24 file: 31,980 rows, one per payload (every Type starts with P), 0 duplicate JCATs.

| # | GCAT col | Proposed name | Proposed definition (from source) | SatTrack note |
|---|---|---|---|---|
| 1 | Launch_Tag | `launch_tag` | (shared block, batch 1 #3) | Joins to the launch lists. |
| 2 | Launch_Date | `launch_datetime_utc` | UTC Gregorian calendar date of the launch. | The data includes time, e.g. `2026 Oct 23 2248:44`, so it's more precise than `gcat_launch_date`. Parsed with `gcat_date()`, keeping precision. |
| 3 | Piece | `cospar_id` | (shared block, batch 1 #4) | |
| 4 | Type | `sat_type` | (shared block, batch 1 #5). **Important:** when GCAT knows which satellites were on a launch but not which catalog number belongs to which, it matches them arbitrarily and sets the **9th character of SatType to `?`**. (The source page labels this column `SatType`.) | 724 rows have `?` in position 9. |
| 5 | — (derived from Type) | `flag_catalog_match_uncertain` | TRUE when character 9 of SatType is `?`, which GCAT documents as an arbitrary match between a named satellite and the launch's catalog slots. | New, derived in intermediate. Means the satellite's identity and catalog number may be swapped with another payload on the same launch. |
| 6 | Name | `gcat_name` | (shared block, batch 1 #6) | |
| 7 | PLName | `pre_launch_name` | (shared block, batch 1 #7) | |
| 8 | JCAT | `jcat` | (shared block, batch 1 #1) | PK. |
| 9 | SatOwner | `current_owner_code` | (shared block, batch 3 #10) The current owner of the payload if still in space, otherwise the owner at re-entry. | Same meaning as currentcat Owner, so one doc block. |
| 10 | SatState | `current_state_code` | (shared block, batch 3 #11) Country associated with the payload owner. | |
| 11 | LV_Type | `lv_type` *(existing)* | Name of the type of rocket used, as given in the GCAT LV table. | FK to launch vehicles. |
| 12 | Flight_ID | `flight_id` *(existing)* | Identifier for the particular launch, e.g. the launch vehicle serial number, or the mission number or name assigned by the launch agency. | |
| 13 | Platform | `launch_platform` | Mobile launch platform (e.g. a submarine or plane), if any. Usually blank. See https://planet4589.org/space/gcat/web/platforms/index.html. | Filled on 823 rows. |
| 14 | Launch_Site | `site_code` *(existing)* | Launch site the rocket went up from (see the GCAT Sites file). For air launches, the airport of the carrier plane's take-off. | v3 strips a trailing `?` (1 row in this file). |
| 15 | Launch_Pad | `launch_pad` | Specific location within the launch site. For air launches, the runway of the carrier plane's take-off. | |
| 16 | Ascent_Site | `ascent_site_code` | Site of the actual rocket launch from a Platform, when different from Launch_Site. For air launches, the drop site. | Filled on 147 rows. |
| 17 | Ascent_Pad | `ascent_pad` | Location of the actual rocket launch from a Platform, when different from Launch_Pad. | |
| 18 | Agency | `launch_agency_code` *(existing)* | OrgCode of the organisation responsible for launch services, often different from the payload owner. (The source page labels this column `Launch_Agency`.) | Composite/uncertain, split by `explode_org_codes()`. |
| 19 | LVState | `launch_agency_country` *(existing)* | Country (or equivalent) associated with the launch agency. | Feeds country resolution. |
| 20 | Launch_Code | `launch_code` | First letter = launch category (O orbital, D deep space, M military missile, T test rocket, A atmospheric, S suborbital, H high-altitude sounding rocket, R re-entry test, X launch from another world, Y suborbital crewed spaceplane). The rest = the launch success fraction: S success, F fail, U unknown, E pad explosion, or a percentage for partial success (e.g. OS80). GCAT says it's reliable for categories O and D. | Data: OS 30,267; OF 897; DS 446; OF40 117; …; **category `N` (`NS` 13, `NF` 2) → NULL** in `launch_category` (undocumented). The success part is still parsed. |
| 21 | — (derived) | `launch_category` / `launch_success_code` | First letter / remainder of Launch_Code, as above. | New, derived in intermediate. |
| 22 | LTCite | `launch_time_ref` | Citation that is the primary reference for the launch's existence and its launch time. See the GCAT Refs file. | |
