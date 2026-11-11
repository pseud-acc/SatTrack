-- Launches tab: the 15 launch vehicle brands that put the most catalogued payloads in orbit.
with cte_fct__satellite_master as (
    select
        launch_vehicle_brand
        , object_type
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        launch_vehicle_brand
        , count(*) as payloads
    from cte_fct__satellite_master
    where object_type = 'PAYLOAD'
        and launch_vehicle_brand is not null
    group by launch_vehicle_brand
    order by payloads desc
    limit 15
)

select * from cte_final
