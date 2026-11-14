-- One row per GCAT object (satcat + satcat100k), vague dates parsed, undocumented codes nulled.
-- Undocumented values become NULL here; raw values stay in staging (decided 2026-10-25).
with cte_stg__jsr__satcat as (
    select
        jcat
        , satcat_ref
        , launch_tag
        , cospar_id
        , sat_type
        , gcat_name
        , pre_launch_name
        , gcat_launch_date_raw
        , parent_ref
        , phase_end_date_raw
        , phase_status
        , owner_code
        , owner_state_code
        , manufacturer_code
        , bus
        , mass_kg
        , mass_flag
        , dry_mass_kg
        , length_m
        , diameter_m
        , span_m
        , shape
        , orbit_type_raw
        , _source_file
        , _source_row_number
        , _source_updated_at
    from {{ ref('stg__jsr__satcat') }}
)

, cte_stg__jsr__satcat100k as (
    select
        jcat
        , satcat_ref
        , launch_tag
        , cospar_id
        , sat_type
        , gcat_name
        , pre_launch_name
        , gcat_launch_date_raw
        , parent_ref
        , phase_end_date_raw
        , phase_status
        , owner_code
        , owner_state_code
        , manufacturer_code
        , bus
        , mass_kg
        , mass_flag
        , dry_mass_kg
        , length_m
        , diameter_m
        , span_m
        , shape
        , orbit_type_raw
        , _source_file
        , _source_row_number
        , _source_updated_at
    from {{ ref('stg__jsr__satcat100k') }}
)

, cte_gcat_objects as ( -- both catalog files, every row (deduplicated where read)
    select
        jcat
        , satcat_ref
        , launch_tag
        , cospar_id
        , sat_type
        , gcat_name
        , pre_launch_name
        , gcat_launch_date_raw
        , parent_ref
        , phase_end_date_raw
        , phase_status
        , owner_code
        , owner_state_code
        , manufacturer_code
        , bus
        , mass_kg
        , mass_flag
        , dry_mass_kg
        , length_m
        , diameter_m
        , span_m
        , shape
        , orbit_type_raw
        , _source_file
        , _source_row_number
        , _source_updated_at
    from cte_stg__jsr__satcat
    union all by name
    select
        jcat
        , satcat_ref
        , launch_tag
        , cospar_id
        , sat_type
        , gcat_name
        , pre_launch_name
        , gcat_launch_date_raw
        , parent_ref
        , phase_end_date_raw
        , phase_status
        , owner_code
        , owner_state_code
        , manufacturer_code
        , bus
        , mass_kg
        , mass_flag
        , dry_mass_kg
        , length_m
        , diameter_m
        , span_m
        , shape
        , orbit_type_raw
        , _source_file
        , _source_row_number
        , _source_updated_at
    from cte_stg__jsr__satcat100k
)

, cte_final as (
    select
        jcat
        , satcat_ref
        , launch_tag
        , cospar_id
        , sat_type
        , case when left(sat_type, 1) in ('P', 'R', 'C', 'D') then left(sat_type, 1) end as sat_type_class
        , gcat_name
        , pre_launch_name
        , {{ helper__parse_vague_date_columns('gcat_launch_date_raw', 'gcat_launch_date') }}
        , parent_ref
        , {{ helper__parse_vague_date_columns('phase_end_date_raw', 'phase_end_date') }}
        , case when phase_status in ('O', 'AO', 'AO IN', 'UDK', 'REL', 'DEP', 'TO', 'TOA', 'OX', 'E', 'N', 'NA', 'LEASE',
                                   'S', 'R', 'D', 'L', 'LF', 'AS', 'AR', 'AR IN', 'AL', 'AL IN', 'TX', 'F', 'AF', 'DSO',
                                   'DSA', 'DSA IN', 'LO', 'LOA', 'DK', 'GRP', 'ATT', 'TFR', 'TFR E', 'TFR IN', 'C',
                                   'EVA DP', 'EVA RP', 'REFLT', 'EO', 'EAO', 'EN', 'OI', 'OE', 'ERR')
             then phase_status end as phase_status
        , owner_code
        , owner_state_code
        , manufacturer_code
        , bus
        , mass_kg
        , cast(coalesce(mass_flag = '?', false) as integer) as flag_mass_estimated
        , dry_mass_kg
        , length_m
        , diameter_m
        , span_m
        , shape
        , orbit_type_raw
        , nullif(split_part(orbit_type_raw, '/', 1), '') as orbit_regime
        , nullif(split_part(orbit_type_raw, '/', 2), '') as orbit_subtype
        , _source_file
        , _source_updated_at
        , {{ helper__audit_fields() }}
    from cte_gcat_objects
    -- the first occurrence of a JCAT across both files wins (applies to the combined rows)
    qualify row_number() over (partition by jcat order by _source_file, _source_row_number) = 1
)

select * from cte_final
