-- Orbits tab: density of perigee altitude from 100 to 2,000 km (10 km bins), by object type.
with cte_fct__satellite_master as (
    select
        object_type
        , periapsis
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        cast(floor(periapsis / 10) * 10 as integer) as perigee_km
        , object_type
        , count(*) as objects
    from cte_fct__satellite_master
    where periapsis >= 100
        and periapsis < 2000
    group by
        cast(floor(periapsis / 10) * 10 as integer)
        , object_type
    order by perigee_km
)

select * from cte_final
