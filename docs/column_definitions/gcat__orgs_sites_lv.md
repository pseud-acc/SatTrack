# Column definitions: GCAT organisations, launch sites and launch vehicles

Part of the SatTrack column definitions; see `00_overview.md` for the rules and decisions.

## Batch 5: GCAT organisations, launch sites, launch vehicles (`orgs.tsv`, `sites.tsv`, `lv.tsv` → `stg__jsr__orgs`, `stg__jsr__sites`, `stg__jsr__lv`)

Sources:
- `orgs`: GCAT "Organizations Database", https://planet4589.org/space/gcat/web/orgs/index.html (4,144 rows on 2026-10-24; `Code` unique).
- `sites`: GCAT "Launch Origins Database", https://planet4589.org/space/gcat/web/sites/index.html (712 rows; `Site` unique).
- `lv`: GCAT "Launch Vehicle List", https://planet4589.org/space/gcat/web/lvs/lv/index.html (1,837 rows; **unique on `LV_Name` + `LV_Variant`**, with 200 duplicate names).

**v3 bug found:** `normalize_jsr_orgs` reads a column `State`, but the orgs file has `StateCode`. So `org_country_code` is **NULL for all 4,131 rows** in `dim_org` (2026-10-04 DB). It's the same class of bug as `Tx`/`EndTxDate`, and the schema-drift source test would catch it.

GCAT's own guidance on names: `ShortEName` is a "Short name in English. Useful for summary information. Can be omitted when ShortName is itself English" (sites page). So display names should prefer the English name and fall back to the host-language one; that derived rule is in batch 8.

