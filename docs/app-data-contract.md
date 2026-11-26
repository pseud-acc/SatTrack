# App data contract

The data files the pipeline publishes for the app and the browser: what each dataset holds, the envelope they share,
and the rules for changing them. The reasons are in [DECISIONS.md](DECISIONS.md) (D-009 to D-012).

The Dash app's CSVs (`satcat_tle.csv`, `last_data_update.csv`) are covered in [app/README.md](../app/README.md);
they stay until the Cesium viewer replaces the Plotly views (Phase 3).

## Datasets

**Core datasets** are what every feature builds on. **Feature datasets** are added with the feature that needs them,
to the same envelope.

| Dataset | Kind | Contents | Access | Status |
|---|---|---|---|---|
| `objects` | Core | Every tracked object: identity, type, full OMM element set, filter fields | Whole file, every page load | **Published** (plan 2.1) |
| `object_detail` | Core | What the detail panel shows (shape below) | One object at a time | Shape agreed; file ships with the panel (3.4) |
| `reentries` | Feature | Objects predicted to re-enter soon | Whole file | With plan 7 |
| `conjunctions` | Feature | Close-approach pairs (CelesTrak SOCRATES; D-008 rules) | Whole file | With plan 7 |
| `transmitters` | Feature | Radio frequencies (SatNOGS DB, CC BY-SA, so its own file) | One object or whole file | With plan 7 |
| `element_history` | Feature | Past element sets per object | One object at a time | With plan 7; needs a per-object store |
| `catalogue_history` | Feature | Every object ever catalogued, decayed ones included | Whole file | With the replay / statistics |
| `launch_sites`, `organisations` | Feature | Reference lists | Whole file | With plan 5.2 |
| `events` | Feature | Launched this week, newly catalogued, re-entered | Whole file | With event pages |

Not data contracts: the filter spec (`app/contracts/filter_spec.schema.json`, plan 2.2) versions with the app's code;
filter options are computed in the browser from `objects`; user data (accounts, watchlists) belongs in an app
database, never in the pipeline.

## The envelope

Every dataset is one JSON document:

```json
{
  "dataset": "objects",
  "schema": 2,
  "count": 32652,
  "generated_at": "2026-11-21T14:24:40+00:00",
  "run_id": "run_2026-11-21T142334Z",
  "key": "satcat_id",
  "attribution": [
    "Orbital data: USSPACECOM via Space-Track.org",
    "Launch, owner and mission details: GCAT (J. McDowell, planet4589.org), CC BY 4.0",
    "Constellation groups: CelesTrak (Dr T.S. Kelso)"
  ],
  "caution": "Public element sets must not be used for conjunction (collision) assessment.",
  "records": [ { "satcat_id": 5, "...": "..." } ]
}
```

