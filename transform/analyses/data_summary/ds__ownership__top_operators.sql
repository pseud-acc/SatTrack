-- Ownership tab: the 15 operators with the most payloads, by status.
with cte_fct__satellite_master as (
    select
        operator_name
        , object_type
        , status
    from {{ ref('fct__satellite_master') }}
)

, cte_payloads as (
    select
        operator_name
        , status
    from cte_fct__satellite_master
    where object_type = 'PAYLOAD'
        and operator_name is not null
)

, cte_top_operators as (
    select
        operator_name
    from cte_payloads
    group by operator_name
    order by count(*) desc
    limit 15
)

, cte_final as (
    select
        cte_payloads.operator_name
        , cte_payloads.status
        , count(*) as payloads
    from cte_payloads
    inner join cte_top_operators
        on cte_payloads.operator_name = cte_top_operators.operator_name
    group by
        cte_payloads.operator_name
        , cte_payloads.status
)

select * from cte_final
