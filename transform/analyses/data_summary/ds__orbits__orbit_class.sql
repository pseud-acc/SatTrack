-- Orbits tab: objects per TLE-based orbit class (app 5-class rule on the Space-Track element set), by object type.
with cte_fct__satellite_master as (
    select
        orbit_class
        , object_type
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        coalesce(orbit_class, 'Not classified') as orbit_class
        , object_type
        , count(*) as objects
    from cte_fct__satellite_master
    group by
        coalesce(orbit_class, 'Not classified')
        , object_type
)

select * from cte_final
