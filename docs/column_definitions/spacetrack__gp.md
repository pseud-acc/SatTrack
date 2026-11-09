# Column definitions: Space-Track GP

Part of the SatTrack column definitions; see `00_overview.md` for the rules and decisions.

## Batch 6: Space-Track GP (`raw_spacetrack.gp` → `stg__spacetrack__gp`)

Sources:
- Space-Track documentation and FAQ, https://www.space-track.org/documentation. The logged-in version (fetched 2026-10-25 with the user's account) adds the gp field list and the boxscore / launch_site class descriptions. It says GP formats "use the same keywords and definitions for OMM as provided in the Orbit Data Messages (ODM) CCSDS Recommended Standard 502.0-B-3".
- CCSDS 502.0-B-3 "Orbit Data Messages" (April 2023), Tables 4-1 to 4-3 and §4.2.4.6–4.2.4.9, https://public.ccsds.org/Pubs/502x0b3e1.pdf.

Space-Track also documents that "many analyst satellite objects' catalog numbers in the 70K – 99K range do not have much metadata."

2026-10-04 v3 snapshot: 31,989 rows, one per `NORAD_CAT_ID`. The query is `decay_date/null-val/epoch/>now-10`, so these are on-orbit objects with an element set from the last 10 days. Space-Track field names are upper-case in raw and snake_case in staging. v3 names are kept where they exist.

