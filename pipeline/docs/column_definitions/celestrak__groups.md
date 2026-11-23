# Column definitions: CelesTrak GP groups

Part of the SatTrack column definitions; see `00_overview.md` for the rules and decisions.

## Batch 11c: CelesTrak GP groups (`raw_celestrak.gp_group_member`, `raw_celestrak.gp_group_index` → `stg__celestrak__*`) *(new source, D-026, 2026-11-23)*

Source: CelesTrak GP data formats documentation and GP index page (Dr T.S. Kelso), https://celestrak.org/NORAD/documentation/gp-data-formats.php ; https://celestrak.org/NORAD/elements/

**UNSOURCED wording, owner to confirm (2026-11-23).** CelesTrak is never fetched from a developer machine (D-008), and the fetch workflow's artifact held the group CSVs only, so the text of CelesTrak's documentation could not be read for this batch. The definitions below state only what the downloaded data shows (the query URL `gp.php?GROUP=<group>&FORMAT=csv` and the rows of fetch run 45061938995, 22 Nov 2026); they still need CelesTrak's own wording from the pages above. The member columns `satcat_id`, `object_name` and `object_id` are CelesTrak's CSV `NORAD_CAT_ID`, `OBJECT_NAME` and `OBJECT_ID`, the same OMM keywords as Space-Track GP, so they share the existing blocks.

| # | CelesTrak col | Proposed name | Proposed definition (from source) | SatTrack note |
|---|---|---|---|---|
| 1 | GROUP (query parameter) | `celestrak_group` | **UNSOURCED, owner to confirm.** The name of a CelesTrak GP group: the `GROUP` value in CelesTrak's query `gp.php?GROUP=<group>&FORMAT=csv`. From CelesTrak's GP index page and query URL. E.g. `starlink` (holds STARLINK-1008, NORAD 44714); `gps-ops` (GPS BIIR-5, NORAD 26407). | **Detail:** Case as CelesTrak writes it (`iridium-NEXT`). In `gp_group_member` it is the group the row was downloaded from; one object can be in several groups (e.g. NORAD 26407 is in `gps-ops` and `gnss`). |
| 2 | GROUP_TITLE (index page) | `celestrak_group_title` | **UNSOURCED, owner to confirm.** The title CelesTrak's GP index page shows for a group, as written there. From the GP index page, parsed by SatTrack at ingestion. E.g. "GPS Operational" for `gps-ops`. | **Detail:** Parsed from the page's HTML (`sattrack_ingest/celestrak.py`): the first text of the group's row that isn't a format label. A configured group without a title stops the update (the last copy stays). The parser has not yet been checked against the live page (PR for 3.8). |
| 3 | INDEX_POSITION (index page) | `celestrak_index_position` | **UNSOURCED, owner to confirm.** The group's position among the groups linked from CelesTrak's GP index page, counting from 1 in page order. From the GP index page. E.g. 1 for `last-30-days` on 22 Nov 2026. | **Detail:** Kept to show the page order the warning check reports in; not used in any rule. |
