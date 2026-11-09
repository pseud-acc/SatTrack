-- One row per jcat: ordered lists of every owner, manufacturer and launch agency org (codes and names)
-- for the app's multi-select org filter (VARCHAR[]).
with cte_int__jsr__satellite_catalogue as (
    select
        jcat
    from {{ ref('int__jsr__satellite_catalogue') }}
)

, cte_int__jsr__org_satellite_owner_map as (
    select
        jcat
        , org_code
        , org_code_ord
        , org_name
    from {{ ref('int__jsr__org_satellite_owner_map') }}
)

, cte_int__jsr__org_satellite_manufacturer_map as (
    select
        jcat
        , org_code
        , org_code_ord
        , org_name
    from {{ ref('int__jsr__org_satellite_manufacturer_map') }}
)

, cte_int__jsr__org_launch_agency_map as (
    select
        jcat
        , org_code
        , org_code_ord
        , org_name
    from {{ ref('int__jsr__org_launch_agency_map') }}
)

, cte_owner_org_lists as (
    select
        jcat
        , list(org_code order by org_code_ord) as codes
        , list(coalesce(org_name, org_code) order by org_code_ord) as names
    from cte_int__jsr__org_satellite_owner_map
    group by jcat
)

, cte_manufacturer_org_lists as (
    select
        jcat
        , list(org_code order by org_code_ord) as codes
        , list(coalesce(org_name, org_code) order by org_code_ord) as names
    from cte_int__jsr__org_satellite_manufacturer_map
    group by jcat
)

, cte_launch_agency_org_lists as (
    select
        jcat
        , list(org_code order by org_code_ord) as codes
        , list(coalesce(org_name, org_code) order by org_code_ord) as names
    from cte_int__jsr__org_launch_agency_map
    group by jcat
)

, cte_final as (
    select
        c.jcat
        , coalesce(owners.codes, cast([] as varchar[])) as owner_org_codes
        , coalesce(owners.names, cast([] as varchar[])) as owner_org_names
        , coalesce(makers.codes, cast([] as varchar[])) as manufacturer_org_codes
        , coalesce(makers.names, cast([] as varchar[])) as manufacturer_org_names
        , coalesce(agencies.codes, cast([] as varchar[])) as launch_agency_org_codes
        , coalesce(agencies.names, cast([] as varchar[])) as launch_agency_org_names
        -- display names: the first listed organisation of a composite GCAT code ('GSFC/ESA' -> GSFC)
        , owners.names[1] as operator_name
        , makers.names[1] as manufacturer_name
        , {{ helper__audit_fields() }}
    from cte_int__jsr__satellite_catalogue as c
    left join cte_owner_org_lists as owners using (jcat)
    left join cte_manufacturer_org_lists as makers using (jcat)
    left join cte_launch_agency_org_lists as agencies using (jcat)
)

select * from cte_final
