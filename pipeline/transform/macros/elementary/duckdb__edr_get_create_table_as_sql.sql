{% macro duckdb__edr_get_create_table_as_sql(temporary, relation, sql_query, expiration_hours=none) %}
  {% if temporary and elementary.is_dbt_fusion() %}
  create or replace table {{ relation }} as {{ sql_query }}
  {% else %}
  create or replace {% if temporary %} temporary {% endif %} table {{ relation }} as {{ sql_query }}
  {% endif %}
{% endmacro %}
