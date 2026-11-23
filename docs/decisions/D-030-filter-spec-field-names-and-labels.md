# D-030 Filter spec field names are the objects dataset's; labels come from dbt `meta`

**Status:** Accepted, 2026-11-22 (plan 2.2), by the owner. **Component:** `app/contracts/filter_spec.schema.json`,
the mart schema YAML, every UI that shows a filter.

## Context

The filter spec (plan 2.2) is used by the Dash sidebar now, by the Cesium viewer in the browser (3.3) and by
natural-language query (Phase 6). It needs one name for each field. Three vocabularies exist: the dbt mart columns
(`operational_status`), the `objects` dataset (the same names, D-009/D-010), and the legacy app CSV headers
(`Status`, `Owner`, `Purpose`), which the Plotly views use until plan 3.6 removes them.

People must never see a snake_case name in the app. Today the sidebar's captions ("Orbit Type", "Search
Satellite") are typed into the layout, separately from the data.

## Options

| | Spec field names | Labels | For | Against |
|---|---|---|---|---|
| **A (chosen)** | `objects` / mart names | `config: meta: label:` on the mart column, written into the schema as each field's `title` | One vocabulary for server, browser and NL query; the label lives next to the column's definition and type; CI can require it | Two YAML edits to add a field (list + label) |
| B | CSV headers | Typed in the layout | Smallest change now | Cesium and NLQ would need a translation; retired with Plotly in 3.6 |
| C | Mart names | An alias table in the app | Labels editable without dbt | The mapping layer D-010 avoids: two lists that can drift |

Future features weighed: NL query needs labels the model can map words to ("purpose", "owner") and names it can
emit exactly; Cesium's legend and "Colour by" menu (D-017 in the Cesium review) need the same labels; the
per-satellite pages and API (Phase 7) expose the same fields.

## Decision

- Spec clauses use the `objects` dataset's field names.
- Each filterable column's dbt schema YAML carries `config: meta: label: "<label>"`. dbt 2.0.8 (the pinned
  version) accepts column `meta` under `config:`; `dbt parse` puts it in both `meta` and `config.meta` of the
  manifest, and dbt-bouncer passes (2,324 checks). Top-level column `meta` is the deprecated form, so it isn't used.
- `pipeline/scripts/build_filter_spec_schema.py` writes each label as the field's `title` in
  `filter_spec.schema.json`. The build fails if a filterable field has no label, and a test fails if a label is
  blank, contains an underscore or equals the field name.
- The app reads labels with `app.core.filter_spec.label(field)`.

Labels set now (matching the sidebar's existing captions where there is one): SATCAT number, Satellite name,
Object type, Status, Orbit type, Owner, Launch vehicle, Purpose, Launch year.

## Consequences

- Renaming a label is a dbt YAML change plus a regenerated schema; CI catches a stale schema.
- The server's sidebar path needs a table with these names (see the open question in the PR: built from the
  `objects` dataset, or from the CSV during the Plotly transition).

## Revisit if

- Labels need translating (i18n): move them to a message catalogue keyed by field name, generated the same way.
- A field needs different labels in different places (e.g. short legend vs long filter caption): add `meta.short_label`.
