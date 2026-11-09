-- One row per launched payload per launch agency organisation (every co-agency in a GCAT composite code).
with cte_int__jsr__org_launch_agency_map as (
    select
        map_sk
        , jcat
        , org_role
        , org_code
        , org_code_ord
        , org_code_raw
        , flag_composite
        , flag_uncertain
        , parse_rule
        , org_name
    from {{ ref('int__jsr__org_launch_agency_map') }}
)

, cte_final as (
    select
        cast(map_sk as varchar) as map_sk
        , cast(jcat as varchar) as jcat
        , cast(org_role as varchar) as org_role
        , cast(org_code as varchar) as org_code
        , cast(org_code_ord as integer) as org_code_ord
        , cast(org_code_raw as varchar) as org_code_raw
        , cast(flag_composite as integer) as flag_composite
        , cast(flag_uncertain as integer) as flag_uncertain
        , cast(parse_rule as varchar) as parse_rule
        , cast(org_name as varchar) as org_name
        , {{ helper__audit_fields() }}
    from cte_int__jsr__org_launch_agency_map
)

select * from cte_final
