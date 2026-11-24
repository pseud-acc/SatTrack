-- 1:1 with raw_celestrak.gp_group_member (one row per object per configured CelesTrak group, D-026): rename + cast only.
with cte_final as (
    select
        cast("GROUP" as varchar) as celestrak_group
        , try_cast("NORAD_CAT_ID" as integer) as satcat_id
        , cast(nullif("OBJECT_NAME", '') as varchar) as object_name
        , cast(nullif("OBJECT_ID", '') as varchar) as object_id
        , cast(_loaded_at as timestamp) as _loaded_at
        , _run_id
    from {{ source('celestrak', 'gp_group_member') }}
)

select * from cte_final
