-- Programme families tab: the 20 GCAT programmes (shell level, e.g. 'Starlink 2MO S1') with the most payloads.
with cte_fct__satellite_master as (
    select
        object_type
        , satellite_program
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        satellite_program
        , count(*) as payloads
    from cte_fct__satellite_master
    where object_type = 'PAYLOAD'
        and satellite_program is not null
    group by satellite_program
    order by payloads desc
    limit 20
)

select * from cte_final
