-- Ownership tab: the 15 manufacturers with the most payloads.
with cte_fct__satellite_master as (
    select
        manufacturer_name
        , object_type
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        manufacturer_name
        , count(*) as payloads
    from cte_fct__satellite_master
    where object_type = 'PAYLOAD'
        and manufacturer_name is not null
    group by manufacturer_name
    order by payloads desc
    limit 15
)

select * from cte_final
