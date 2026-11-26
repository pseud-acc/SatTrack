-- One row per object in the GP feed that belongs to a constellation (D-047): near-identical satellites working
-- together. CelesTrak is the golden source:
--   * CelesTrak constellation groups (int__celestrak__satellite_group_membership, kind constellation), named by
--     CelesTrak's title; an object in two groups takes the first in config order;
--   * plus the few CelesTrak has no group for, from the ad-hoc seed manual_satellite_grouping (kind constellation):
--     payloads with their own GCAT payload record (mission_details_source = 'own') whose programme family is one of
--     the rule's values, or whose name matches its regular expression. Debris and stages inherit their parent's
--     programme, so they never match.
-- A CelesTrak group beats a manual row; two manual rows are taken in name order.
with cte_int__celestrak__satellite_group_membership as (
    select
        satcat_id
        , celestrak_group
        , celestrak_group_kind
        , celestrak_group_order
        , grouping_name
    from {{ ref('int__celestrak__satellite_group_membership') }}
)

, cte_stg__sattrack__manual_satellite_grouping as (
    select
        grouping_kind
        , grouping_name
        , definition_rule_type
        , definition_rule_values
    from {{ ref('stg__sattrack__manual_satellite_grouping') }}
)

, cte_int__xsrc__satellite_gcat_matched as (
    select
        satcat_id
        , jcat
        , object_name
        , object_type
    from {{ ref('int__xsrc__satellite_gcat_matched') }}
)

, cte_int__jsr__satellite_status as (
    select
        jcat
        , satellite_program_family
        , mission_details_source
    from {{ ref('int__jsr__satellite_status') }}
)

, cte_manual_rules as ( -- one row per manual constellation and rule value (`|`-separated; a pattern stays whole)
    select
        grouping_name
        , definition_rule_type
        , unnest(
            case
                when definition_rule_type = 'object_name_regex' then [definition_rule_values]  -- a pattern is one value
                else string_split(definition_rule_values, '|')
            end
        ) as rule_value
    from cte_stg__sattrack__manual_satellite_grouping
    where grouping_kind = 'constellation'
)

, cte_own_payloads as ( -- GP objects that are payloads with their own GCAT payload record
    select
        sat.satcat_id
        , upper(sat.object_name) as object_name
        , st.satellite_program_family
    from cte_int__xsrc__satellite_gcat_matched as sat
    inner join cte_int__jsr__satellite_status as st
        on st.jcat = sat.jcat
    where sat.object_type = 'PAYLOAD'
        and st.mission_details_source = 'own'
)

, cte_celestrak_memberships as ( -- GP objects in a CelesTrak constellation group
    select
        mem.satcat_id
        , mem.grouping_name as satellite_constellation_name
        , 'celestrak_group' as constellation_source
        , mem.celestrak_group as constellation_rule_value
        , 0 as source_rank
        , mem.celestrak_group_order as order_in_source
    from cte_int__celestrak__satellite_group_membership as mem
    inner join cte_int__xsrc__satellite_gcat_matched as sat
        on sat.satcat_id = mem.satcat_id
    where mem.celestrak_group_kind = 'constellation'
)

, cte_manual_memberships as ( -- own payloads matched by a manual row's programme family or name
    select
        pay.satcat_id
        , rul.grouping_name as satellite_constellation_name
        , rul.definition_rule_type as constellation_source
        , rul.rule_value as constellation_rule_value
        , 1 as source_rank
        , 0 as order_in_source
    from cte_own_payloads as pay
    inner join cte_manual_rules as rul
        on (rul.definition_rule_type = 'gcat_program_family' and rul.rule_value = pay.satellite_program_family)
        or (rul.definition_rule_type = 'object_name_regex' and regexp_matches(pay.object_name, rul.rule_value))
)

, cte_all_memberships as (
    select
        satcat_id
        , satellite_constellation_name
        , constellation_source
        , constellation_rule_value
        , source_rank
        , order_in_source
    from cte_celestrak_memberships
    union all
    select
        satcat_id
        , satellite_constellation_name
        , constellation_source
        , constellation_rule_value
        , source_rank
        , order_in_source
    from cte_manual_memberships
)

, cte_ranked_memberships as ( -- CelesTrak first (config order), then manual rows (name order)
    select
        satcat_id
        , satellite_constellation_name
        , constellation_source
        , constellation_rule_value
        , row_number() over (
            partition by satcat_id
            order by source_rank, order_in_source, satellite_constellation_name
        ) as membership_rank
    from cte_all_memberships
)

, cte_final as (
    select
        cast(satcat_id as integer) as satcat_id
        , cast(satellite_constellation_name as varchar) as satellite_constellation_name
        , cast(constellation_source as varchar) as constellation_source
        , cast(constellation_rule_value as varchar) as constellation_rule_value
        , {{ helper__audit_fields() }}
    from cte_ranked_memberships
    where membership_rank = 1
)

select * from cte_final
