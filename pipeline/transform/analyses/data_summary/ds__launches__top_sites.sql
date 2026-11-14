-- Launches tab: the 15 launch sites with the most catalogued objects, by object type.
with cte_fct__satellite_master as (
    select
        site_name
        , object_type
    from {{ ref('fct__satellite_master') }}
)

, cte_top_sites as (
    select
        site_name
    from cte_fct__satellite_master
    where site_name is not null
    group by site_name
    order by count(*) desc
    limit 15
)

, cte_final as (
    select
        cte_fct__satellite_master.site_name
        , cte_fct__satellite_master.object_type
        , count(*) as objects
    from cte_fct__satellite_master
    inner join cte_top_sites
        on cte_fct__satellite_master.site_name = cte_top_sites.site_name
    group by
        cte_fct__satellite_master.site_name
        , cte_fct__satellite_master.object_type
)

select * from cte_final
