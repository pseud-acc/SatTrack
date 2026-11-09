-- Orbits tab: objects per TLE-based orbit class (app 5-class rule on the Space-Track element set), by status.
with cte_fct__satellite_master as (
    select
        orbit_class
        , status
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        coalesce(orbit_class, 'Not classified') as orbit_class
        , status
        , count(*) as objects
    from cte_fct__satellite_master
    group by
        coalesce(orbit_class, 'Not classified')
        , status
)

select * from cte_final
