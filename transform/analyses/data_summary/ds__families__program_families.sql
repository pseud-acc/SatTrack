-- Programme families tab: the 15 largest programme families (satellite_program_family, from the GCAT Program field)
-- with at least 50 payloads, by status. Some are constellations, others long-running series.
with cte_fct__satellite_master as (
    select
        object_type
        , status
        , satellite_program_family
    from {{ ref('fct__satellite_master') }}
)

, cte_families as (
    select
        satellite_program_family
        , status
    from cte_fct__satellite_master
    where object_type = 'PAYLOAD'
        and satellite_program_family is not null
)

, cte_large_families as (
    select
        satellite_program_family
    from cte_families
    group by satellite_program_family
    having count(*) >= 50
    order by count(*) desc
    limit 15
)

, cte_final as (
    select
        cte_families.satellite_program_family
        , cte_families.status
        , count(*) as payloads
    from cte_families
    inner join cte_large_families
        on cte_families.satellite_program_family = cte_large_families.satellite_program_family
    group by
        cte_families.satellite_program_family
        , cte_families.status
)

select * from cte_final
