-- 1:1 with raw_celestrak.gp_group_index (every group CelesTrak's GP index page lists, D-026): rename + cast only.
with cte_final as (
    select
        cast("GROUP" as varchar) as celestrak_group
        , cast(nullif(trim("GROUP_TITLE"), '') as varchar) as celestrak_group_title
        , try_cast("INDEX_POSITION" as integer) as celestrak_index_position
        , cast(_loaded_at as timestamp) as _loaded_at
        , _run_id
    from {{ source('celestrak', 'gp_group_index') }}
)

select * from cte_final
