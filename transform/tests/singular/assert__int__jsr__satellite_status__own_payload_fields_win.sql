-- Fails when inherited payload fields appear on an object with its own payload record or its own mission category,
-- on a payload (only GCAT Type R / C / D objects inherit), or from a payload other than the Parent chain's.
with cte_int__jsr__satellite_status as (
    select
        jcat
        , flag_has_psatcat_record
        , mission_category
        , payload_fields_source
        , payload_fields_parent_jcat
    from {{ ref('int__jsr__satellite_status') }}
)

, cte_int__jsr__satellite_parent_payload as (
    select
        jcat
        , sat_type_class
        , parent_payload_jcat
    from {{ ref('int__jsr__satellite_parent_payload') }}
)

select
    'own_payload_fields_win' as check_name
    , st.jcat
    , st.payload_fields_source
    , st.payload_fields_parent_jcat
    , chain.sat_type_class
from cte_int__jsr__satellite_status as st
left join cte_int__jsr__satellite_parent_payload as chain on chain.jcat = st.jcat
where (st.payload_fields_source = 'inherited_parent'
       and (st.flag_has_psatcat_record = 1
            or st.mission_category is not null
            or coalesce(chain.sat_type_class, '') not in ('R', 'C', 'D')
            or st.payload_fields_parent_jcat is distinct from chain.parent_payload_jcat))
   or (st.payload_fields_source = 'own' and st.flag_has_psatcat_record = 0)
   or (st.payload_fields_source <> 'inherited_parent' and st.payload_fields_parent_jcat is not null)
