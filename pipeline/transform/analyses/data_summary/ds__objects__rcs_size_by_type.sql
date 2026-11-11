-- Objects tab: radar cross-section size class per object type (unreported shown as 'Not reported').
with cte_fct__satellite_master as (
    select
        object_type
        , rcs_size
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        object_type
        , coalesce(rcs_size, 'Not reported') as rcs_size
        , count(*) as objects
    from cte_fct__satellite_master
    group by
        object_type
        , coalesce(rcs_size, 'Not reported')
)

select * from cte_final
