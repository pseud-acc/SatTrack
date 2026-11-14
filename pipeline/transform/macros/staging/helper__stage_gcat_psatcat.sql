{% macro helper__stage_gcat_psatcat(table) %}
with cte_final as (
    select
        {{ sattrack.helper__clean_gcat_text('JCAT') }} as jcat
        , {{ sattrack.helper__clean_gcat_text('Piece') }} as cospar_id
        , {{ sattrack.helper__clean_gcat_text('Name') }} as un_registry_name
        , {{ sattrack.helper__clean_gcat_text('LDate') }} as gcat_launch_date_raw
        , {{ sattrack.helper__clean_gcat_text('TLast') }} as last_active_date_raw
        , {{ sattrack.helper__clean_gcat_text('TOp') }} as end_operation_date_raw
        , {{ sattrack.helper__clean_gcat_text('TDate') }} as end_transmission_date_raw
        , {{ sattrack.helper__clean_gcat_text('TF') }} as end_of_life_code
        , {{ sattrack.helper__clean_gcat_text('Program') }} as satellite_program
        , {{ sattrack.helper__clean_gcat_text('Plane') }} as constellation_plane
        , {{ sattrack.helper__clean_gcat_text('Att') }} as attitude_control
        , {{ sattrack.helper__clean_gcat_text('Mvr') }} as maneuverability
        , {{ sattrack.helper__clean_gcat_text('Class') }} as ownership_class
        , {{ sattrack.helper__clean_gcat_text('Category') }} as mission_category
        , {{ sattrack.helper__clean_gcat_text('Result') }} as mission_result
        , {{ sattrack.helper__clean_gcat_text('Control') }} as control_centre
        , {{ sattrack.helper__clean_gcat_text('Discipline') }} as science_discipline
        , {{ sattrack.helper__clean_gcat_text('UNState') }} as un_state
        , {{ sattrack.helper__clean_gcat_text('UNReg') }} as un_reg_doc
        , {{ sattrack.helper__cast_gcat_value('UNPeriod', 'double') }} as un_period_min
        , {{ sattrack.helper__cast_gcat_value('UNPerigee', 'double') }} as un_perigee_km
        , {{ sattrack.helper__cast_gcat_value('UNApogee', 'double') }} as un_apogee_km
        , {{ sattrack.helper__cast_gcat_value('UNInc', 'double') }} as un_inclination_deg
        , {{ sattrack.helper__clean_gcat_text('DispEpoch') }} as disposal_epoch_raw
        , {{ sattrack.helper__cast_gcat_value('DispPeri', 'double') }} as disposal_perigee_km
        , {{ sattrack.helper__cast_gcat_value('DispApo', 'double') }} as disposal_apogee_km
        , {{ sattrack.helper__cast_gcat_value('DispInc', 'double') }} as disposal_inclination_deg
        , {{ sattrack.helper__clean_gcat_text('Comment') }} as gcat_comment
        , cast(_loaded_at as timestamp) as _loaded_at
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , cast(_source_row_number as integer) as _source_row_number
        , _source_file
        , _run_id
    from {{ source('jsr', table) }}
)

select * from cte_final
{% endmacro %}
