{#- one unit of the precision as an interval: the width of the range a Vague Date without a '?' implies (GCAT example table) -#}
{% macro helper__parse_vague_date_unit(col) -%}
{%- set p = sattrack.helper__parse_vague_date_precision(col) -%}
(case replace({{ p }}, '?', '')
    when 'second' then interval 1 second
    when 'minute' then interval 1 minute
    when 'hour' then interval 1 hour
    when 'centiday' then (case
        when regexp_full_match({{ sattrack.helper__normalise_vague_date(col) }}, '\d{4} [A-Z][a-z]{2} \d{1,2}\.\d') then interval 8640 second
        else interval 864 second end)
    when 'day' then interval 1 day
    when 'month' then interval 1 month
    when 'quarter' then interval 3 month
    when 'year' then interval 1 year
    when 'decade' then interval 10 year
    when 'century' then interval 100 year
    when 'millennium' then interval 1000 year
    else interval 0 second end)
{%- endmacro %}
