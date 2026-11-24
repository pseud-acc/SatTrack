-- One row per object in a configured CelesTrak constellation or operator group (D-026): the group's display name.
-- Rules: only groups the config includes (kind constellation or operator) count; every other group is excluded.
-- An object in two included groups takes the first in config order (constellations, then operators). The display
-- name is CelesTrak's group title on its GP index page with the word "Operational" removed ("GPS Operational" -> "GPS").
with cte_stg__celestrak__gp_group_member as (
    select
        celestrak_group
        , satcat_id
    from {{ ref('stg__celestrak__gp_group_member') }}
)

, cte_stg__celestrak__gp_group_index as (
    select
        celestrak_group
        , celestrak_group_title
    from {{ ref('stg__celestrak__gp_group_index') }}
)

, cte_stg__celestrak__group_config as (
    select
        celestrak_group
        , celestrak_group_kind
        , celestrak_group_order
    from {{ ref('stg__celestrak__group_config') }}
)

, cte_included_groups as ( -- configured groups CelesTrak lists, with their display names
    select
        cfg.celestrak_group
        , cfg.celestrak_group_order
        , nullif(
            trim(regexp_replace(regexp_replace(idx.celestrak_group_title, '\bOperational\b', '', 'g'), '\s+', ' ', 'g'))
            , ''
        ) as constellation
    from cte_stg__celestrak__group_config as cfg
    inner join cte_stg__celestrak__gp_group_index as idx
        on idx.celestrak_group = cfg.celestrak_group
    where cfg.celestrak_group_kind in ('constellation', 'operator')
)

, cte_ranked_memberships as ( -- one row per object and included group, ranked by config order
    select
        mem.satcat_id
        , grp.celestrak_group
        , grp.constellation
        , row_number() over (
            partition by mem.satcat_id
            order by grp.celestrak_group_order, grp.celestrak_group
        ) as membership_rank
    from cte_stg__celestrak__gp_group_member as mem
    inner join cte_included_groups as grp
        on grp.celestrak_group = mem.celestrak_group
    where mem.satcat_id is not null
        and grp.constellation is not null
)

, cte_final as (
    select
        cast(satcat_id as integer) as satcat_id
        , cast(constellation as varchar) as constellation
        , cast(celestrak_group as varchar) as celestrak_group
        , {{ helper__audit_fields() }}
    from cte_ranked_memberships
    where membership_rank = 1
)

select * from cte_final