| # | GCAT col | Proposed name | Proposed definition (from source) | SatTrack note |
|---|---|---|---|---|
| 1 | orgs.Code | `org_code` *(existing)* | GCAT Org Code for the organisation in a particular phase (time period): a unique string of 1–8 characters (digits, upper-case letters, dash), e.g. `NASA`, `I-ESRO`. Usually refers to a single operating location (e.g. NASA-Goddard), not the parent agency. | PK. Target of every owner/manufacturer/agency code. |
| 2 | orgs.UCode | `org_ucode` | "Unified" Org Code shared by all phases of the same organisation, e.g. FORDA for Philco WDL → Ford Aerospace → Space Systems Loral → Maxar. Usually the Code of the first phase. For current countries it's usually the Internet TLD (CN), or the single-letter code for EU countries (D, F). | Lets the app group an organisation across renames. |
| 3 | orgs.StateCode | `org_state_code` *(was `org_country_code`)* | Org Code of the nation-state, IGO or other polity responsible for the organisation, normally the country it's located in ("host country"). Must be an org of type CY, IGO or AP. | **Fixes the v3 bug** (read from `State`, which doesn't exist). Renamed to match `site_state_code`. |
| 4 | orgs.Type | `org_type` | Organisation roles, a slash-separated set (e.g. `LV/E`). Codes include CY country, CYP province, IGO intergovernmental, AP astronomical polity, E engine maker, LV launch-vehicle maker, PL payload maker, LA launch agency, O payload owner, S suborbital operator, P parent org, and LS/LP/LC/LZ for launch origins. GCAT: "somewhat patchy… I do not recommend relying on data in this column with the exception of the special values CY, IGO and AP". | Use only to identify country-like orgs (CY, IGO, AP). Never filter operators by role. |
| 5 | orgs.Class | `org_class` | Organisation class: A academic/amateur/non-profit, B business/commercial, C civil government, D defence/military/intelligence. Usually, but not always, the same as the class of its satellites. | Same codes as psatcat `ownership_class`, so it shares the label seed. |
| 6 | orgs.TStart | `org_start_date` | Start of this organisation phase (e.g. founding), in Vague Date format. Null = unknown. | |
| 7 | orgs.TStop | `org_stop_date` | End of this phase (e.g. closed or renamed), in Vague Date format. Null = "still in operation, or assumed to be so". | `-` and `*` both mean NULL (still operating). |
| 8 | orgs.ShortName | `org_short_name` *(existing)* | Short ASCII name suitable for labels and tables, nominally transliterated from the host country's language. | v3 coalesced it with ShortEName in staging. That moves to batch 8's display rule, so staging keeps both columns. |
| 9 | orgs.Name | `org_full_name` *(existing)* | Full name (up to 80 ASCII characters), transliterated from the host country's language. | |
| 10 | orgs.Location | `org_location` *(existing)* | Approximate location (e.g. city), often as UrbanArea-Suburb, e.g. "Los Angeles-El Segundo". | |
| 11 | orgs.Longitude | `org_longitude` | Longitude of the location, degrees east. | |
| 12 | orgs.Latitude | `org_latitude` | Latitude of the location, degrees north. | |
| 13 | orgs.Error | `org_location_error_deg` | Error in longitude/latitude, in degrees. | |
| 14 | orgs.Parent | `org_parent_code` | Org Code of the organisation this org is part of. | FK to `org_code`, at warn level. |
| 15 | orgs.ShortEName | `org_short_name_en` | Short name in English. | Filled for only 444 of 4,144 rows. |
| 16 | orgs.EName | `org_full_name_en` | Full name in English. | 1,398 of 4,144. |
| 17 | orgs.UName | `org_full_name_unicode` | Full name in Unicode, host language. | |
| 18 | sites.Site | `site_code` *(existing)* | Org Code for the launch site, or for this time phase of it if the site changed name. | PK. FK target of launchlog `Launch_Site`. |
| 19 | sites.Code | `site_legacy_code` | Blank entry, kept for back compatibility. | Always `-`. Kept 1:1 in staging and excluded from intermediate. |
| 20 | sites.UCode | `site_ucode` | Unified Org Code for all phases of the launch site. | Not unique. v3 was right not to use it as the key. |
| 21 | sites.Type | `site_type` | Site type: LS launch site (land-based), LC launch cruise (an expedition with multiple sea launch points), LZ launch zone (a compact zone of air or sea launch points). | Accepted values LS, LC, LZ. |
| 22 | sites.StateCode | `site_state_code` *(was `site_country_code`)* | Org Code of the nation-state, IGO or other polity responsible for the site, normally the country it's located in. Must be a CY, IGO or AP org in the Organizations database. | Decided 2026-10-25: exposed as `site_state` (e.g. Kourou = GUF, Baikonur = RU/SU). |
| 23 | sites.TStart | `site_start_date` | Start of this site phase, in Vague Date format. `-`/`*` = unknown. | |
| 24 | sites.TStop | `site_stop_date` | End of this site phase. `-`/`*` = still in operation, or assumed to be so. | |
| 25 | sites.ShortName | `site_short_name` *(existing)* | Short ASCII name suitable for labels, nominally transliterated from the host language. | |
| 26 | sites.Name | `site_name` *(existing)* | Full name (up to 80 ASCII characters), transliterated, host language. "Where known, this is the formal name of the launch site." | Its last part (e.g. "Kazakstan") seeds `site_location_country` (batch 7). |
| 27 | sites.Location | `site_location` | City and locality of the launch site. | Filled on 339 of 712. |
| 28 | sites.Longitude | `site_longitude` *(existing)* | Geographic longitude, east-positive, decimal degrees. For sites with several pads the position is "a bit arbitrary". | |
| 29 | sites.Latitude | `site_latitude` *(existing)* | Geographic latitude, decimal degrees. | |
| 30 | sites.Error | `site_location_error_deg` | Uncertainty of the site location. | GCAT gives no unit for sites; degrees by analogy with orgs. |
| 31 | sites.Parent | `site_operator_code` | Org Code of the organisation operating the launch site, when non-empty. | FK to `org_code`. |
| 32 | sites.ShortEName | `site_short_name_en` | Short name in English. "Useful for summary information. Can be omitted when ShortName is itself English." | |
| 33 | sites.EName | `site_full_name_en` | Full name in English. | |
| 34 | sites.Group | `site_group` | Currently groups ocean launch sites, lunar sites and some unknown V2 launch areas. "Likely to be repurposed in future releases." | Don't build logic on it. The schema-drift test watches it. |
| 35 | sites.UName | `site_full_name_unicode` | Unicode version of the full name in the parent organisation's language. | |
| 36 | lv.LV_Name | `lv_name` *(existing)* | Name of the launch vehicle. GCAT uses the name in use by the launch agency at the time of launch. | Joins to launchlog `LV_Type`. Not unique alone (see the key note above). |
| 37 | lv.LV_Family | `lv_family` *(existing)* | Launch vehicle family, defined by the base (first) stage. A new family starts with "a change in the tankage diameter" (families page, https://planet4589.org/space/gcat/web/lvs/family/index.html). | Hidden grouping key. Not a brand: e.g. Zenit includes Antares. |
| 38 | lv.LV_Manufacturer | `lv_manufacturer_code` *(existing)* | Org Code of the manufacturer (see the Orgs file). | Composite/uncertain, split by `explode_org_codes()`. |
| 39 | lv.LV_Variant | `lv_variant` | Distinguishes different launch vehicles with the same name, e.g. Vanguard variants with different third stages. | Part of the staging PK (`lv_name`, `lv_variant`). |
| 40 | lv.LV_Alias | `lv_alias` | Alternative name for the same vehicle, e.g. Taurus 1110 has the alias "ARPA Taurus", meaning the separate ARPA Taurus entry is the same vehicle under an earlier name. | Filled on 23 rows. |
| 41 | lv.LV_Min_Stage | `lv_min_stage` | Minimum stage number. Usually 1, sometimes 0 for strap-on boosters, occasionally -1. `A` marks air-launch platforms. Since Aug 2026, R-7 (Soyuz) boosters are stage 0 and the core is stage 1. | 2026-10-24 data has only `1` (1,402), `0` (427) and `-1` (8); no `A` yet. Text in staging, and intermediate casts to integer with `A` mapped to NULL plus `flag_air_launch_platform`. |
| 42 | lv.LV_Max_Stage | `lv_max_stage` | Maximum stage number. | |
| 43 | lv.Length | `lv_length_m` | Approximate length in metres. It can vary with payload and fairing. | |
| 44 | lv.LFlag | `lv_length_flag` | **UNSOURCED.** Not described on the LV page. In the object catalogs, `?` means an estimate. | **Staging only** (undocumented by GCAT). Values are only `?` or blank. |
| 45 | lv.Diameter | `lv_diameter_m` | Diameter in metres. | |
| 46 | lv.DFlag | `lv_diameter_flag` | **UNSOURCED**, as LFlag. | **Staging only** (undocumented by GCAT). Values are only `?` or blank. |
| 47 | lv.Launch_Mass | `lv_launch_mass_t` | Launch mass in **tonnes**. | Unit differs from satellite masses (kg). |
| 48 | lv.MFlag | `lv_launch_mass_flag` | **UNSOURCED**, as LFlag. | **Staging only** (undocumented by GCAT). Values are only `?` or blank. |
| 49 | lv.LEO_Capacity | `lv_leo_capacity_kg` | Approximate LEO payload capacity in kg. Only provided for some orbital vehicles, and "especially tentative". | |
| 50 | lv.GTO_Capacity | `lv_gto_capacity_kg` | Approximate GTO payload capacity in kg. Only for some orbital vehicles, and "especially tentative". | |
| 51 | lv.TO_Thrust | `lv_takeoff_thrust_kn` | Launch thrust in kN. | |
| 52 | lv.Class | `lv_class` | Vehicle type: O orbital, D deep space, M missile, R research rocket, V re-entry test, X exoatmospheric test, Y exoatmospheric weather rocket, A endoatmospheric missile, C cruise missile, Q endoatmospheric re-entry test, T endoatmospheric test/research, W endoatmospheric weather rocket. | **`B` (99 rows) becomes NULL in intermediate** (undocumented, decided 2026-10-25). Raw stays in staging. |
| 53 | lv.Apogee | `lv_max_apogee_km` | Estimated maximum apogee in km, often a rough order-of-magnitude estimate. | |
| 54 | lv.Range | `lv_range_km` | For some IRBMs/ICBMs, "an extra figure representing the range". | Unit not stated (km assumed). **Partly sourced.** |
| 55 | lv.GenericName | `lv_generic_name` | **UNSOURCED definition** (the column isn't described on the LV page). The values are GCAT's generic vehicle names, e.g. Falcon 9, CZ-6, Soyuz. | Kept as a **reference column** (decided 2026-10-25), labelled "undocumented column". The filter uses `lv_brand`. |
