-- Launches tab: objects in the current catalogue by launch year, by object type.
with cte_fct__satellite_master as (
    select
        launch_year
        , object_type
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        launch_year
        , object_type
        , count(*) as objects
    from cte_fct__satellite_master
    where launch_year is not null
    group by
        launch_year
        , object_type
    order by launch_year
)

select * from cte_final
