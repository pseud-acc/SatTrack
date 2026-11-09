-- One row per GCAT object in the Current Catalog or the payload catalogs: operating / transmitting primitives (D9),
-- current-catalog activity, and the GCAT activity signal used by the status rule (decided 2026-10-25):
-- gcat_active = (TOp = '*' OR currentcat Active = 'A') AND TF <> 'Z' (zombie = Inactive), set for payload rows only.
-- Ownership class and mission category codes get GCAT's rule-derived short labels; unlabelled codes show raw.
-- Rocket stages, components and debris without a payload record take the mission category and programme of the payload
-- their GCAT Parent chain leads to (int__jsr__satellite_parent_payload); an object's own payload record always wins.
-- satellite_program_family (leading letters of the programme) follows the programme; constellation_plane is always the object's own.
with cte_stg__jsr__psatcat as (
    select
        jcat
        , end_operation_date_raw
        , end_transmission_date_raw
        , last_active_date_raw
        , end_of_life_flag
        , maneuverability
        , ownership_class
        , mission_category
        , satellite_program
        , constellation_plane
        , _source_file
        , _source_row_number
        , _source_updated_at
    from {{ ref('stg__jsr__psatcat') }}
)

, cte_stg__jsr__psatcat100k as (
    select
        jcat
        , end_operation_date_raw
        , end_transmission_date_raw
        , last_active_date_raw
        , end_of_life_flag
        , maneuverability
        , ownership_class
        , mission_category
        , satellite_program
        , constellation_plane
        , _source_file
        , _source_row_number
        , _source_updated_at
    from {{ ref('stg__jsr__psatcat100k') }}
)

, cte_int__jsr__satellite_current as (
    select
        jcat
        , activity_type
        , current_status
        , flag_gcat_in_orbit
    from {{ ref('int__jsr__satellite_current') }}
)

, cte_int__jsr__satellite_parent_payload as (
    select
        jcat
        , parent_payload_jcat
    from {{ ref('int__jsr__satellite_parent_payload') }}
)

, cte_stg__jsr__gcat_code_labels as (
    select
        label_domain
        , gcat_code
        , short_label
    from {{ ref('stg__jsr__gcat_code_labels') }}
)

, cte_gcat_payloads as ( -- both payload files, every row (deduplicated where read)
    select
        jcat
        , end_operation_date_raw
        , end_transmission_date_raw
        , last_active_date_raw
        , end_of_life_flag
        , maneuverability
        , ownership_class
        , mission_category
        , satellite_program
        , constellation_plane
        , _source_file
        , _source_row_number
        , _source_updated_at
    from cte_stg__jsr__psatcat
    union all by name
    select
        jcat
        , end_operation_date_raw
        , end_transmission_date_raw
        , last_active_date_raw
        , end_of_life_flag
        , maneuverability
        , ownership_class
        , mission_category
        , satellite_program
        , constellation_plane
        , _source_file
        , _source_row_number
        , _source_updated_at
    from cte_stg__jsr__psatcat100k
)

, cte_gcat_label_maps as ( -- one row: code -> short label lookups (DuckDB allows no subqueries inside lambdas)
    select
        map_from_entries(list({'k': gcat_code, 'v': short_label}) filter (where label_domain = 'mission_category')) as mission_map
        , map_from_entries(list({'k': gcat_code, 'v': short_label}) filter (where label_domain = 'ownership_class')) as class_map
    from cte_stg__jsr__gcat_code_labels
)

, cte_payload_status as ( -- payload primitives, documented codes only
    select
        jcat
        , end_operation_date_raw
        , end_transmission_date_raw
        , last_active_date_raw
        , case when end_of_life_flag in ('D', 'E', 'U', 'X', 'Z') then end_of_life_flag end as end_of_life_flag
        , case when maneuverability in ('M', 'D') then maneuverability end as maneuverability
        , case when regexp_full_match(ownership_class, '[ABCD]{1,2}') then ownership_class end as ownership_class
        , mission_category
        , list_filter(string_split(regexp_replace(coalesce(mission_category, ''), '[?*]', '', 'g'), '/'), lambda x: x <> '') as mission_category_list
        , satellite_program
        -- family = the leading run of letters of the GCAT programme name ('Starlink 2MO S1' -> 'Starlink'); NULL when none
        , nullif(regexp_extract(satellite_program, '^[A-Za-z]+'), '') as satellite_program_family
        , constellation_plane
        , _source_file
        , _source_updated_at
    from cte_gcat_payloads
    -- the first occurrence of a JCAT across both files wins (applies to the combined rows)
    qualify row_number() over (partition by jcat order by _source_file, _source_row_number) = 1
)

