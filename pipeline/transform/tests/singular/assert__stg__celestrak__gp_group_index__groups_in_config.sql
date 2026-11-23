{{ config(severity='warn') }}
-- Warns, never fails (D-026, D-037 emails it): CelesTrak's GP index lists a group that the group config
-- (sattrack_ingest/config.py) neither includes nor excludes, or an included group is no longer on the index.
-- Either way the config needs a look: add the new group to one of the lists, or drop the vanished one.
-- An empty index (no download has succeeded yet) checks nothing.
with cte_stg__celestrak__gp_group_index as (
    select
        celestrak_group
    from {{ ref('stg__celestrak__gp_group_index') }}
)

, cte_stg__celestrak__group_config as (
    select
        celestrak_group
        , celestrak_group_kind
    from {{ ref('stg__celestrak__group_config') }}
)

, cte_groups_not_in_config as (
    select
        'not_in_config' as check_name
        , idx.celestrak_group
    from cte_stg__celestrak__gp_group_index as idx
    left join cte_stg__celestrak__group_config as cfg
        on cfg.celestrak_group = idx.celestrak_group
    where cfg.celestrak_group is null
)

, cte_index_size as (
    select
        count(*) as listed_groups
    from cte_stg__celestrak__gp_group_index
)

, cte_included_not_on_index as (
    select
        'included_not_on_index' as check_name
        , cfg.celestrak_group
    from cte_stg__celestrak__group_config as cfg
    inner join cte_index_size as size
        on size.listed_groups > 0
    left join cte_stg__celestrak__gp_group_index as idx
        on idx.celestrak_group = cfg.celestrak_group
    where idx.celestrak_group is null
        and cfg.celestrak_group_kind in ('constellation', 'operator')
)

select
    check_name
    , celestrak_group
from cte_groups_not_in_config
union all
select
    check_name
    , celestrak_group
from cte_included_not_on_index
