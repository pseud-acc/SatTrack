-- One row per GCAT object (satcat + satcat100k): the launch it came from, with the site, vehicle family and launch
-- agency names resolved. Payloads use their own launch-log row; every other object (rocket stages, components, debris)
-- takes the launch-level fields of its satcat Launch_Tag, which GCAT says "matches the launch tag in the launch lists
-- and may be used to join the two databases". Launch-level fields are the same on every launch-log row of a launch.
with cte_int__jsr__satellite_catalogue as (
    select
        jcat
        , launch_tag
    from {{ ref('int__jsr__satellite_catalogue') }}
)

, cte_int__jsr__launch_events as (
    select
        jcat
        , launch_tag
        , launch_datetime
        , launch_datetime_precision
        , site_code
        , lv_type
        , lv_brand
        , flight_id
        , launch_agency_code
        , launch_category
        , flag_catalog_match_uncertain
    from {{ ref('int__jsr__launch_events') }}
)

, cte_int__jsr__org_launch_agency_map as (
    select
        jcat
        , org_code
        , org_code_ord
        , org_name
    from {{ ref('int__jsr__org_launch_agency_map') }}
)

, cte_int__jsr__launch_sites as (
    select
        site_code
        , site_display_name
        , site_state
        , site_location_country
        , site_latitude
        , site_longitude
    from {{ ref('int__jsr__launch_sites') }}
)

, cte_int__jsr__launch_vehicles as (
    select
        lv_name
        , lv_family
    from {{ ref('int__jsr__launch_vehicles') }}
)

, cte_int__jsr__org_organisations as (
    select
        org_code
        , org_display_name
    from {{ ref('int__jsr__org_organisations') }}
)

, cte_launches as ( -- one row per launch tag; a launch whose payload rows disagree would fan out and fail the jcat key test
    select
        ev.launch_tag
        , ev.launch_datetime
        , ev.launch_datetime_precision
        , ev.site_code
        , ev.lv_type
        , ev.lv_brand
        , ev.flight_id
        , ev.launch_agency_code
        , ev.launch_category
        -- every co-agency of the launch in GCAT order (the same list on each payload row of the launch)
        , list_sort(list(distinct {'ord': agency.org_code_ord, 'code': agency.org_code, 'name': coalesce(agency.org_name, agency.org_code)})
            filter (where agency.org_code is not null)) as launch_agency_orgs
    from cte_int__jsr__launch_events as ev
    left join cte_int__jsr__org_launch_agency_map as agency on agency.jcat = ev.jcat
    group by all
)

, cte_object_launches as ( -- the object's own launch-log row wins; otherwise its satcat Launch_Tag
    select
        cat.jcat
        , coalesce(own.launch_tag, cat.launch_tag) as launch_tag
        , own.jcat is not null as has_own_launch_record
        , own.flag_catalog_match_uncertain
    from cte_int__jsr__satellite_catalogue as cat
    left join cte_int__jsr__launch_events as own on own.jcat = cat.jcat
)

, cte_final as (
    select
        obj.jcat
        , launch.launch_tag
        , launch.launch_datetime
        , launch.launch_datetime_precision
        , launch.site_code
        , site.site_display_name as site_name
        , site.site_state
        , site.site_location_country
        , site.site_latitude
        , site.site_longitude
        , launch.lv_type
        , launch.lv_brand
        , lv.lv_family
        , launch.flight_id
        , launch.launch_agency_code
        -- the first listed agency names a composite code ('NASA/ESA' -> NASA); every agency is in the org lists
        , agency.org_display_name as launch_agency_name
        , list_transform(launch.launch_agency_orgs, lambda x: x.code) as launch_agency_org_codes
        , list_transform(launch.launch_agency_orgs, lambda x: x.name) as launch_agency_org_names
        , launch.launch_category
        -- payload-specific (GCAT llog.html SatType position 9): only on the object's own launch-log row
        , obj.flag_catalog_match_uncertain
        , case
            when obj.has_own_launch_record then 'own'
            when launch.launch_tag is not null then 'inherited_launch'
            else 'none'
        end as launch_fields_source
        , {{ helper__audit_fields() }}
    from cte_object_launches as obj
    left join cte_launches as launch on launch.launch_tag = obj.launch_tag
    left join cte_int__jsr__launch_sites as site on site.site_code = launch.site_code
    left join cte_int__jsr__launch_vehicles as lv on lv.lv_name = launch.lv_type
    left join cte_int__jsr__org_organisations as agency
        on agency.org_code = split_part(rtrim(launch.launch_agency_code, '?'), '/', 1)
)

select * from cte_final
