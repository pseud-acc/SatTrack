{{ config(severity='warn') }}
-- Warns, never fails (D-046, D-037 emails it): a constellation membership whose CelesTrak OBJECT_NAME doesn't contain
-- the name its group's members carry, i.e. CelesTrak may list spacecraft in the group that aren't the constellation
-- (as tdrss lists the spacecraft that use TDRSS). The expected string is the group's member-name prefix from the
-- config when it has one (tdrss: "TDRS"), else the most common leading word of the group's member names (e.g.
-- STARLINK, GPS, COSMOS for glo-ops, GSAT for galileo), derived from the data each run, with no list of exceptions.
-- Operator groups (kind operator: planet, ses, ...) list an operator's fleet under its own satellite names, so they
-- are not checked. A second check warns when a group's prefix matches none of its members (CelesTrak renamed them).
with cte_int__celestrak__satellite_constellation as (
    select
        satcat_id
        , celestrak_group
    from {{ ref('int__celestrak__satellite_constellation') }}
)

, cte_stg__celestrak__gp_group_member as (
    select
        celestrak_group
        , satcat_id
        , object_name
    from {{ ref('stg__celestrak__gp_group_member') }}
)

, cte_stg__celestrak__group_config as (
    select
        celestrak_group
        , celestrak_group_kind
        , celestrak_group_member_name_prefix
    from {{ ref('stg__celestrak__group_config') }}
)

, cte_member_name_stems as ( -- each member's leading word: the letters before the first non-letter
    select
        celestrak_group
        , satcat_id
        , object_name
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

, cte_expected_names as ( -- constellation groups: the config prefix, else the most common leading word
    select
        cfg.celestrak_group
        , upper(coalesce(cfg.celestrak_group_member_name_prefix, stm.name_stem)) as expected_name_string
    from cte_stg__celestrak__group_config as cfg
    left join cte_ranked_group_stems as stm
        on stm.celestrak_group = cfg.celestrak_group
        and stm.stem_rank = 1
    where cfg.celestrak_group_kind = 'constellation'
)

, cte_names_lacking_expected_string as (
    select
        'name_lacks_expected_string' as check_name
        , con.celestrak_group
        , con.satcat_id
        , mem.object_name
        , exp.expected_name_string
    from cte_int__celestrak__satellite_constellation as con
    inner join cte_expected_names as exp
        on exp.celestrak_group = con.celestrak_group
    inner join cte_stg__celestrak__gp_group_member as mem
        on mem.celestrak_group = con.celestrak_group
        and mem.satcat_id = con.satcat_id
    where exp.expected_name_string is not null
        and strpos(upper(coalesce(mem.object_name, '')), exp.expected_name_string) = 0
)

, cte_prefix_matches_none as (
    select
        'prefix_matches_no_member' as check_name
        , cfg.celestrak_group
        , cast(null as integer) as satcat_id
        , cast(null as varchar) as object_name
        , upper(cfg.celestrak_group_member_name_prefix) as expected_name_string
    from cte_stg__celestrak__group_config as cfg
    inner join cte_member_name_stems as mem
        on mem.celestrak_group = cfg.celestrak_group
    where cfg.celestrak_group_member_name_prefix is not null
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
