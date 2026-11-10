{% docs __overview__ %}
# SatTrack data pipeline

Ingestion lands Space-Track and GCAT data unchanged; dbt stages, combines and serves it in two independently published units (tracking, enrichment). Column definitions come from the publishers' own documentation and are cited in each doc block.

## Entity relationship diagram (marts)

Built from the dbt manifest on every docs build: the relationships are the `fk__*` relationships tests on the marts, and the diagram shows only the columns that take part in one. Click it to open it full size.

<a href="erd/erd_marts.svg" target="_blank"><img src="erd/erd_marts.svg" alt="Entity relationship diagram of the SatTrack marts" style="max-width:100%;background:#fff;border-radius:6px;padding:8px"></a>

Source files: [Mermaid](erd/erd_marts.mmd) (key columns), [DBML](erd/erd_marts.dbml) (all columns).
{% enddocs %}

