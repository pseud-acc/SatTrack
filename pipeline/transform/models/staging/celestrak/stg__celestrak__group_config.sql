-- 1:1 with raw_celestrak.group_config (the pipeline's CelesTrak group list, sattrack_ingest/config.py, D-026):
-- rename + cast only.
with cte_final as (
    select
        cast("GROUP" as varchar) as celestrak_group
        , cast("GROUP_KIND" as varchar) as celestrak_group_kind
        , try_cast(nullif("GROUP_ORDER", '') as integer) as celestrak_group_order
        , cast(nullif("GROUP_MEMBER_NAME_PREFIX", '') as varchar) as celestrak_group_member_name_prefix
        , cast(_loaded_at as timestamp) as _loaded_at
        , _run_id
    from {{ source('celestrak', 'group_config') }}
)

select * from cte_final
