-- One row per satellite per manufacturer organisation (every co-manufacturer in a GCAT composite code).
with cte_int__jsr__org_satellite_manufacturer_map as (
    select
        map_id
        , jcat
        , org_role
        , org_code
        , org_code_ord
        , org_code_raw
        , is_composite
        , is_uncertain
        , parse_rule
        , org_name
    from {{ ref('int__jsr__org_satellite_manufacturer_map') }}
)

, cte_final as (
    select
        cast(map_id as varchar) as map_id
        , cast(jcat as varchar) as jcat
        , cast(org_role as varchar) as org_role
        , cast(org_code as varchar) as org_code
        , cast(org_code_ord as integer) as org_code_ord
        , cast(org_code_raw as varchar) as org_code_raw
        , cast(is_composite as boolean) as is_composite
        , cast(is_uncertain as boolean) as is_uncertain
        , cast(parse_rule as varchar) as parse_rule
        , cast(org_name as varchar) as org_name
        , {{ helper__audit_fields() }}
    from cte_int__jsr__org_satellite_manufacturer_map
)

select * from cte_final
