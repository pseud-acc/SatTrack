-- One row per GCAT launch site, with both country fields (decided 2026-10-25), and the dim__country key of the location country:
--   site_state            = the responsible state (GCAT StateCode), named from GCAT's country-like orgs;
--   site_location_country = where the site physically is: country of the nearest pinned GeoNames city to the
--                           GCAT coordinates. Astronomical-polity states (e.g. LUNA) give that body; GCAT type LC
--                           (launch cruise) or a site > 150 km from any city whose name says ocean/sea gives 'At sea'.
--   site_location_country_sk = the country_sk (int__pycountry__geo_countries) of the nearest city's ISO alpha-2 code, a
--                           current country before a former one; NULL unless the location country comes from the nearest city.
with cte_stg__jsr__sites as (
    select
        site_code
        , site_ucode
        , site_type
        , site_state_code
        , site_short_name
        , site_name
        , site_short_name_en
        , site_latitude
        , site_longitude
        , site_location
        , site_operator_code
        , site_start_date_raw
        , site_stop_date_raw
        , _source_updated_at
    from {{ ref('stg__jsr__sites') }}
)

, cte_stg__geonames__cities as (
    select
        geonameid
        , city_name
        , iso_alpha2
        , latitude
        , longitude
    from {{ ref('stg__geonames__cities') }}
)

, cte_stg__pycountry__iso_countries as (
    select
        iso_alpha2
        , country_name
        , country_common_name
        , is_historic
    from {{ ref('stg__pycountry__iso_countries') }}
)

, cte_int__pycountry__geo_countries as (
    select
        country_sk
        , iso_alpha2
        , is_historic
    from {{ ref('int__pycountry__geo_countries') }}
)

, cte_int__jsr__org_organisations as (
    select
        org_code
        , org_display_name
        , org_type
    from {{ ref('int__jsr__org_organisations') }}
)

, cte_site_nearest_city as ( -- nearest pinned GeoNames city to each site with coordinates
    select
        s.site_code
        , c.iso_alpha2
        , c.city_name
        , {{ helper__calculate_haversine_km('s.site_latitude', 's.site_longitude', 'c.latitude', 'c.longitude') }} as km
    from cte_stg__jsr__sites as s
    cross join cte_stg__geonames__cities as c
    where s.site_latitude is not null and s.site_longitude is not null
    qualify row_number() over (partition by s.site_code order by km, c.geonameid) = 1
)

, cte_current_country_names as (
    select
        iso_alpha2
        , coalesce(country_common_name, country_name) as country_name
    from cte_stg__pycountry__iso_countries
    where not is_historic
)

, cte_country_key_by_alpha2 as ( -- one country key per alpha-2 code: a current country before a former one
    select
        iso_alpha2
        , country_sk
    from cte_int__pycountry__geo_countries
    qualify row_number() over (partition by iso_alpha2 order by is_historic, country_sk) = 1
)

, cte_sites_located as ( -- each site with its responsible state and how its location country is decided
    select
        s.*
        , n.iso_alpha2 as nearest_iso_alpha2
        , n.city_name as nearest_city
        , n.km as nearest_km
        , st.org_display_name as site_state
        , case
            when coalesce(st.org_type, '') like '%AP%' then 'astronomical_polity'
            when s.site_type = 'LC' then 'launch_cruise'
            when n.km > 150 and (s.site_name ilike '%ocean%' or s.site_name ilike '%sea%') then 'at_sea'
            when n.iso_alpha2 is not null then 'nearest_city'
            else 'no_coordinates'
        end as site_location_method
    from cte_stg__jsr__sites as s
    left join cte_site_nearest_city as n using (site_code)
    left join cte_int__jsr__org_organisations as st on st.org_code = s.site_state_code
)

, cte_final as (
    select
        c.site_code
        , c.site_ucode
        , c.site_type
        , c.site_short_name
        , c.site_name
        , coalesce(c.site_short_name_en, c.site_short_name) as site_display_name
        , c.site_latitude
        , c.site_longitude
        , c.site_location
        , c.site_operator_code
        , c.site_state_code
        , c.site_state
        , case c.site_location_method
            when 'astronomical_polity' then c.site_state
            when 'launch_cruise' then 'At sea'
            when 'at_sea' then 'At sea'
            else iso.country_name
        end as site_location_country
        , case when c.site_location_method = 'nearest_city' then c.nearest_iso_alpha2 end as site_location_iso_alpha2
        , case when c.site_location_method = 'nearest_city' then ck.country_sk end as site_location_country_sk
        , c.site_location_method
        , c.nearest_city
        , round(c.nearest_km, 1) as nearest_city_km
        , {{ helper__parse_vague_date_columns('c.site_start_date_raw', 'site_start_date') }}
        , (c.site_stop_date_raw is null or c.site_stop_date_raw = '*') as flag_site_active
        , c._source_updated_at
        , {{ helper__audit_fields() }}
    from cte_sites_located as c
    left join cte_current_country_names as iso on iso.iso_alpha2 = c.nearest_iso_alpha2
    left join cte_country_key_by_alpha2 as ck on ck.iso_alpha2 = c.nearest_iso_alpha2
)

select * from cte_final
