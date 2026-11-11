-- Ownership tab: the 15 owner countries or organisations with the most objects, by object type.
with cte_fct__satellite_master as (
    select
        owner_country
        , object_type
    from {{ ref('fct__satellite_master') }}
)

, cte_top_owners as (
    select
        owner_country
    from cte_fct__satellite_master
    where owner_country is not null
    group by owner_country
    order by count(*) desc
    limit 15
)

, cte_final as (
    select
        cte_fct__satellite_master.owner_country
        , cte_fct__satellite_master.object_type
        , count(*) as objects
    from cte_fct__satellite_master
    inner join cte_top_owners
        on cte_fct__satellite_master.owner_country = cte_top_owners.owner_country
    group by
        cte_fct__satellite_master.owner_country
        , cte_fct__satellite_master.object_type
)

select * from cte_final
