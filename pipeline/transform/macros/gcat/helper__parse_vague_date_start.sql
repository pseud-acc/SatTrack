{#- interval start per GCAT: the date as written, less one unit when uncertain ('?' widens the range by one unit on each side) -#}
{% macro helper__parse_vague_date_start(col) -%}
{%- set p = sattrack.helper__parse_vague_date_precision(col) -%}
{%- set b = sattrack.helper__parse_vague_date_base(col) -%}
(case
    when {{ b }} is null then null
    else {{ b }} - (case when {{ p }} like '%?' then 1 else 0 end) * {{ sattrack.helper__parse_vague_date_unit(col) }}
end)
{%- endmacro %}
