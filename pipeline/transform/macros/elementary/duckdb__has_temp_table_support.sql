{# dbt v2 (Fusion) pools connections, so DuckDB temp tables created in one adapter call are
   invisible to the next. Mirror Elementary's own Redshift-on-Fusion fix for DuckDB:
   use regular tables (Elementary cleans them up) instead of temp tables. #}
{% macro duckdb__has_temp_table_support() %}
    {% do return(not elementary.is_dbt_fusion()) %}
{% endmacro %}
