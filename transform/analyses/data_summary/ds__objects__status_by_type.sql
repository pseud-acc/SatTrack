-- Objects tab: active vs inactive objects per object type.
with cte_fct__satellite_master as (
    select
        object_type
        , status
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        object_type
        , status
        , count(*) as objects
    from cte_fct__satellite_master
    group by
        object_type
        , status
)

select * from cte_final
