{% macro helper__clean_gcat_text(col) -%}
nullif(nullif(trim({{ sattrack.helper__quote_column(col) }}), ''), '-')
{%- endmacro %}
