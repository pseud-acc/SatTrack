{#- interval end per GCAT: the date as written plus one unit, or plus two units when uncertain ('?'), so a '?' range is three units wide -#}
{% macro helper__parse_vague_date_end(col) -%}
{%- set p = sattrack.helper__parse_vague_date_precision(col) -%}
{%- set b = sattrack.helper__parse_vague_date_base(col) -%}
(case
    when {{ b }} is null then null
    else {{ b }} + (case when {{ p }} like '%?' then 2 else 1 end) * {{ sattrack.helper__parse_vague_date_unit(col) }}
end)
{%- endmacro %}
