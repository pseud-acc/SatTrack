-- One row per satellite per owner organisation (every co-owner in a GCAT composite code).
with cte_int__jsr__org_satellite_owner_map as (
    select
        map_sk
        , jcat
        , org_role
        , org_code
        , org_code_order
        , org_code_raw
        , flag_multiple_orgs
        , flag_org_uncertain
        , org_code_split_rule
        , org_name
    from {{ ref('int__jsr__org_satellite_owner_map') }}
)

, cte_final as (
    select
        cast(map_sk as varchar) as map_sk
        , cast(jcat as varchar) as jcat
        , cast(org_role as varchar) as org_role
        , cast(org_code as varchar) as org_code
        , cast(org_code_order as integer) as org_code_order
        , cast(org_code_raw as varchar) as org_code_raw
        , cast(flag_multiple_orgs as integer) as flag_multiple_orgs
        , cast(flag_org_uncertain as integer) as flag_org_uncertain
        , cast(org_code_split_rule as varchar) as org_code_split_rule
        , cast(org_name as varchar) as org_name
        , {{ helper__audit_fields() }}
    from cte_int__jsr__org_satellite_owner_map
)

select * from cte_final
