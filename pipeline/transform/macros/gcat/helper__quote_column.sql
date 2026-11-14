{#- quote bare column names (GCAT has columns like Primary and IF that are SQL keywords) -#}
{% macro helper__quote_column(col) -%}
{%- if modules.re.match('^[A-Za-z_][A-Za-z0-9_]*$', col) -%}{{ adapter.quote(col) }}{%- else -%}{{ col }}{%- endif -%}
{%- endmacro %}
