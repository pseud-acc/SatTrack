-- One row per jcat per manufacturer org, from GCAT composite codes (keeps every co-org).
with cte_int__jsr__satellite_catalogue as (
    select
        jcat
        , manufacturer_code
    from {{ ref('int__jsr__satellite_catalogue') }}
)

, cte_int__jsr__org_organisations as (
    select
        org_code
        , org_display_name
    from {{ ref('int__jsr__org_organisations') }}
)

, cte_manufacturer_org_codes as ( -- one row per organisation in each composite code
    {{ helper__explode_org_codes('cte_int__jsr__satellite_catalogue', 'jcat', 'manufacturer_code', 'manufacturer') }}
)

, cte_final as (
    select
        m.map_sk
        , m.entity_key as jcat
        , m.org_role
        , m.org_code
        , m.org_code_order
        , m.org_code_raw
        , m.flag_multiple_orgs
        , m.flag_org_uncertain
        , m.org_code_split_rule
        , o.org_display_name as org_name
        , {{ helper__audit_fields() }}
    from cte_manufacturer_org_codes as m
    left join cte_int__jsr__org_organisations as o using (org_code)
)

select * from cte_final
