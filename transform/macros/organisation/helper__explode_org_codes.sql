{#- One row per organisation in a GCAT composite code ('GSFC/ESA', 'ESA?'); see _organisation__macros.yml. -#}
{% macro helper__explode_org_codes(relation, key_col, code_col, role) -%}
select
    {{ dbt_utils.generate_surrogate_key(['entity_key', "'" ~ role ~ "'", 'ord', 'part']) }} as map_id
    , entity_key
    , '{{ role }}' as org_role
    , rtrim(part, '?') as org_code
    , cast(ord as integer) as org_code_ord
    , raw_code as org_code_raw
    , raw_code like '%/%' as is_composite
    , part like '%?' as is_uncertain
    , case when raw_code like '%/%' then 'split_slash' else 'single' end as parse_rule
from (
    select
        {{ key_col }} as entity_key
        , {{ code_col }} as raw_code
        , trim(p.part) as part
        , p.ord
    from {{ relation }}
    cross join unnest(string_split({{ code_col }}, '/')) with ordinality as p(part, ord)
    where {{ code_col }} is not null
) as code_parts
where rtrim(part, '?') <> ''
{%- endmacro %}
