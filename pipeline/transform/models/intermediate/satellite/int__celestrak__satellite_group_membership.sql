-- One row per object and CelesTrak constellation or system group it is listed in (D-026, D-047), with the group's
-- display name and whether the object's name fits the group. CelesTrak is the golden source for these groupings.
--   * Only groups the config downloads as a constellation or a system (kinds constellation, system, system_hosted,
--     system_hosted_umbrella) count; station and excluded groups never do.
--   * member_system_token / member_prn: what CelesTrak writes in a member's name, e.g. "SES-5 (EGNOS/PRN 136)" gives
--     EGNOS and 136; "BEIDOU-3 G1 (PRN 130)" gives no token and 130. Used for sbas, whose members name their system.
--   * Display name: CelesTrak's group title on its GP index page without the word "Operational"
--     ("GPS Operational" -> "GPS"). A group missing from the index has no name and is left out.
--   * Member-name prefix (D-046): a group with one counts only members whose CelesTrak OBJECT_NAME starts with it.
--   * flag_name_fits_group (D-046 name check, D-047): 1 when the member's name contains the group's expected string
--     (its prefix, else the most common leading word of its members' names, e.g. TDRS for tdrss, STARLINK for
--     starlink); exceptions live in helper__flag_member_name_fits_group. System groups keep only fitting members.
with cte_stg__celestrak__gp_group_member as (
    select
        celestrak_group
        , satcat_id
        , object_name
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
        , celestrak_group_member_name_prefix
    from {{ ref('stg__celestrak__group_config') }}
)

, cte_grouping_groups as ( -- downloaded constellation and system groups CelesTrak lists, with display names
    select
        cfg.celestrak_group
        , cfg.celestrak_group_kind
        , cfg.celestrak_group_order
        , cfg.celestrak_group_member_name_prefix
        , nullif(
            trim(regexp_replace(regexp_replace(idx.celestrak_group_title, '\bOperational\b', '', 'g'), '\s+', ' ', 'g'))
            , ''
        ) as grouping_name
    from cte_stg__celestrak__group_config as cfg
    inner join cte_stg__celestrak__gp_group_index as idx
        on idx.celestrak_group = cfg.celestrak_group
    where cfg.celestrak_group_kind in ('constellation', 'system', 'system_hosted', 'system_hosted_umbrella')
)

, cte_member_name_stems as ( -- each member's leading word: the letters before the first non-letter
    select
        celestrak_group
        , regexp_extract(upper(object_name), '^[A-Z]+') as name_stem
    from cte_stg__celestrak__gp_group_member
    where object_name is not null
)

, cte_ranked_group_stems as ( -- each group's leading words, most common first (ties: alphabetical)
    select
        celestrak_group
        , name_stem
        , row_number() over (
            partition by celestrak_group
            order by count(*) desc, name_stem
        ) as stem_rank
    from cte_member_name_stems
    where name_stem <> ''
    group by
        celestrak_group
        , name_stem
)

, cte_memberships as ( -- members of those groups that meet the group's prefix (D-046)
    select
        mem.satcat_id
        , grp.celestrak_group
        , grp.celestrak_group_kind
        , grp.celestrak_group_order
        , grp.grouping_name
        , mem.object_name
        , upper(coalesce(grp.celestrak_group_member_name_prefix, stm.name_stem)) as expected_name_string
    from cte_stg__celestrak__gp_group_member as mem
    inner join cte_grouping_groups as grp
        on grp.celestrak_group = mem.celestrak_group
    left join cte_ranked_group_stems as stm
        on stm.celestrak_group = mem.celestrak_group
        and stm.stem_rank = 1
    where mem.satcat_id is not null
        and grp.grouping_name is not null
        and (
            grp.celestrak_group_member_name_prefix is null
            or starts_with(upper(mem.object_name), upper(grp.celestrak_group_member_name_prefix))
        )
)

, cte_final as (
    select
        cast(satcat_id as integer) as satcat_id
        , cast(celestrak_group as varchar) as celestrak_group
        , cast(celestrak_group_kind as varchar) as celestrak_group_kind
        , cast(celestrak_group_order as integer) as celestrak_group_order
        , cast(grouping_name as varchar) as grouping_name
        , cast(object_name as varchar) as object_name
        , cast(expected_name_string as varchar) as expected_name_string
        , cast(nullif(regexp_extract(upper(object_name), '\(([A-Z0-9-]+)/PRN', 1), '') as varchar) as member_system_token
        , cast(nullif(regexp_extract(upper(object_name), 'PRN ([0-9]+)\)', 1), '') as varchar) as member_prn
        , cast(
            {{ helper__flag_member_name_fits_group('celestrak_group', 'object_name', 'expected_name_string') }}
            as integer
        ) as flag_name_fits_group
        , {{ helper__audit_fields() }}
    from cte_memberships
)

select * from cte_final
