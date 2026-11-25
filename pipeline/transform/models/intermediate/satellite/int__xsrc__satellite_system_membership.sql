-- One row per object in the GP feed and satellite system it belongs to (D-047): non-identical satellites working
-- together; a satellite can belong to several. CelesTrak says a system exists; GCAT completes its membership.
-- Deterministic rules:
--   1. system groups (kind system: gps-ops, glo-ops, galileo, beidou, tdrss, dmc), named by CelesTrak's title. A
--      member counts only when its name fits the group (flag_name_fits_group: drops the TDRSS users in tdrss, HJ-1A/1B
--      and YAOGAN-4 in dmc). GCAT then adds every payload with its own payload record that shares a programme family
--      with a kept member (retired GPS satellites, BEIJING 1 and DEIMOS 1 in DMC, ...). Primary.
--   2. manual systems from the ad-hoc seed manual_satellite_grouping (kind system), on own payloads by programme
--      family or name: primary ones (NavIC, QZSS, JPSS, GOES, Copernicus Sentinels) and hosted ones by name (MSAS on
--      QZS-3/6/7). CelesTrak's gnss group is not used: "GNSS" is the umbrella term for every navigation system.
--   3. hosted groups (kind system_hosted: sarsat), named by CelesTrak's title. Hosted.
--   4. hosted umbrella groups (kind system_hosted_umbrella: sbas). "SBAS" is an umbrella term, never a system: each
--      member's system is the token CelesTrak writes before "/PRN" in its name (EGNOS, WAAS, GAGAN, SDCM, SOUTHPAN, ...);
--      a manual row can name members by PRN instead (BDSBAS: PRN 130, 143, 144, from GPS.gov's PRN register). Hosted.
-- A system reached both ways keeps one row, primary. Debris and stages inherit their parent's programme, so the GCAT
-- steps never add them; hosted groups are never completed from GCAT (their members belong to many programmes).
with cte_int__celestrak__satellite_group_membership as (
    select
        satcat_id
        , celestrak_group_kind
        , grouping_name
        , member_system_token
        , member_prn
        , flag_name_fits_group
    from {{ ref('int__celestrak__satellite_group_membership') }}
)

, cte_stg__sattrack__manual_satellite_grouping as (
    select
        grouping_kind
        , grouping_name
        , definition_rule_type
        , definition_rule_values
        , flag_hosted_system
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

, cte_kept_system_members as ( -- step 1 exclusion: system group members whose names fit the group
    select
        satcat_id
        , grouping_name as satellite_system_name
    from cte_int__celestrak__satellite_group_membership
    where celestrak_group_kind = 'system'
        and flag_name_fits_group = 1
)

, cte_manual_rules as ( -- one row per manual system and rule value (`|`-separated; a pattern stays whole)
    select
        grouping_name as satellite_system_name
        , definition_rule_type
        , unnest(
            case
                when definition_rule_type = 'object_name_regex' then [definition_rule_values]  -- a pattern is one value
                else string_split(definition_rule_values, '|')
            end
        ) as rule_value
        , flag_hosted_system
    from cte_stg__sattrack__manual_satellite_grouping
    where grouping_kind = 'system'
)

, cte_system_families as ( -- step 1: the programme families of the kept members
    select distinct
        mem.satellite_system_name
        , pay.satellite_program_family
    from cte_kept_system_members as mem
    inner join cte_own_payloads as pay
        on pay.satcat_id = mem.satcat_id
    where pay.satellite_program_family is not null
)

, cte_payload_rules as ( -- every rule matched on own payloads (steps 1 and 2)
    select
        satellite_system_name
        , 'gcat_program_family' as rule_type
        , satellite_program_family as rule_value
        , 'celestrak_system_group' as system_source
        , 1 as flag_primary_system
    from cte_system_families
    union all
    select
        satellite_system_name
        , definition_rule_type as rule_type
        , rule_value
        , 'manual' as system_source
        , 1 - flag_hosted_system as flag_primary_system
    from cte_manual_rules
    where definition_rule_type in ('gcat_program_family', 'object_name_regex')
)

, cte_payload_memberships as ( -- steps 1-2: own payloads matched by family or name
    select
        pay.satcat_id
        , rul.satellite_system_name
        , rul.system_source
        , rul.flag_primary_system
    from cte_own_payloads as pay
    inner join cte_payload_rules as rul
        on (rul.rule_type = 'gcat_program_family' and rul.rule_value = pay.satellite_program_family)
        or (rul.rule_type = 'object_name_regex' and regexp_matches(pay.object_name, rul.rule_value))
)

, cte_kept_members_in_feed as ( -- step 1 members themselves (e.g. one GCAT hasn't catalogued yet)
    select
        mem.satcat_id
        , mem.satellite_system_name
        , 'celestrak_system_group' as system_source
        , 1 as flag_primary_system
    from cte_kept_system_members as mem
    inner join cte_int__xsrc__satellite_gcat_matched as sat
        on sat.satcat_id = mem.satcat_id
)

, cte_hosted_members_in_feed as ( -- steps 3-4: hosted group members in the GP feed
    select
        mem.satcat_id
        , mem.celestrak_group_kind
        , mem.grouping_name
        , mem.member_system_token
        , mem.member_prn
    from cte_int__celestrak__satellite_group_membership as mem
    inner join cte_int__xsrc__satellite_gcat_matched as sat
        on sat.satcat_id = mem.satcat_id
    where mem.celestrak_group_kind in ('system_hosted', 'system_hosted_umbrella')
)

, cte_hosted_named_memberships as ( -- step 3 by group title, step 4 by the name's system token
    select
        satcat_id
        , case
            when celestrak_group_kind = 'system_hosted' then grouping_name
            else member_system_token
        end as satellite_system_name
        , case
            when celestrak_group_kind = 'system_hosted' then 'celestrak_hosted_group'
            else 'celestrak_member_name'
        end as system_source
        , 0 as flag_primary_system
    from cte_hosted_members_in_feed
    where celestrak_group_kind = 'system_hosted'
        or member_system_token is not null
)

, cte_hosted_prn_memberships as ( -- step 4 by PRN, for manual rows (BDSBAS)
    select
        mem.satcat_id
        , rul.satellite_system_name
        , 'manual' as system_source
        , 0 as flag_primary_system
    from cte_hosted_members_in_feed as mem
    inner join cte_manual_rules as rul
        on rul.definition_rule_type = 'celestrak_member_prn'
        and rul.rule_value = mem.member_prn
    where mem.celestrak_group_kind = 'system_hosted_umbrella'
)

, cte_all_memberships as (
    select
        satcat_id
        , satellite_system_name
        , system_source
        , flag_primary_system
    from cte_payload_memberships
    union all
    select
        satcat_id
        , satellite_system_name
        , system_source
        , flag_primary_system
    from cte_kept_members_in_feed
    union all
    select
        satcat_id
        , satellite_system_name
        , system_source
        , flag_primary_system
    from cte_hosted_named_memberships
    union all
    select
        satcat_id
        , satellite_system_name
        , system_source
        , flag_primary_system
    from cte_hosted_prn_memberships
)

, cte_memberships as ( -- one row per object and system; primary wins when reached both ways
    select
        satcat_id
        , satellite_system_name
        , max(flag_primary_system) as flag_primary_system
        , arg_max(system_source, flag_primary_system) as system_source
    from cte_all_memberships
    group by
        satcat_id
        , satellite_system_name
)

, cte_final as (
    select
        cast(satcat_id as integer) as satcat_id
        , cast(satellite_system_name as varchar) as satellite_system_name
        , cast(flag_primary_system as integer) as flag_primary_system
        , cast(system_source as varchar) as system_source
        , {{ helper__audit_fields() }}
    from cte_memberships
)

select * from cte_final