| Field | Meaning |
|---|---|
| `dataset` | The dataset's name; also its file name and URL (`/data/<dataset>.json`) |
| `schema` | Version of the record shape. Additive changes keep it; renaming a field or changing its meaning raises it, and a reader rejects a version it doesn't know |
| `count` | Number of records; a reader checks it equals `len(records)` |
| `generated_at` | When the export wrote the file (UTC) |
| `run_id` | The pipeline run that built the data (the tracking mart's run, for `objects`) |
| `key` | The field that identifies a record and joins datasets: `satcat_id` |
| `attribution`, `caution` | The citation and the Space-Track caution every public output carries; each dataset has its own, so licences never mix |
| `records` | One record per object, sorted by the key, which is unique |

**Rules**
- Field names are the dbt mart column names. Their definitions are in the [column docs](https://pseud-acc.github.io/SatTrack/).
  There is no renaming or lookup layer.
- Gaps are `null`; label lists are always arrays (`[]` when there are none); element numbers are never rounded.
- One JSON Schema per dataset in `app/contracts/<dataset>.schema.json`. The pipeline validates every record against
  it, checks the count and that the key is unique and sorted, and refuses to publish otherwise. The last good files
  stay live.
- All of a run's files (CSVs and datasets) are listed with their SHA-256 in `app/current.json` and go live together.

## `objects` (schema 2)

Written by `pipeline/transform/analyses/app_export/app__objects.sql` through `scripts/export_app_csvs.py`.
One record per object in the Space-Track GP feed with a full element set, of every type (D-011). Elements come
from `fct__gp_elements` (tracking, updated every run). Descriptive fields come from `fct__satellite_master`
(enrichment), through a left join: an object new to the GP feed appears at once, with null details until
enrichment next succeeds.

| Field | Type | Null? | Source column |
|---|---|---|---|
| `satcat_id` | integer | no | `fct__gp_elements.satcat_id` |
| `object_id` | string | yes | `fct__gp_elements.object_id` (`UNKNOWN` for analyst objects) |
| `object_name` | string | yes | `fct__satellite_master.object_name`, else `fct__gp_elements.object_name` |
| `object_type` | string | no | `fct__gp_elements.object_type`: `PAYLOAD`, `ROCKET BODY`, `DEBRIS`, `UNKNOWN` |
| `epoch` | string | no | `fct__gp_elements.epoch`, as `%Y-%m-%dT%H:%M:%S.%f` UTC |
| `mean_motion` | number | no | `fct__gp_elements.mean_motion` (rev/day) |
| `eccentricity` | number | no | `fct__gp_elements.eccentricity` |
| `inclination` | number | no | `fct__gp_elements.inclination` (deg) |
| `ra_of_asc_node` | number | no | `fct__gp_elements.ra_of_asc_node` (deg) |
| `arg_of_pericenter` | number | no | `fct__gp_elements.arg_of_pericenter` (deg) |
| `mean_anomaly` | number | no | `fct__gp_elements.mean_anomaly` (deg) |
| `bstar` | number | no | `fct__gp_elements.bstar` |
| `mean_motion_dot` | number | no | `fct__gp_elements.mean_motion_dot` |
| `mean_motion_ddot` | number | no | `fct__gp_elements.mean_motion_ddot` |
| `rev_at_epoch` | integer | no | `fct__gp_elements.rev_at_epoch` |
| `element_set_no` | integer | no | `fct__gp_elements.element_set_no` |
| `ephemeris_type` | integer | no | `fct__gp_elements.ephemeris_type` (0 = SGP4) |
| `classification_type` | string | no | `fct__gp_elements.classification_type` |
| `orbital_period` | number | no | `fct__gp_elements.orbital_period` (min) |
| `operational_status` | string | yes | `fct__satellite_master.operational_status` |
| `orbit_class` | string | yes | `fct__satellite_master.orbit_class` |
| `owner_country` | string | yes | `fct__satellite_master.owner_country` |
| `launch_year` | integer | yes | `fct__satellite_master.launch_year` |
| `mission_category_labels` | array of strings | no (may be `[]`) | `fct__satellite_master.mission_category_labels` |
| `ownership_class_labels` | array of strings | no (may be `[]`) | `fct__satellite_master.ownership_class_labels` |
| `launch_vehicle_brand` | string | yes | `fct__satellite_master.launch_vehicle_brand` |
| `site_location_country` | string | yes | `fct__satellite_master.site_location_country` |
| `satellite_constellation_name` | string | yes | `fct__satellite_master.satellite_constellation_name`: the constellation (near-identical satellites working together), from CelesTrak's groups or the ad-hoc seed (D-047), e.g. `Starlink`, `Sentinel-2`; null when none. Anything that shows it carries the credit "Constellation groups: CelesTrak (Dr T.S. Kelso)" |
| `primary_satellite_system_name` | string | yes | `fct__satellite_master.primary_satellite_system_name`: the satellite system the object was built for (D-047), e.g. `GPS`; null when none |
| `satellite_system_names` | array of strings | no (may be `[]`) | `fct__satellite_master.satellite_system_names`: every system, primary first, then hosted ones (e.g. `Search & Rescue (SARSAT)`, `EGNOS`) |

Schema 2 (D-047, 25 Nov 2026) replaced schema 1's `constellation` (CelesTrak's constellation or operator group, D-026)
with the three fields above; a reader that knows only schema 1 rejects the file, as the contract requires.

**Using it in the browser.** satellite.js's `json2satrec` takes the OMM keywords in capitals. The element fields'
names are those keywords in lower case, so the browser builds the OMM record by uppercasing them (`mean_motion` →
`MEAN_MOTION`, `satcat_id` → `NORAD_CAT_ID`): a fixed rule, not a lookup table. On load the browser builds its own
columns (typed arrays) and an index by `satcat_id`, in a Web Worker. That form is rebuilt on every load and never saved.

**Size** (21 Nov 2026, 32,652 records): 23.7 MB raw, 1.70 MB Brotli, 2.44 MB gzip.

## `object_detail` (shape agreed, file with plan 3.4)

One record per object, keyed by `satcat_id`, in the same envelope, loaded one object at a time. Field groups, all
taken from `fct__satellite_master` with their mart names:

- **Identity:** `satcat_id`, `jcat`, `object_name`, `object_id`, `satellite_program`, `satellite_program_family`,
  `constellation_plane`.
- **Organisations:** `owner_org_codes` / `owner_org_names`, `operator_name`, `manufacturer_org_codes` /
  `manufacturer_org_names`, `launch_agency_org_codes` / `launch_agency_org_names` (ordered lists), and
  `owner_country_codes`.
- **Launch:** `launch_date` with `launch_datetime_precision`, `site_code`, `site_name`, `site_latitude`,
  `site_longitude`, `launch_vehicle_type`, `launch_vehicle_family`, `flight_id`.
- **Physical:** `mass_kg` (with `flag_mass_estimated`), `dry_mass_kg`, `span_m`; bus, shape, dimensions, power and
  payload are added in plan 5.1.
- **Status:** `operational_status` with `operational_status_source`, `flag_still_operating`,
  `flag_still_transmitting`, `end_operation_date` and `end_transmission_date` with their precision, `end_of_life_code`.
- **Data quality:** `object_type_source`, `launch_details_source`, `mission_details_source`,
  `flag_catalog_match_uncertain`, `flag_orbit_conflict`, `jcat_link_method`.

The panel's design (3.4, 5.2) may narrow or extend this list before the file ships. Every addition is additive.

## Delivery

- **Publishing:** the pipeline writes `<dataset>.json.br` and `<dataset>.json.gz` next to the CSVs in the private
  bucket's `app/` prefix, and lists them in `app/current.json`.
- **Serving:** the app loads them at start-up (checksums verified) and serves `GET /data/<dataset>.json` exactly as
  compressed:
  - the encoding follows the browser's `Accept-Encoding` preferences (RFC 9110 §12.5.3): Brotli or gzip, Brotli
    on a tie. The response is decompressed when no compressed coding is acceptable or the browser prefers
    `identity`, and `406 Not Acceptable` when all three are refused;
  - an `ETag` (the SHA-256 of the bytes sent), `Cache-Control: no-cache` and `Vary: Accept-Encoding`;
  - a repeat visit downloads nothing (304, weak comparison, `*` accepted) until a run publishes new data. The 304
    is decided before any decompression.
- **Workers:** gunicorn runs threaded workers (`--threads 4` in the Procfile). The file is larger than Heroku's 1 MB
  router buffer, so a slow download holds one thread, not a whole worker. CI's Heroku build check tests this with
  slow clients (D-012).
- **Local runs and CI:** `SATTRACK_APP_DATA_DIR` works the same way. `tests/app_data/objects.json.{br,gz}` is a
  384-record sample.
