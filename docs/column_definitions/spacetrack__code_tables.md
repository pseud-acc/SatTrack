# Column definitions: Space-Track code tables

Part of the SatTrack column definitions; see `00_overview.md` for the rules and decisions.

## Batch 6b: Space-Track code tables (`raw_spacetrack.boxscore`, `raw_spacetrack.launch_site` → `stg__spacetrack__boxscore`, `stg__spacetrack__launch_site`) *(new sources, decided 2026-10-25)*

Source: Space-Track logged-in API documentation (boxscore and launch_site classes), https://www.space-track.org/documentation (fetched 2026-10-25).

These use the same Space-Track login and are fetched once a day (both tiny). They give **Space-Track's own meaning for every `COUNTRY_CODE` and `SITE` value**. Coverage is complete: 104 of 104 country codes and 34 of 34 site codes used in GP, i.e. all 31,478 objects with a code. They're used for meaning, coverage tests and lineage. **Display names come from pycountry (countries) and GCAT (sites)**, because the Space-Track names are mixed-case, use legacy names ("TYURATAM" for Baikonur), include organisations among the "countries", and contain a few source typos ("MYNAMAR", "Taiyaun"). (Correction 2026-10-25: an earlier note said the SES name had broken characters; the data holds a correct É and the Windows console mis-displayed it).

| # | Space-Track col | Proposed name | Proposed definition (from source) | SatTrack note |
|---|---|---|---|---|
| 1 | boxscore.SPADOC_CD | `country_code` | The Space-Track country/organisation code used in GP `COUNTRY_CODE` (boxscore: "grouped by country/organization"). | PK. A relationships test checks that every GP `country_code` exists here (error). |
| 2 | boxscore.COUNTRY | `spacetrack_country_name` | Space-Track's name for the code, e.g. "PEOPLES REPUBLIC OF CHINA", "EUROPEAN SPACE AGENCY". | 87 of 122 exactly match a pycountry name; the other 35 go in `country_alias_map.csv` (reviewed once). A code mapped to NULL there is a non-country owner. |
| 3 | boxscore.ORBITAL_* / DECAYED_* counts | `boxscore_*` | Counts of objects per code by type and status (boxscore: "accounting of man-made objects that have been or are in orbit"). | Staging only. Could feed a reconciliation test against our own counts. |
| 4 | launch_site.SITE_CODE | `spacetrack_site_code` | The Space-Track launch site code used in GP `SITE` ("list of launch sites found in satellite catalog records"). | PK. Every GP `launch_site` must exist here. |
| 5 | launch_site.LAUNCH_SITE | `spacetrack_site_name` | Space-Track's name for the site, e.g. "AIR FORCE EASTERN TEST RANGE", "FRENCH GUIANA". | No coordinates. Fallback label only; GCAT sites stay the display and map source. |
