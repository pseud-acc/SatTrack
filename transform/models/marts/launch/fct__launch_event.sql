-- One row per payload launch from the GCAT launch log, with the launch category and success code split out.
with cte_int__jsr__launch_events as (
    select
        jcat
        , launch_tag
        , launch_datetime
        , launch_datetime_start
        , launch_datetime_end
        , launch_datetime_precision
        , cospar_id
        , flag_catalog_match_uncertain
        , site_code
        , flag_site_uncertain
        , launch_pad
        , ascent_site_code
        , ascent_pad
        , launch_platform
        , lv_type
        , lv_brand
        , flight_id
        , launch_agency_code
        , launch_agency_country
        , launch_code
        , launch_category
        , launch_success_code
        , launch_time_ref
        , current_owner_code
        , current_state_code
        , _source_updated_at
    from {{ ref('int__jsr__launch_events') }}
)

, cte_final as (
    select
        cast(jcat as varchar) as jcat
        , cast(launch_tag as varchar) as launch_tag
        , cast(launch_datetime as timestamp) as launch_datetime
        , cast(launch_datetime_start as timestamp) as launch_datetime_start
        , cast(launch_datetime_end as timestamp) as launch_datetime_end
        , cast(launch_datetime_precision as varchar) as launch_datetime_precision
        , cast(cospar_id as varchar) as cospar_id
        , cast(flag_catalog_match_uncertain as integer) as flag_catalog_match_uncertain
        , cast(site_code as varchar) as site_code
        , cast(flag_site_uncertain as integer) as flag_site_uncertain
        , cast(launch_pad as varchar) as launch_pad
        , cast(ascent_site_code as varchar) as ascent_site_code
        , cast(ascent_pad as varchar) as ascent_pad
        , cast(launch_platform as varchar) as launch_platform
        , cast(lv_type as varchar) as lv_type
        , cast(lv_brand as varchar) as lv_brand
        , cast(flight_id as varchar) as flight_id
        , cast(launch_agency_code as varchar) as launch_agency_code
        , cast(launch_agency_country as varchar) as launch_agency_country
        , cast(launch_code as varchar) as launch_code
        , cast(launch_category as varchar) as launch_category
        , cast(launch_success_code as varchar) as launch_success_code
        , cast(launch_time_ref as varchar) as launch_time_ref
        , cast(current_owner_code as varchar) as current_owner_code
        , cast(current_state_code as varchar) as current_state_code
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , {{ helper__audit_fields() }}
    from cte_int__jsr__launch_events
)

select * from cte_final
