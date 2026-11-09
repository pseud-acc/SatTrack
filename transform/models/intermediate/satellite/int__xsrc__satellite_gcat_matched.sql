-- One row per object in the Space-Track GP feed, linked to its GCAT JCAT with the GCAT catalogue fields the master needs.
-- GCAT: "Sequence numbers in the S catalog are in one-to-one correspondence with the US SATCAT catalog numbers",
-- so link by 'S' + lpad(NORAD, 5) first, then by a COSPAR ID that identifies one GCAT object (decided 2026-10-25).
-- Owner country: the Space-Track country code resolved through int__xsrc__geo_owner_country, with two GCAT State rules:
--   CIS  -> the country of the GCAT State when the State is SU or RU; the split rows are countries, not organisations (decided 2026-10-25);
--   TBD  -> the country of the GCAT State when it resolves (decided 2026-11-08).
-- The State country is resolved by int__xsrc__geo_state_country, so the labels are the ISO names (Russian Federation; USSR for the former country).
-- Every other owner, organisations included, keeps the Space-Track result.
with cte_int__spacetrack__satellite_catalogue as (
    select
        satcat_id
        , object_name
        , object_id
        , object_type
        , country_code
        , launch_date
        , orbit_class
        , orbital_period
        , inclination
        , eccentricity
        , apoapsis
        , periapsis
        , rcs_size
        , epoch
        , tle_age_days
        , tle_line_1
        , tle_line_2
        , _loaded_at
    from {{ ref('int__spacetrack__satellite_catalogue') }}
)

, cte_int__jsr__satellite_catalogue as (
    select
        jcat
        , cospar_id
        , sat_type_class
        , gcat_launch_date
        , state_code
        , owner_code
        , orbit_regime
        , mass_kg
        , flag_mass_estimated
        , dry_mass_kg
        , span_m
        , _source_updated_at
    from {{ ref('int__jsr__satellite_catalogue') }}
)

, cte_int__xsrc__geo_owner_country as (
    select
        country_code
        , owner_country
        , owner_country_codes
        , owner_country_is_org
        , owner_country_method
    from {{ ref('int__xsrc__geo_owner_country') }}
)

, cte_int__xsrc__geo_state_country as (
    select
        state_code
        , owner_country
        , owner_country_codes
    from {{ ref('int__xsrc__geo_state_country') }}
)

, cte_links_by_norad as (
    -- NB: DuckDB lpad() truncates longer strings (lpad('100001', 5, '0') = '10000'), so numbers >= 100,000
    -- are used unpadded (GCAT: S100001). Caught by unique__int__xsrc__satellite_gcat_matched__jcat.
    select
        gp.satcat_id
        , cat.jcat
        , 's_norad' as jcat_link_method
    from cte_int__spacetrack__satellite_catalogue as gp
    join cte_int__jsr__satellite_catalogue as cat
        on cat.jcat = 'S' || case when gp.satcat_id < 100000 then lpad(cast(gp.satcat_id as varchar), 5, '0')
                                  else cast(gp.satcat_id as varchar) end
)

, cte_unique_cospar_pieces as ( -- COSPAR IDs that identify exactly one GCAT object
    select
        jcat
        , cospar_id
    from cte_int__jsr__satellite_catalogue
    qualify count(*) over (partition by cospar_id) = 1
)

, cte_links_by_cospar as (
    select
        gp.satcat_id
        , u.jcat
        , 'cospar' as jcat_link_method
    from cte_int__spacetrack__satellite_catalogue as gp
    join cte_unique_cospar_pieces as u on u.cospar_id = gp.object_id
    where gp.satcat_id not in (select satcat_id from cte_links_by_norad)
      and u.jcat not in (select jcat from cte_links_by_norad)
)

, cte_jcat_links as (
    select
        satcat_id
        , jcat
        , jcat_link_method
    from cte_links_by_norad
    union all
    select
        satcat_id
        , jcat
        , jcat_link_method
    from cte_links_by_cospar
)

, cte_final as (
    select
        gp.satcat_id
        , cast(gp.satcat_id as varchar) as canonical_satellite_id
        , link.jcat
        , coalesce(link.jcat_link_method, 'none') as jcat_link_method
        , link.jcat is not null as flag_gcat_matched
        , gp.object_name
        , gp.object_id
        -- object type: GP, falling back to GCAT Type[0] when GP says UNKNOWN
        , case
            when gp.object_type <> 'UNKNOWN' then gp.object_type
            when cat.sat_type_class = 'P' then 'PAYLOAD'
            when cat.sat_type_class = 'R' then 'ROCKET BODY'
            when cat.sat_type_class in ('C', 'D') then 'DEBRIS'
            else gp.object_type
        end as object_type
        , case when gp.object_type <> 'UNKNOWN' or cat.sat_type_class is null then 'spacetrack' else 'gcat' end as object_type_source
        , gp.object_type as spacetrack_object_type
        , cat.sat_type_class
        -- in orbit: every object in the GP feed is on orbit
        , true as flag_in_orbit
        , gp.country_code as spacetrack_country_code
        -- owner country rule, then the owner fields that follow it (aliases read by the lines below)
        , case
            when gp.country_code = 'CIS' and cat.state_code in ('SU', 'RU') and gst.state_code is not null then 'gcat_state'
            when gp.country_code = 'TBD' and gst.state_code is not null then 'gcat_state_tbd'
            when geo.country_code is not null then geo.owner_country_method
            else 'none'
        end as owner_country_source
        , case owner_country_source
            when 'gcat_state' then gst.owner_country
            when 'gcat_state_tbd' then gst.owner_country
            else geo.owner_country
        end as owner_country
        , case owner_country_source
            when 'gcat_state' then gst.owner_country_codes
            when 'gcat_state_tbd' then gst.owner_country_codes
            else coalesce(geo.owner_country_codes, cast([] as varchar[]))
        end as owner_country_codes
        , case
            when owner_country_source in ('gcat_state', 'gcat_state_tbd') then false
            else coalesce(geo.owner_country_is_org, false)
        end as owner_country_is_org
        -- launch date: GP, falling back to GCAT LDate
        , coalesce(gp.launch_date, cast(cat.gcat_launch_date as date)) as launch_date
        , case
            when gp.launch_date is not null then 'spacetrack'
            when cat.gcat_launch_date is not null then 'gcat'
            else 'none'
        end as launch_date_source
        , year(coalesce(gp.launch_date, cast(cat.gcat_launch_date as date))) as launch_year
        , gp.launch_date as spacetrack_launch_date
        , cat.gcat_launch_date
        , gp.orbit_class
        , gp.orbital_period
        , gp.inclination
        , gp.eccentricity
        , gp.apoapsis
        , gp.periapsis
        , gp.rcs_size
        , gp.epoch
        , gp.tle_age_days
        , gp.tle_line_1
        , gp.tle_line_2
        , gp._loaded_at as positions_as_of
        , cat.state_code
        , cat.owner_code
        , cat.orbit_regime
        , cat.mass_kg
        , cat.flag_mass_estimated
        , cat.dry_mass_kg
        , cat.span_m
        , cat._source_updated_at as details_as_of
        , {{ helper__audit_fields() }}
    from cte_int__spacetrack__satellite_catalogue as gp
    left join cte_jcat_links as link using (satcat_id)
    left join cte_int__jsr__satellite_catalogue as cat on cat.jcat = link.jcat
    left join cte_int__xsrc__geo_owner_country as geo on geo.country_code = gp.country_code
    left join cte_int__xsrc__geo_state_country as gst on gst.state_code = cat.state_code
)

select * from cte_final
