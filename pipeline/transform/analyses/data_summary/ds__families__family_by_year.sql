-- Programme families tab: payloads by launch year for the 6 largest programme families (satellite_program_family);
-- every other payload falls into 'Other' or 'No programme'.
with cte_fct__satellite_master as (
    select
        object_type
        , launch_year
        , satellite_program_family
    from {{ ref('fct__satellite_master') }}
)

, cte_payloads as (
    select
        launch_year
        , satellite_program_family as program_family
    from cte_fct__satellite_master
    where object_type = 'PAYLOAD'
        and launch_year is not null
)

, cte_top_families as (
    select
        program_family
    from cte_payloads
    where program_family is not null
    group by program_family
    having count(*) >= 50
    order by count(*) desc
    limit 6
)

, cte_grouped as (
    select
        cte_payloads.launch_year
        , case
            when cte_top_families.program_family is not null then cte_top_families.program_family
            when cte_payloads.program_family is null then 'No programme'
            else 'Other'
        end as program_group
    from cte_payloads
    left join cte_top_families
        on cte_payloads.program_family = cte_top_families.program_family
)

, cte_final as (
    select
        launch_year
        , program_group
        , count(*) as payloads
    from cte_grouped
    group by
        launch_year
        , program_group
    order by launch_year
)

select * from cte_final