| # | GP key | Proposed name | Proposed definition (from source) | SatTrack note |
|---|---|---|---|---|
| 1 | CCSDS_OMM_VERS | `ccsds_omm_vers` | OMM format version "x.y": y increments for corrections and minor changes, x for major changes. (CCSDS T4-1) | |
| 2 | COMMENT | `omm_comment` | Free-text comment in the OMM header. (CCSDS T4-1) | |
| 3 | CREATION_DATE | `creation_date` *(existing)* | File creation date/time in UTC. (CCSDS T4-1) | Space-Track also uses it to query GP history. |
| 4 | ORIGINATOR | `originator` *(existing)* | Creating agency or operator. (CCSDS T4-1) | Data: `18 SPCS` for 100%. |
| 5 | OBJECT_NAME | `object_name` *(existing)* | Name of the spacecraft whose mean-element orbit data is given. CCSDS recommends names from the UN Office for Outer Space Affairs designator index, or `UNKNOWN`. (CCSDS T4-2) | **Shown in the app** (decided 2026-10-25). Analyst objects hold "TBA - TO BE ASSIGNED". |
| 6 | OBJECT_ID | `object_id` *(existing)* | Object identifier, recommended to be the international (COSPAR) designator in the format YYYY-NNNP{PP}: year of launch, three-digit launch serial number, then at least one capital letter for the piece. `UNKNOWN` if not available. (CCSDS T4-2) | COSPAR fallback key for the GCAT link. Space-Track FAQ: well-tracked objects use `YYYY-000A` (year catalogued, launch number 000). |
| 7 | CENTER_NAME | `center_name` | Origin of the OMM reference frame, a natural solar-system body (e.g. EARTH). For TLE-based OMMs it must be EARTH. (CCSDS T4-2, §4.2.4.6) | Accepted value `EARTH`. |
| 8 | REF_FRAME | `ref_frame` | Reference frame of the Keplerian elements. NORAD TLEs and SGP outputs are defined in TEME of Date, which TLE-based OMMs must use. (CCSDS T4-2, §4.2.4.9) | Accepted value `TEME`. |
| 9 | TIME_SYSTEM | `time_system` | Time system of the elements. UTC for TLE-based OMMs. (CCSDS T4-2, §4.2.4.6) | Accepted value `UTC`. |
| 10 | MEAN_ELEMENT_THEORY | `mean_element_theory` *(existing)* | The mean element theory, i.e. the proper method for propagating the state (e.g. SGP, SGP4, SGP4-XP, DSST). (CCSDS T4-2) | Data: `SGP4` for 100%. Accepted values guard the app's sgp4 propagator. |
| 11 | EPOCH | `epoch` *(existing)* | Epoch of the mean Keplerian elements. "All values in the OMM are 'at epoch'." (CCSDS T4-3, §4.2.4.3) | Source of `tle_age_days`. Recent-data test within 3 days. |
| 12 | MEAN_MOTION | `mean_motion` *(existing)* | Keplerian mean motion in revolutions per day (used instead of semi-major axis when the theory is SGP/SGP4). (CCSDS T4-3) | Feeds `classify_orbit_class()` (GEO test 0.99–1.01). |
| 13 | ECCENTRICITY | `eccentricity` *(existing)* | Eccentricity (dimensionless). (CCSDS T4-3) | Test: 0 to just under 1. |
| 14 | INCLINATION | `inclination` *(existing)* | Inclination, in degrees. (CCSDS T4-3) | Test: 0–180. |
| 15 | RA_OF_ASC_NODE | `ra_of_asc_node` *(existing)* | Right ascension of the ascending node, in degrees. (CCSDS T4-3) | |
| 16 | ARG_OF_PERICENTER | `arg_of_pericenter` *(existing)* | Argument of pericenter, in degrees. (CCSDS T4-3) | |
| 17 | MEAN_ANOMALY | `mean_anomaly` *(existing)* | Mean anomaly, in degrees. (CCSDS T4-3) | |
| 18 | EPHEMERIS_TYPE | `ephemeris_type` *(existing)* | TLE ephemeris type, default 0. "Some sources suggest" 0 SGP, 2 SGP4, 3 PPT3, 4 SGP4-XP, 6 Special Perturbations. (CCSDS T4-3, §4.2.4.7) | Data: `0` for 100%. |
| 19 | CLASSIFICATION_TYPE | `classification_type` *(existing)* | Classification, default U. "Some sources suggest" U unclassified, S secret. (CCSDS T4-3, §4.2.4.7) | Data: `U` for 100%. Accepted value `U`. |
| 20 | NORAD_CAT_ID | `satcat_id` *(existing)* | NORAD Catalog Number ("Satellite Number"), an integer of up to nine digits. (CCSDS T4-3) | PK. In TLE lines, numbers ≥ 100,000 use Alpha-5 (`A0001` = 100001). |
| 21 | ELEMENT_SET_NO | `element_set_no` *(existing)* | Element set number for this satellite. "Normally incremented sequentially but may be out of sync if it is generated from a backup source. Used to distinguish different TLEs." (CCSDS T4-3) | |
| 22 | REV_AT_EPOCH | `rev_at_epoch` *(existing)* | Revolution number at epoch. (CCSDS T4-3) | |
| 23 | BSTAR | `bstar` *(existing)* | Drag-like ballistic coefficient required by SGP4 (the SGP4 drag parameter), in 1/Earth radii. (CCSDS T4-3) | |
| 24 | MEAN_MOTION_DOT | `mean_motion_dot` *(existing)* | First time derivative of the mean motion (a drag term), in rev/day². (CCSDS T4-3) | CCSDS note: when sourced from a TLE, divide by 2 to match the SGP Taylor-series term. **Not used for propagation** (sgp4 reads the TLE lines). |
| 25 | MEAN_MOTION_DDOT | `mean_motion_ddot` *(existing)* | Second time derivative of the mean motion (a drag term), in rev/day³. (CCSDS T4-3) | As above, divide by 6. |
| 26 | SEMIMAJOR_AXIS | `semimajor_axis` *(existing)* | Semi-major axis in km, derived by Space-Track from mean motion: a = (μ / (n·2π/86400)²)^(1/3), with μ = 398600.4418. (Space-Track FAQ) | Derived by Space-Track, not an OMM element in GP. |
| 27 | PERIOD | `orbital_period` *(existing)* | Orbital period in minutes = 1440 / mean motion. (Space-Track FAQ) | Feeds `classify_orbit_class()`. |
| 28 | APOAPSIS | `apoapsis` *(existing)* | Apogee height in km = a·(1 + e) − 6378.135. (Space-Track FAQ) | A height above Earth's equatorial radius, the same convention as GCAT Perigee/Apogee. The FAQ notes values "may not match exactly" the SATCAT's. |
| 29 | PERIAPSIS | `periapsis` *(existing)* | Perigee height in km = a·(1 − e) − 6378.135. (Space-Track FAQ) | Test: apoapsis ≥ periapsis. |
| 30 | OBJECT_TYPE | `object_type` *(existing)* | Object type: "Payload, Rocket Body, Debris, Unknown" (Space-Track logged-in API documentation (gp class), fetched 2026-10-25). The gp model definition types it as `varchar(12)`. | Data: 18,701 / 10,053 / 2,041 / 1,194. The composite with GCAT Type (field review) has its own block, `object_type__resolved` (batch 8 #4). |
| 31 | RCS_SIZE | `rcs_size` *(existing)* | Scaled radar cross-section: Small (< 0.1 m²), Medium (0.1–1 m²), Large (> 1 m²). Only scaled values have been published since 18 Aug 2014. (Space-Track FAQ) | Data: LARGE 18,786; MEDIUM 9,494; SMALL 2,957; NULL 752. The FAQ writes the bounds in "m"; they're areas. |
| 32 | COUNTRY_CODE | `country_code` *(existing)* | "Country code" (Space-Track logged-in API documentation (gp class), fetched 2026-10-25). **The codes are defined by the Space-Track `boxscore` class** ("accounting of man-made objects… grouped by country/organization"), which names all 122 codes, e.g. PRC = "PEOPLES REPUBLIC OF CHINA", CIS = "COMMONWEALTH OF INDEPENDENT STATES", TBD = "TO BE DETERMINED/UNKNOWN". `char(6)`. | Same code list as CelesTrak OWNER (98.4% equal). Feeds `owner_country`. No `UNKN` in the current snapshot; analyst objects have NULL. |
| 33 | LAUNCH_DATE | `launch_date` *(existing)* | "Launch date" (Space-Track logged-in API documentation (gp class), fetched 2026-10-25). `date`. FAQ: well-tracked objects get 1 January of the year catalogued. | The composite with GCAT LDate (field review) has its own block, `launch_date__resolved` (batch 8 #10). |
| 34 | SITE | `launch_site` *(existing)* | "Launch site" (Space-Track logged-in API documentation (gp class), fetched 2026-10-25). **Codes defined by the Space-Track `launch_site` class** ("list of launch sites found in satellite catalog records", 45 codes, e.g. FRGUI = "FRENCH GUIANA", TTMTR = "TYURATAM MISSILE AND SPACE COMPLEX"). `char(5)`. `UNKN` for well-tracked objects (FAQ). | Fallback for the site fields. |
| 35 | DECAY_DATE | `decay_date` *(existing)* | "Decay date" (Space-Track logged-in API documentation (gp class), fetched 2026-10-25). `date`. | Always NULL given the on-orbit query. |
| 36 | FILE | `file_no` *(existing)* | "File identifier for groups uploaded together" (Space-Track logged-in API documentation (gp class), fetched 2026-10-25). `bigint`. | 796 distinct values in the snapshot. |
| 37 | GP_ID | `gp_id` *(existing)* | "Unique ephemerides identifier" (Space-Track logged-in API documentation (gp class), fetched 2026-10-25). `int`, not null. | Unique per row; test as a secondary key. |
| 38 | TLE_LINE0 | `tle_line_0` *(existing)* | Title line of the element set, one of the "TLE lines as fields (TLE_LINE0, TLE_LINE1, TLE_LINE2)" in JSON/CSV/HTML output (Space-Track logged-in API documentation (gp class), fetched 2026-10-25). `varchar(27)`. |  |
| 39 | TLE_LINE1 | `tle_line_1` *(existing)* | First line of the TLE. TLE and 3LE formats use Alpha-5 for catalog numbers ≥ 100,000. (Space-Track FAQ: Alpha-5, TLE checksum) | Tests: starts `1 `, 69 characters, checksum, catalog number = `satcat_id` after Alpha-5 decoding. |
| 40 | TLE_LINE2 | `tle_line_2` *(existing)* | Second line of the TLE. (Space-Track FAQ) | Tests: starts `2 `, 69 characters, checksum. |

---

## Batch 9b: Space-Track values kept beside the resolved value (added 2026-11-08)

Source: Space-Track logged-in API documentation (gp class), https://www.space-track.org/documentation (fetched 2026-10-25).

The master resolves some fields across Space-Track and GCAT (batch 8). These columns keep the GP value unchanged next to the resolved one, so the choice can be audited.

| # | GP key | Proposed name | Proposed definition (from source) | SatTrack note |
|---|---|---|---|---|
| 1 | COUNTRY_CODE | `spacetrack_country_code` | GP `COUNTRY_CODE` unchanged: "Country code", with the codes defined by the Space-Track `boxscore` class (batch 6 #32). | In `int__xsrc__satellite_gcat_matched` and `fct__satellite_master`. Kept beside `owner_country` (batch 8 #11), which is resolved from it. |
| 2 | LAUNCH_DATE | `spacetrack_launch_date` | GP `LAUNCH_DATE` unchanged: "Launch date" (batch 6 #33). FAQ: well-tracked objects get 1 January of the year catalogued. | In `int__xsrc__satellite_gcat_matched`. Kept beside `launch_date` (batch 8 #10), which falls back to GCAT. |
| 3 | OBJECT_TYPE | `spacetrack_object_type` | GP `OBJECT_TYPE` unchanged: "Payload, Rocket Body, Debris, Unknown" (batch 6 #30). | In `int__xsrc__satellite_gcat_matched`. Kept beside `object_type` (batch 8 #4), which falls back to GCAT when this is UNKNOWN. |