, cte_gcat_object_status as ( -- payload and current-catalog primitives per JCAT
    select
        coalesce(p.jcat, c.jcat) as jcat
        , p.jcat is not null as has_psatcat_record
        , c.jcat is not null as has_currentcat_record
        , p.end_operation_date_raw = '*' as flag_still_operating
        , p.end_transmission_date_raw = '*' as flag_still_transmitting
        , {{ helper__parse_vague_date_columns('p.end_operation_date_raw', 'end_operation_date') }}
        , {{ helper__parse_vague_date_columns('p.end_transmission_date_raw', 'end_transmission_date') }}
        -- GCAT: TLast '*' means "no information" (TOp / TDate '*' mean "still operating / transmitting"), so it has no date
        , cast({{ helper__parse_vague_date_base('p.last_active_date_raw') }} as timestamp) as last_active_date
        , cast({{ helper__parse_vague_date_start('p.last_active_date_raw') }} as timestamp) as last_active_date_start
        , cast({{ helper__parse_vague_date_end('p.last_active_date_raw') }} as timestamp) as last_active_date_end
        , case
            when p.last_active_date_raw = '*' then 'no_information'
            else {{ helper__parse_vague_date_precision('p.last_active_date_raw') }}
        end as last_active_date_precision
        , p.end_of_life_flag
        , p.maneuverability
        , p.ownership_class
        , list_transform(list_filter(string_split(coalesce(p.ownership_class, ''), ''), lambda x: x <> ''),
            lambda x: coalesce(map_extract_value(labels.class_map, x), x)) as ownership_class_labels
        , p.mission_category
        , p.mission_category_list
        , list_transform(p.mission_category_list,
            lambda x: coalesce(map_extract_value(labels.mission_map, x), x)) as mission_category_labels
        , coalesce(p.mission_category like '%?%', false) as flag_category_uncertain
        , coalesce(p.mission_category like '%*%', false) as flag_orbit_data_secret
        , p.satellite_program
        , p.satellite_program_family
        , p.constellation_plane
        , c.activity_type
        , c.current_status
        , c.flag_gcat_in_orbit
        -- GCAT says the object came down (currentcat DDate set); NULL when it isn't in the Current Catalog
        , not c.flag_gcat_in_orbit as flag_gcat_descended
        , case when p.jcat is not null then
            ((p.end_operation_date_raw = '*') or coalesce(c.activity_type = 'A', false))
                and coalesce(p.end_of_life_flag, '') <> 'Z'
        end as gcat_active
        , p._source_file
        , p._source_updated_at
    from cte_payload_status as p
    full outer join cte_int__jsr__satellite_current as c on c.jcat = p.jcat
    cross join cte_gcat_label_maps as labels
)

, cte_payload_field_inheritance as ( -- own payload record, else the parent payload's record (payload-level fields only)
    select
        obj.jcat
        , case when obj.has_psatcat_record then obj.mission_category_list else parent.mission_category_list end as mission_category_list
        , case when obj.has_psatcat_record then obj.mission_category_labels else parent.mission_category_labels end as mission_category_labels
        , case when obj.has_psatcat_record then obj.satellite_program else parent.satellite_program end as satellite_program
        , case when obj.has_psatcat_record then obj.satellite_program_family else parent.satellite_program_family end as satellite_program_family
        , case
            when obj.has_psatcat_record then 'own'
            when parent.jcat is not null then 'inherited_parent'
            else 'none'
        end as payload_fields_source
        , case when not obj.has_psatcat_record then parent.jcat end as payload_fields_parent_jcat
    from cte_gcat_object_status as obj
    left join cte_int__jsr__satellite_parent_payload as chain on chain.jcat = obj.jcat
    left join cte_gcat_object_status as parent
        on parent.jcat = chain.parent_payload_jcat
        and parent.has_psatcat_record
)

, cte_final as (
    select
        jcat
        , has_psatcat_record
        , has_currentcat_record
        , flag_still_operating
        , flag_still_transmitting
        , end_operation_date
        , end_operation_date_start
        , end_operation_date_end
        , end_operation_date_precision
        , end_transmission_date
        , end_transmission_date_start
        , end_transmission_date_end
        , end_transmission_date_precision
        , last_active_date
        , last_active_date_start
        , last_active_date_end
        , last_active_date_precision
        , end_of_life_flag
        , maneuverability
        , ownership_class
        , ownership_class_labels
        , obj.mission_category
        , inherit.mission_category_list
        , inherit.mission_category_labels
        , flag_category_uncertain
        , flag_orbit_data_secret
        , inherit.satellite_program
        , inherit.satellite_program_family
        , obj.constellation_plane
        , inherit.payload_fields_source
        , inherit.payload_fields_parent_jcat
        , activity_type
        , current_status
        , flag_gcat_in_orbit
        , flag_gcat_descended
        , gcat_active
        -- status: Active / Inactive from GCAT only (decided 2026-10-25): the payload rule, else currentcat Active
        , case when coalesce(gcat_active, activity_type = 'A', false) then 'Active' else 'Inactive' end as status
        , case when has_psatcat_record then 'gcat_psatcat' else 'gcat_currentcat' end as status_source
        , _source_file
        , _source_updated_at
        , {{ helper__audit_fields() }}
    from cte_gcat_object_status as obj
    join cte_payload_field_inheritance as inherit using (jcat)
)

select * from cte_final
