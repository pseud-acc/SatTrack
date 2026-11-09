-- Fails when one launch tag carries more than one set of launch-level fields across its launch-log rows: the launch
-- key that rocket stages, components and debris inherit through must name exactly one launch.
with cte_int__jsr__launch_events as (
    select
        launch_tag
        , launch_datetime
        , launch_datetime_precision
        , site_code
        , lv_type
        , flight_id
        , launch_agency_code
        , launch_category
    from {{ ref('int__jsr__launch_events') }}
)

, cte_launch_variants as (
    select
        launch_tag
        , count(distinct (launch_datetime, launch_datetime_precision, site_code, lv_type, flight_id, launch_agency_code, launch_category)) as n_variants
    from cte_int__jsr__launch_events
    group by launch_tag
)

select
    'launch_tag_one_launch' as check_name
    , launch_tag
    , n_variants
from cte_launch_variants
where n_variants > 1 or launch_tag is null
