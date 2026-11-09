-- Fails when inherited launch fields appear on an object that has its own launch-log row, or when an object
-- marked 'own' does not show its own row's values (an object's own value always wins).
with cte_int__jsr__satellite_launch_details as (
    select
        jcat
        , launch_tag
        , site_code
        , lv_type
        , launch_agency_code
        , launch_fields_source
    from {{ ref('int__jsr__satellite_launch_details') }}
)

, cte_int__jsr__launch_events as (
    select
        jcat
        , launch_tag
        , site_code
        , lv_type
        , launch_agency_code
    from {{ ref('int__jsr__launch_events') }}
)

select
    'own_launch_wins' as check_name
    , ld.jcat
    , ld.launch_fields_source
    , ld.launch_tag
    , own.launch_tag as own_launch_tag
from cte_int__jsr__satellite_launch_details as ld
left join cte_int__jsr__launch_events as own on own.jcat = ld.jcat
where (ld.launch_fields_source = 'inherited_launch' and own.jcat is not null)
   or (ld.launch_fields_source = 'own' and own.jcat is null)
   or (ld.launch_fields_source = 'own' and (ld.launch_tag is distinct from own.launch_tag
                                            or ld.site_code is distinct from own.site_code
                                            or ld.lv_type is distinct from own.lv_type
                                            or ld.launch_agency_code is distinct from own.launch_agency_code))
