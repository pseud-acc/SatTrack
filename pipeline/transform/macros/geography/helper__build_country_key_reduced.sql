{% macro helper__build_country_key_reduced(expr) -%}
trim(regexp_replace(regexp_replace({{ sattrack.helper__build_country_key_full(expr) }},
    '\b(the|of|republic|peoples|people|democratic|federal|state|states|islamic|kingdom|commonwealth|union)\b', ' ', 'g'),
    '\s+', ' ', 'g'))
{%- endmacro %}
