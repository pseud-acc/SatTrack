# Column definitions: GCAT object and payload catalogs

Part of the SatTrack column definitions; see `00_overview.md` for the rules and decisions.

## Batch 1: GCAT object catalog (`satcat.tsv` → `stg__jsr__satcat`)

Source: GCAT "Object Catalog Column Descriptions", https://planet4589.org/space/gcat/web/cat/cols.html (GCAT release 1.8.8, data update 2026-10-24).

**Also applies to `satcat100k.tsv`** (GCAT "satcat100k (Extended)", objects with SATCAT number ≥ 100,000, same header), which feeds `stg__jsr__satcat100k`. Same doc blocks, with `_source_file` telling the two apart.

| # | GCAT col | Proposed name | Proposed definition (from source) | SatTrack note |
|---|---|---|---|---|
| 1 | JCAT | `jcat` *(existing)* | GCAT's unique alphanumeric identifier for a space object: one prefix letter for the catalog it belongs to (A auxcat, C csocat, D deepcat, F ftocat, L lcat, R rcat, S standard, T tmpcat) followed by a 5- or 9-digit sequence number. S-catalog numbers match US SATCAT numbers one-to-one (S46112 = SATCAT 46112). | PK. Test regex `^[A-Z]\d+$`. |
| 2 | Satcat | `satcat_ref` | For objects in the US SATCAT, the integer US SATCAT number. One SATCAT number can cover several attached GCAT objects. Objects without a SATCAT entry hold a code giving the reason instead (e.g. `NNA` none assigned, `NNA A` remained attached, `NSO` suborbital). | Text, because of the NNA/NSO codes. Not the same as Space-Track `satcat_id`. |
| 3 | Launch_Tag | `launch_tag` | Identifier for the launch. For orbital launches, the international (COSPAR) designation of the launch. Otherwise a pseudo-COSPAR `yyyy-Xnnn` assigned by GCAT. It matches the launch tag in the GCAT launch lists and can be used to join objects to launches. | |
| 4 | Piece | `cospar_id` *(existing)* | Piece designation of the object. For objects in the US SATCAT, this is the COSPAR (international) designation, e.g. `2020-032A`. Its launch part usually, but not always, matches Launch_Tag. | Join key to Space-Track `OBJECT_ID`. |
| 5 | Type | `sat_type` | SatType string (see https://planet4589.org/space/gcat/web/intro/type.html). At the coarsest level: payload (P), rocket stage (R), component (C) or debris (D). | First-letter accepted values P/R/C/D. **`Z…` (28 rows) → NULL** for the derived type (decided 2026-10-25). Raw stays in staging. |
| 6 | Name | `gcat_name` | GCAT's recommended name for the object, based on the owner/operator's name. `X part` = an unidentified component that separated from X. `deb X` = debris from the breakup of X. | Kept separate from Space-Track `object_name`. |
| 7 | PLName | `pre_launch_name` *(existing)* | Payload Name: an alternative name, usually the name used by the manufacturer before launch. On some debris it holds `RCS <n>` (radar cross-section in m², unreliable). `[UNID…` marks unidentified debris that may be assigned to the wrong launch. | |
| 8 | LDate | `gcat_launch_date` | Launch date in UTC, to 1-day precision. More precise launch times are in the launch lists. | Separate from Space-Track `launch_date`. |
| 9 | Parent | `parent_ref` | At the start of the current phase, either the parent object the object is attached to (an Extended JCAT ID, sometimes with a port suffix) or the central body whose sphere of influence it is leaving. A trailing `*` warns that the Piece designation may not match the parent's launch. | |
| 10 | SDate | `phase_start_date` | Separation date (phase start date): the UTC start of the current phase, usually when the object separated from its parent. In GCAT's Vague Date format. | Parsed with `gcat_date()` and a precision flag. |
| 11 | Primary | `central_body` | The central body for the current phase (usually Earth), named as in the GCAT Worlds file. | |
| 12 | DDate | `phase_end_date` | Descent date (phase end date): the UTC end of the current phase, usually when the object re-entered the atmosphere. **Blank = the phase is still in progress.** In Vague Date format. | |
| 13 | Status | `phase_status` | The event that ends the current phase. A phase status code (e.g. O in orbit, R re-entered, D deorbited, E exploded, L landed, DK docked). See https://planet4589.org/space/gcat/web/intro/phases.html. | Accepted values from the phases page. **`R?` (13) and `L?` (2) → NULL in intermediate** (decided 2026-10-25: strict, not inferred). Raw stays in staging. |
| 14 | Dest | `phase_destination` | Destination at the end of the current phase: a re-entry or landing location, the JCAT of a new parent object, or the world whose sphere of influence the object is entering. Its meaning depends on Status. | |
| 15 | Owner | `owner_code` *(existing)* | GCAT OrgCode of the object's owner/operator. | May be composite (`A/B`) or uncertain (`?`). The `explode_org_codes()` macro splits these. |
| 16 | State | `state_code` *(existing)* | GCAT OrgCode of the country/state associated with the owner/operator. | Feeds country resolution (D3). |
| 17 | Manufacturer | `manufacturer_code` *(existing)* | GCAT OrgCode of the entity that built the object. | Composite/uncertain, as for owner. |
| 18 | Bus | `bus` | Spacecraft bus (chassis) type. Not standardised, and many are one-off. Most useful for commercial communications satellites, where one bus type is used by many owners. | |
| 19 | Motor | `motor` | Name of the main thruster or rocket engine in the object's propulsion system, with particular attention to apogee motors. Not standardised. | |
| 20 | Mass | `mass_kg` *(existing)* | Mass of this GCAT object in kg at launch (initial orbital insertion), not including attached objects. | |
| 21 | MassFlag | `mass_flag` | `?` = the Mass value is an estimate, hopefully good to about 20%. | Applies to all `*_flag` columns below: text in staging. Intermediate derives a `flag_*_estimated` boolean. |
| 22 | DryMass | `dry_mass_kg` *(existing)* | Dry mass of this GCAT object in kg, a reasonable proxy for its mass after its active lifetime. Excludes attached objects. | |
| 23 | DryFlag | `dry_mass_flag` | `?` = the DryMass value is an estimate (about 20%). | |
| 24 | TotMass | `total_mass_kg` | Total mass at launch (orbital insertion) in kg of a set of attached GCAT objects. It's given on one of them (usually the S entry), and the others hold 0. The sum of the set's Mass values should equal TotMass. | 0 means "carried on another object", not zero mass. |
| 25 | TotFlag | `total_mass_flag` | `?` = the TotMass value is an estimate (about 20%). | |
| 26 | Length | `length_m` *(existing)* | Longest dimension of the main body of the object, in metres. | |
| 27 | LFlag | `length_flag` | `?` = the Length value is a guess (about 20%). | |
| 28 | Diameter | `diameter_m` *(existing)* | Second-longest dimension of the main body, in metres. Length × Diameter approximates the cross-section, not counting appendages. | |
| 29 | DFlag | `diameter_flag` | `?` = the Diameter value is a guess (about 20%). | |
| 30 | Span | `span_m` *(existing)* | Largest dimension of the whole object across all appendages (booms, solar arrays, antennae), in metres. | |
| 31 | SpanFlag | `span_flag` | `?` = the Span value is a guess (about 20%). | |
| 32 | Shape | `shape` *(existing)* | Approximate shape of the object. Carried over from the old RAE table of Earth satellites. | |
| 33 | ODate | `canonical_orbit_epoch` | Epoch of the canonical orbit, in Vague Date format. The canonical orbit is the one GCAT picks as representative of the object's early operations, after initial positioning. | Not the current orbit. Space-Track GP holds that. |
| 34 | Perigee | `canonical_perigee_km` | Conventional perigee height of the canonical orbit in km: perigee radius minus the central body's equatorial radius. | Kept separate from GP `periapsis`. |
| 35 | PF | `canonical_perigee_flag` | `?` = the Perigee value is a guess. | |
| 36 | Apogee | `canonical_apogee_km` | Conventional apogee height of the canonical orbit in km: apogee radius minus the central body's equatorial radius. | |
| 37 | AF | `canonical_apogee_flag` | `?` = the Apogee value is a guess. | |
| 38 | Inc | `canonical_inclination_deg` | Inclination of the canonical orbit in degrees. Earth orbits are relative to the equator of date (TEME). Heliocentric orbits are relative to the J2000 ecliptic, and orbits around other bodies to that body's IAU equator. | |
| 39 | IF | `canonical_inclination_flag` | `?` = the Inc value is a guess. | |
| 40 | OpOrbit | `orbit_type_raw` *(existing)* | Orbit type of the canonical orbit. Values are listed in https://planet4589.org/space/gcat/web/intro/orbits.html. | `orbit_regime` and `orbit_subtype` are split from it in intermediate. Those definitions come in a later batch from orbits.html. |
| 41 | OQUAL | `orbit_quality_note` | Orbit quality note: the source of the canonical orbit. Usually blank. `J` = estimated by McDowell himself. | |
| 42 | AltNames | `alt_names` | Comma-delimited list of further alternative names for the object. | Intermediate may split it into a `VARCHAR[]`. |

---

## Batch 2: GCAT payload catalog (`psatcat.tsv` → `stg__jsr__psatcat`)

Source: GCAT "Payload Catalog Column Descriptions", https://planet4589.org/space/gcat/web/cat/pcols.html.

**Also applies to `psatcat100k.tsv`** (same header), which feeds `stg__jsr__psatcat100k`.

| # | GCAT col | Proposed name | Proposed definition (from source) | SatTrack note |
|---|---|---|---|---|
| 1 | JCAT | `jcat` | (shared block, batch 1 #1) Ties this catalog to the object catalogs. | PK. |
| 2 | Piece | `cospar_id` | (shared block, batch 1 #4) Repeated from the object catalog for convenience. | |
| 3 | Name | `un_registry_name` | Name given in the UN satellite registry, where available. Otherwise GCAT fills in another name for readability. `[Name]` in square brackets = registered, but no name given in the registration. GCAT advises preferring the object catalog name. | |
| 4 | LDate | `gcat_launch_date` | (shared block, batch 1 #8) Same as the object catalog. | |
| 5 | TLast | `last_active_date` | Last Known Active Time: the date the satellite was most recently known to GCAT to be active. GCAT updates it "infrequently and patchily", so an old date doesn't prove the satellite is inactive. `*` = no information. Vague Date format. | D9. `*` becomes NULL. |
| 6 | TOp | `end_operation_date` | End Operation Date: when the satellite is believed to have completed regular operations. After it, the satellite may still be used for tests or keep a beacon, but not for its primary purpose. This isn't the "end of primary mission", which can be much earlier. `*` = believed still operating. | D9. `*` becomes NULL. |
| 7 | — (derived from TOp) | `flag_still_operating` *(existing)* | TRUE when TOp is `*`, which GCAT documents as "the payload is believed to be still operating". | Derived in intermediate (D9). |
| 8 | TDate | `end_transmission_date` *(existing)* | End of Transmission Date (GCAT's "Dead, Dead, Dead" date): after it, the satellite became completely silent and unresponsive, or its owners made no further contact. GCAT's preferred end-of-life date. `*` = believed still transmitting. | D9. `*` becomes NULL. |
| 9 | — (derived from TDate) | `flag_still_transmitting` *(existing)* | TRUE when TDate is `*`, which GCAT documents as "the payload is believed to be still transmitting". | Derived in intermediate (D9). |
| 10 | TF | `end_of_life_flag` | End-of-life special flag: D = recovery capsule, a separate orbiting object for only seconds before the deorbit burn; E = deep-space mission, may be operating outside Earth orbit; U = thought still working, but the UCS active satellite list suggests not; X = end-of-life date is a guess and the satellite could still be partly operating; Z = zombie satellite, no longer controlled but still emitting a beacon. | D9. Accepted values D, E, U, X, Z. |
| 11 | Program | `satellite_program` *(existing)* | Identifies groups of related satellites. GCAT uses it to organise its mission logs. | |
| 12 | Plane | `constellation_plane` | Labels orbital planes or shells in a constellation. GCAT's note says it currently holds numeric shell numbers for OneWeb. | Observed 2026-11-08: filled for 14,262 payloads in `fct__satellite_master` (values such as `6 0`, `7 8`, `11 2`), so GCAT uses it beyond OneWeb; the note on pcols.html is older than the data. Own value only (not inherited). |
| 13 | Att | `attitude_control` | Type of attitude control: G gravity gradient, P pointed/3-axis, PS Sun-pointed, PN/N nadir-pointed, S spin, U unstabilised, `-` unknown. GCAT says it "has not yet been systematically filled in". | 2026-10-24 data: `-` 14,002; P 13,937; **D 1 → NULL** (undocumented). No completeness test. |
| 14 | Mvr | `maneuverability` *(existing)* | Whether the satellite has or had propulsion able to change its orbit. M = maneuverable; D = can make a single deorbit burn. | 2026-10-24 data: M 19,421; `-` 8,145; D 372; **N 2 → NULL in intermediate** (undocumented). Raw stays in staging. |
| 15 | Class | `ownership_class` *(existing)* | One- or (rarely) two-letter use class, usually based on the owner/operator's status: A amateur/academic/non-profit, B business (commercial), C civil (government, non-military), D defence (military, intelligence). Two letters = clearly shared dual use (e.g. BD). | |
| 16 | Category | `mission_category` *(existing)* | General purpose of the satellite, independent of Class. One or two values joined by `/` (e.g. `IMG/TECH`). A trailing `?` = uncertain, and `*` = orbit data kept secret by the US government. Codes include COM, NAV, IMG, IMG-R, MET, SIG, TECH, SCI and AST (full list on the source page). | Accepted values = the documented code list, after removing `?` and `*`. |
| 17 | Result | `mission_result` | Flags satellites that failed early in their mission: S success, F failed, U unknown, N no test (e.g. the rocket failed before the satellite could operate). | |
| 18 | Control | `control_centre` | Location of the spacecraft operations control centre. Not systematically filled in, but filled values should be reliable. | |
| 19 | Discipline | `science_discipline` | For scientific satellites, one or more research areas (e.g. ATM, ION, SOL, XRA; full list on the source page). Old `*` = major mission, which GCAT says to ignore. | Strip `*`. **`GEO` (1 row, on an app object) → NULL** (undocumented; GCAT documents `GEOD`). |
| 20 | UNState | `un_state` *(existing)* | OrgCode of the country that registered the satellite with the UN. `*` = differs from the owner country in the object catalog. `[XX]` = not registered, with the country GCAT thinks ought to have registered it. Blank = not registered and not considered to need it. | Country resolution must handle `[…]` and `*`. |
| 21 | UNReg | `un_reg_doc` *(existing)* | ID of the UN registration document (usually ST/SG/SER.E or A/AC.105/INF series). `*` = listed online, but the document isn't yet available. Blank = not registered. | |
| 22 | UNPeriod | `un_period_min` | Nodal period in minutes, as reported in the UN registration document. GCAT recommends preferring the main catalog's orbital data. | |
| 23 | UNPerigee | `un_perigee_km` | Perigee height in km, as reported in the UN registration document. | |
| 24 | UNApogee | `un_apogee_km` | Apogee height in km, as reported in the UN registration document. | |
| 25 | UNInc | `un_inclination_deg` | Inclination in degrees, as reported in the UN registration document. | |
| 26 | DispEpoch | `disposal_epoch` | Epoch of the disposal orbit, only for maneuverable payloads in Earth orbit. For other objects, the disposal orbit is the initial orbit. A trailing `*` should be ignored. GCAT says the disposal data "should not be relied upon at present" (Oct 2024). | Flag as experimental in docs. **Staging and intermediate only, not marts** (experimental per GCAT; decided 2026-10-25). |
| 27 | DispPeri | `disposal_perigee_km` | Perigee of the end-of-life orbit of a maneuverable satellite. | GCAT gives no unit here; km assumed by analogy with Perigee. **Confirm.** **Staging and intermediate only, not marts** (experimental per GCAT; decided 2026-10-25). |
| 28 | DispApo | `disposal_apogee_km` | Apogee of the end-of-life orbit of a maneuverable satellite. | Unit as above. **Staging and intermediate only, not marts** (experimental per GCAT; decided 2026-10-25). |
| 29 | DispInc | `disposal_inclination_deg` | Inclination of the end-of-life orbit of a maneuverable satellite. | Unit as above. **Staging and intermediate only, not marts** (experimental per GCAT; decided 2026-10-25). |
| 30 | Comment | `gcat_comment` | Descriptive free-text comment from GCAT, which may be empty. | |
