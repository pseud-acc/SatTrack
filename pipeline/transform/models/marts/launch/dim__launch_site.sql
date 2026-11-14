-- One row per GCAT launch site, with its responsible state and physical location country.
with cte_int__jsr__launch_sites as (
    select
        site_code
        , site_ucode
        , site_type
        , site_short_name
        , site_name
        , site_display_name
        , site_latitude
        , site_longitude
        , site_location
        , site_operator_code
        , site_state_code
        , site_state
        , site_location_country
        , site_location_iso_alpha2
        , site_location_country_sk
        , site_location_method
        , nearest_city
        , nearest_city_km
        , site_start_date
        , site_start_date_start
        , site_start_date_end
        , site_start_date_precision
        , flag_site_active
        , _source_updated_at
    from {{ ref('int__jsr__launch_sites') }}
)

, cte_final as (
    select
        cast(site_code as varchar) as site_code
        , cast(site_ucode as varchar) as site_ucode
        , cast(site_type as varchar) as site_type
        , cast(site_short_name as varchar) as site_short_name
        , cast(site_name as varchar) as site_name
        , cast(site_display_name as varchar) as site_display_name
        , cast(site_latitude as double) as site_latitude
        , cast(site_longitude as double) as site_longitude
        , cast(site_location as varchar) as site_location
        , cast(site_operator_code as varchar) as site_operator_code
        , cast(site_state_code as varchar) as site_state_code
        , cast(site_state as varchar) as site_state
        , cast(site_location_country as varchar) as site_location_country
        , cast(site_location_iso_alpha2 as varchar) as site_location_iso_alpha2
        , cast(site_location_country_sk as varchar) as site_location_country_sk
        , cast(site_location_method as varchar) as site_location_method
        , cast(nearest_city as varchar) as nearest_city
        , cast(nearest_city_km as double) as nearest_city_km
        , cast(site_start_date as timestamp) as site_start_date
        , cast(site_start_date_start as timestamp) as site_start_date_start
        , cast(site_start_date_end as timestamp) as site_start_date_end
        , cast(site_start_date_precision as varchar) as site_start_date_precision
        , cast(flag_site_active as integer) as flag_site_active
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , {{ helper__audit_fields() }}
    from cte_int__jsr__launch_sites
)

select * from cte_final
