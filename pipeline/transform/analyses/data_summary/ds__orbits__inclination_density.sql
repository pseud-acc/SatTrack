-- Orbits tab: density of orbital inclination (2 degree bins), by orbit class.
with cte_fct__satellite_master as (
    select
        orbit_class
        , inclination
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        cast(floor(inclination / 2) * 2 as integer) as inclination_deg
        , coalesce(orbit_class, 'Not classified') as orbit_class
        , count(*) as objects
    from cte_fct__satellite_master
    where inclination is not null
    group by
        cast(floor(inclination / 2) * 2 as integer)
        , coalesce(orbit_class, 'Not classified')
    order by inclination_deg
)

select * from cte_final
