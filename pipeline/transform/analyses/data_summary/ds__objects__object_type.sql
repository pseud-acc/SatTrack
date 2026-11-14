-- Objects tab: objects by Space-Track object type.
with cte_fct__satellite_master as (
    select
        object_type
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        object_type
        , count(*) as objects
    from cte_fct__satellite_master
    group by object_type
)

select * from cte_final
