-- Fails (D-053): a rocket body or debris object marked Active. Rocket bodies and debris (Space-Track's object type)
-- are always Inactive, whatever GCAT's current-catalog type says.
with cte_fct__satellite_master as (
    select
        satcat_id
        , object_name
        , object_type
        , operational_status
    from {{ ref('fct__satellite_master') }}
)

select
    satcat_id
    , object_name
    , object_type
    , operational_status
from cte_fct__satellite_master
where object_type in ('ROCKET BODY', 'DEBRIS')
    and operational_status = 'Active'
