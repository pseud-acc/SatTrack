{#- the date as written, with the '?' and 's' flags ignored: the timestamp a Vague Date without a flag would start at; a century (nC) or millennium (nM) is its first day (20C = 1901 Jan 1) -#}
{% macro helper__parse_vague_date_base(col) -%}
{%- set v = sattrack.helper__normalise_vague_date(col) -%}
(case
    when {{ sattrack.helper__clean_gcat_text(col) }} is null or trim({{ sattrack.helper__quote_column(col) }}) in ('*', '?') then null
    when regexp_full_match({{ v }}, '\d{4} [A-Z][a-z]{2} \d{1,2} \d{4}:\d{2}(\.\d+)?')
        then try_strptime(regexp_extract({{ v }}, '^(\d{4} [A-Z][a-z]{2} \d{1,2} \d{4}:\d{2})', 1), '%Y %b %d %H%M:%S')
    when regexp_full_match({{ v }}, '\d{4} [A-Z][a-z]{2} \d{1,2} \d{4}') then try_strptime({{ v }}, '%Y %b %d %H%M')
    when regexp_full_match({{ v }}, '\d{4} [A-Z][a-z]{2} \d{1,2} \d{2}h') then try_strptime(rtrim({{ v }}, 'h'), '%Y %b %d %H')
    when regexp_full_match({{ v }}, '\d{4} [A-Z][a-z]{2} \d{1,2}\.\d{1,2}')
        then try_strptime(split_part({{ v }}, '.', 1), '%Y %b %d')
             + to_milliseconds(cast(round(try_cast('0.' || split_part({{ v }}, '.', 2) as double) * 86400000) as bigint))
    when regexp_full_match({{ v }}, '\d{4} [A-Z][a-z]{2} \d{1,2}') then try_strptime({{ v }}, '%Y %b %d')
    when regexp_full_match({{ v }}, '\d{4} [A-Z][a-z]{2}') then try_strptime({{ v }} || ' 1', '%Y %b %d')
    when regexp_full_match({{ v }}, '\d{4} Q[1-4]')
        then make_timestamp(cast(left({{ v }}, 4) as integer), (cast(right({{ v }}, 1) as integer) - 1) * 3 + 1, 1, 0, 0, 0)
    when regexp_full_match(regexp_replace(trim({{ sattrack.helper__quote_column(col) }}), '\?$', ''), '\d{3}0s')
        then make_timestamp(cast(left(trim({{ sattrack.helper__quote_column(col) }}), 4) as integer), 1, 1, 0, 0, 0)
    when regexp_full_match({{ v }}, '\d{4}') then make_timestamp(cast({{ v }} as integer), 1, 1, 0, 0, 0)
    when regexp_full_match({{ v }}, '\d{1,2}C') then make_timestamp((cast(rtrim({{ v }}, 'C') as integer) - 1) * 100 + 1, 1, 1, 0, 0, 0)
    when regexp_full_match({{ v }}, '\d{1,2}M') then make_timestamp((cast(rtrim({{ v }}, 'M') as integer) - 1) * 1000 + 1, 1, 1, 0, 0, 0)
    else null
end)
{%- endmacro %}
