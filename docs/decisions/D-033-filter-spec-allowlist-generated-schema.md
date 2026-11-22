# D-033 Filterable fields are hand-picked; their types, values and labels are generated from dbt

**Status:** Accepted, 2026-11-22 (plan 2.2), by the owner. **Component:** `app/contracts/filter_fields.yml`,
`pipeline/scripts/build_filter_spec_schema.py`, `app/contracts/filter_spec.schema.json`.

## Context

The allowlist of fields is a security boundary: whatever is filterable can be asked for by anyone, including through
NL query. Types and allowed values, on the other hand, already exist in the dbt schema YAML, and copying them by hand
would drift.

## Options

| | Field list | Types / values / labels | For | Against |
|---|---|---|---|---|
| **A (chosen)** | Hand-picked, committed | Generated from dbt YAML | Deliberate exposure; no drift in types; one place per fact | Two small edits to add a field |
| B | Generated: every column of the objects schema | Generated | No hand step | Every new column becomes filterable (and NL-queryable) by default, including internal or element fields |
| C | Hand-written schema | Hand-written | No generator | Types and enums drift from dbt |

## Decision

- `app/contracts/filter_fields.yml` lists each filterable field and the mart whose YAML documents it. Nine fields
  now: `satcat_id`, `object_name`, `object_type`, `operational_status`, `orbit_class`, `owner_country`,
  `launch_vehicle_brand`, `mission_category_labels`, `launch_year`.
- The generator reads each column's `data_type` (integer/bigint, varchar, varchar[] are supported; anything else
  fails the build), its `accepted_values` test if present (today only `operational_status`), and its label (D-030).
- Operators follow the type: integers `eq/in/not_in/between/is_missing`; strings `eq/in/not_in/is_missing`;
  string lists `contains_any/is_missing`.
- Limits: 32 clauses, 1,000 values per list, 200 characters per string.
- **Sync check:** `pipeline/ingestion/tests/test_filter_spec_schema.py` rebuilds the schema and fails if the
  committed file differs. It runs in the existing "pipeline / tests + dbt checks" CI job, so no workflow change.

## Consequences

- Open sets (owner, vehicle, mission labels, names) are checked by type and length, not by value; their options are
  computed from the data, as the sidebar does today.
- Orbit class and object type have fixed values in practice but no `accepted_values` test in dbt yet. Adding one
  (a dbt change) would make the schema enforce them too; noted for the pipeline backlog.

## Revisit if

- A field needs an operator its type doesn't get (e.g. `between` on a date): add a type rule in the generator.
- NL query needs fields beyond the sidebar's: add them to the list one by one, each a reviewed change.
