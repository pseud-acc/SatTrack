-- Ownership tab: payloads per GCAT ownership class label.
-- A payload with several classes counts once in each; payloads without a class show as 'Not classified'.
with cte_fct__satellite_master as (
    select
        object_type
        , ownership_class_labels
    from {{ ref('fct__satellite_master') }}
)

, cte_labels as (
    select
        coalesce(label.ownership_class, 'Not classified') as ownership_class
    from cte_fct__satellite_master
    left join unnest(ownership_class_labels) as label(ownership_class)
        on true
    where object_type = 'PAYLOAD'
)

, cte_final as (
    select
        ownership_class
        , count(*) as payloads
    from cte_labels
    group by ownership_class
)

select * from cte_final
