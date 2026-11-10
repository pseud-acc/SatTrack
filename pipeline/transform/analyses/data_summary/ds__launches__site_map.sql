-- Launches tab: objects per launch site, with the site coordinates for the map.
with cte_fct__satellite_master as (
    select
        site_name
        , site_location_country
        , site_latitude
        , site_longitude
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        site_name
        , any_value(site_location_country) as site_country
        , avg(site_latitude) as latitude
        , avg(site_longitude) as longitude
        , count(*) as objects
    from cte_fct__satellite_master
    where site_latitude is not null
        and site_longitude is not null
    group by site_name
)

select * from cte_final
