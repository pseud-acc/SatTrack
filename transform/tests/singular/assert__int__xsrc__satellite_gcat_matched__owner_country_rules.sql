-- Fails when an owner country set from the GCAT State is flagged as an organisation, when a TBD owner
-- with a resolvable State is still "Unknown", or when an organisation owner took the State instead of its Space-Track name.
with cte_int__xsrc__satellite_gcat_matched as (
    select
        canonical_satellite_id
        , spacetrack_country_code
        , owner_country
        , owner_country_is_org
        , owner_country_source
    from {{ ref('int__xsrc__satellite_gcat_matched') }}
)

select
    'owner_country_rules' as check_name
    , canonical_satellite_id
    , spacetrack_country_code
    , owner_country
    , owner_country_is_org
    , owner_country_source
from cte_int__xsrc__satellite_gcat_matched
where (owner_country_source in ('gcat_state', 'gcat_state_tbd') and owner_country_is_org)
   or (owner_country_source = 'gcat_state_tbd' and spacetrack_country_code <> 'TBD')
   or (owner_country_source = 'unknown' and spacetrack_country_code <> 'TBD')
   or (owner_country_is_org and owner_country_source <> 'spacetrack_name')
