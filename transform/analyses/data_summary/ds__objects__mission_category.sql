-- Objects tab: the 15 most common GCAT mission categories across payloads, by status.
-- A payload with several categories counts once in each.
with cte_fct__satellite_master as (
    select
        object_type
        , status
        , mission_category_labels
    from {{ ref('fct__satellite_master') }}
)

, cte_payload_categories as (
    select
        category.mission_category
        , status
    from cte_fct__satellite_master
    cross join unnest(mission_category_labels) as category(mission_category)
    where object_type = 'PAYLOAD'
)

, cte_top_categories as (
    select
        mission_category
    from cte_payload_categories
    group by mission_category
    order by count(*) desc
    limit 15
)

, cte_final as (
    select
        cte_payload_categories.mission_category
        , cte_payload_categories.status
        , count(*) as payloads
    from cte_payload_categories
    inner join cte_top_categories
        on cte_payload_categories.mission_category = cte_top_categories.mission_category
    group by
        cte_payload_categories.mission_category
        , cte_payload_categories.status
)

select * from cte_final
