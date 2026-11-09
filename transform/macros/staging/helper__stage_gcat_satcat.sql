{% macro helper__stage_gcat_satcat(table) %}
with cte_final as (
    select
        {{ sattrack.helper__clean_gcat_text('JCAT') }} as jcat
        , {{ sattrack.helper__clean_gcat_text('Satcat') }} as satcat_ref
        , {{ sattrack.helper__clean_gcat_text('Launch_Tag') }} as launch_tag
        , {{ sattrack.helper__clean_gcat_text('Piece') }} as cospar_id
        , {{ sattrack.helper__clean_gcat_text('Type') }} as sat_type
        , {{ sattrack.helper__clean_gcat_text('Name') }} as gcat_name
        , {{ sattrack.helper__clean_gcat_text('PLName') }} as pre_launch_name
        , {{ sattrack.helper__clean_gcat_text('LDate') }} as gcat_launch_date_raw
        , {{ sattrack.helper__clean_gcat_text('Parent') }} as parent_ref
        , {{ sattrack.helper__clean_gcat_text('SDate') }} as phase_start_date_raw
        , {{ sattrack.helper__clean_gcat_text('Primary') }} as central_body
        , {{ sattrack.helper__clean_gcat_text('DDate') }} as phase_end_date_raw
        , {{ sattrack.helper__clean_gcat_text('Status') }} as phase_status
        , {{ sattrack.helper__clean_gcat_text('Dest') }} as phase_destination
        , {{ sattrack.helper__clean_gcat_text('Owner') }} as owner_code
        , {{ sattrack.helper__clean_gcat_text('State') }} as state_code
        , {{ sattrack.helper__clean_gcat_text('Manufacturer') }} as manufacturer_code
        , {{ sattrack.helper__clean_gcat_text('Bus') }} as bus
        , {{ sattrack.helper__clean_gcat_text('Motor') }} as motor
        , {{ sattrack.helper__cast_gcat_value('Mass', 'double') }} as mass_kg
        , {{ sattrack.helper__clean_gcat_text('MassFlag') }} as mass_flag
        , {{ sattrack.helper__cast_gcat_value('DryMass', 'double') }} as dry_mass_kg
        , {{ sattrack.helper__clean_gcat_text('DryFlag') }} as dry_mass_flag
        , {{ sattrack.helper__cast_gcat_value('TotMass', 'double') }} as total_mass_kg
        , {{ sattrack.helper__clean_gcat_text('TotFlag') }} as total_mass_flag
        , {{ sattrack.helper__cast_gcat_value('Length', 'double') }} as length_m
        , {{ sattrack.helper__clean_gcat_text('LFlag') }} as length_flag
        , {{ sattrack.helper__cast_gcat_value('Diameter', 'double') }} as diameter_m
        , {{ sattrack.helper__clean_gcat_text('DFlag') }} as diameter_flag
        , {{ sattrack.helper__cast_gcat_value('Span', 'double') }} as span_m
        , {{ sattrack.helper__clean_gcat_text('SpanFlag') }} as span_flag
        , {{ sattrack.helper__clean_gcat_text('Shape') }} as shape
        , {{ sattrack.helper__clean_gcat_text('ODate') }} as canonical_orbit_epoch_raw
        , {{ sattrack.helper__cast_gcat_value('Perigee', 'double') }} as canonical_perigee_km
        , {{ sattrack.helper__clean_gcat_text('PF') }} as canonical_perigee_flag
        , {{ sattrack.helper__cast_gcat_value('Apogee', 'double') }} as canonical_apogee_km
        , {{ sattrack.helper__clean_gcat_text('AF') }} as canonical_apogee_flag
        , {{ sattrack.helper__cast_gcat_value('Inc', 'double') }} as canonical_inclination_deg
        , {{ sattrack.helper__clean_gcat_text('IF') }} as canonical_inclination_flag
        , {{ sattrack.helper__clean_gcat_text('OpOrbit') }} as orbit_type_raw
        , {{ sattrack.helper__clean_gcat_text('OQUAL') }} as orbit_quality_note
        , {{ sattrack.helper__clean_gcat_text('AltNames') }} as alt_names
        , cast(_loaded_at as timestamp) as _loaded_at
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , cast(_source_row_number as integer) as _source_row_number
        , _source_file
        , _run_id
    from {{ source('jsr', table) }}
)

select * from cte_final
{% endmacro %}
