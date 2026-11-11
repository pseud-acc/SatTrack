{#- Audit fields on every model: when the row was built and by which job run (SATTRACK_RUN_ID is set by
    run_pipeline.py; 'manual' for local or ad hoc runs). -#}
{% macro helper__audit_fields() -%}
    cast({{ dbt.current_timestamp() }} as timestamp) as inserted_date_time
        , cast('{{ env_var("SATTRACK_RUN_ID", "manual") }}' as varchar) as inserted_by
{%- endmacro %}
