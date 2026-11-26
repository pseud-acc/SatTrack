{{ config(severity='warn') }}
-- Warns, never fails (D-046, D-047, D-037 emails it). Two checks on CelesTrak's groups:
--   * name_lacks_expected_string: a member of a constellation group whose name doesn't fit the group (its prefix,
--     else the most common leading word of its members' names), i.e. CelesTrak may list spacecraft in the group that
--     aren't the constellation. System groups aren't reported: they drop such members by rule (D-047), and hosted
--     groups list several programmes by design. Exceptions live in helper__flag_member_name_fits_group.
--   * prefix_matches_no_member: a group's member-name prefix matches none of its members (CelesTrak renamed them).
with cte_int__celestrak__satellite_group_membership as (
    select
        satcat_id
        , celestrak_group
        , celestrak_group_kind
        , object_name
        , expected_name_string
        , flag_name_fits_group
    from {{ ref('int__celestrak__satellite_group_membership') }}
)

, cte_stg__celestrak__gp_group_member as (
    select
        celestrak_group
        , object_name
    from {{ ref('stg__celestrak__gp_group_member') }}
)

, cte_stg__celestrak__group_config as (
    select
        celestrak_group
        , celestrak_group_member_name_prefix
    from {{ ref('stg__celestrak__group_config') }}
)

, cte_names_lacking_expected_string as (
    select
        'name_lacks_expected_string' as check_name
        , celestrak_group
        , satcat_id
        , object_name
        , expected_name_string
    from cte_int__celestrak__satellite_group_membership
    where celestrak_group_kind = 'constellation'
        and expected_name_string is not null
        and flag_name_fits_group = 0
)

, cte_prefix_matches_none as (
    select
        'prefix_matches_no_member' as check_name
        , cfg.celestrak_group
        , cast(null as integer) as satcat_id
        , cast(null as varchar) as object_name
        , upper(cfg.celestrak_group_member_name_prefix) as expected_name_string
    from cte_stg__celestrak__group_config as cfg
    inner join cte_stg__celestrak__gp_group_member as mem
        on mem.celestrak_group = cfg.celestrak_group
    where cfg.celestrak_group_member_name_prefix is not null
        and mem.object_name is not null
    group by
        cfg.celestrak_group
        , cfg.celestrak_group_member_name_prefix
    having sum(
        case when starts_with(upper(mem.object_name), upper(cfg.celestrak_group_member_name_prefix)) then 1 else 0 end
    ) = 0
)

select
    check_name
    , celestrak_group
    , satcat_id
    , object_name
    , expected_name_string
from cte_names_lacking_expected_string
union all
select
    check_name
    , celestrak_group
    , satcat_id
    , object_name
    , expected_name_string
from cte_prefix_matches_none
