{% macro helper__build_country_key_full(expr) -%}
trim(regexp_replace(regexp_replace(lower(strip_accents({{ expr }})), '[^a-z ]', ' ', 'g'), '\s+', ' ', 'g'))
{%- endmacro %}
