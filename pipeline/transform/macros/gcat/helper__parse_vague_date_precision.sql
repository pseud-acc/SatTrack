{% macro helper__parse_vague_date_precision(col) -%}
(case
    when {{ sattrack.helper__clean_gcat_text(col) }} is null then null
    when trim({{ sattrack.helper__quote_column(col) }}) = '*' then 'current'
    when trim({{ sattrack.helper__quote_column(col) }}) = '?' then 'unknown'
    else (case
        when regexp_full_match({{ sattrack.helper__normalise_vague_date(col) }}, '\d{4} [A-Z][a-z]{2} \d{1,2} \d{4}:\d{2}(\.\d+)?') then 'second'
        when regexp_full_match({{ sattrack.helper__normalise_vague_date(col) }}, '\d{4} [A-Z][a-z]{2} \d{1,2} \d{4}') then 'minute'
        when regexp_full_match({{ sattrack.helper__normalise_vague_date(col) }}, '\d{4} [A-Z][a-z]{2} \d{1,2} \d{2}h') then 'hour'
        when regexp_full_match({{ sattrack.helper__normalise_vague_date(col) }}, '\d{4} [A-Z][a-z]{2} \d{1,2}\.\d{1,2}') then 'centiday'
        when regexp_full_match({{ sattrack.helper__normalise_vague_date(col) }}, '\d{4} [A-Z][a-z]{2} \d{1,2}') then 'day'
        when regexp_full_match({{ sattrack.helper__normalise_vague_date(col) }}, '\d{4} [A-Z][a-z]{2}') then 'month'
        when regexp_full_match({{ sattrack.helper__normalise_vague_date(col) }}, '\d{4} Q[1-4]') then 'quarter'
        when regexp_full_match(regexp_replace(trim({{ sattrack.helper__quote_column(col) }}), '\?$', ''), '\d{3}0s') then 'decade'
        when regexp_full_match({{ sattrack.helper__normalise_vague_date(col) }}, '\d{4}') then 'year'
        when regexp_full_match({{ sattrack.helper__normalise_vague_date(col) }}, '\d{1,2}C') then 'century'
        when regexp_full_match({{ sattrack.helper__normalise_vague_date(col) }}, '\d{1,2}M') then 'millennium'
        else 'unparsed' end)
        || (case when trim({{ sattrack.helper__quote_column(col) }}) like '%?' then '?' else '' end)
end)
{%- endmacro %}
