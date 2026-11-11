{% macro helper__parse_vague_date_columns(col, name) -%}
cast({{ sattrack.helper__parse_vague_date_base(col) }} as timestamp) as {{ name }}
        , cast({{ sattrack.helper__parse_vague_date_start(col) }} as timestamp) as {{ name }}_start
        , cast({{ sattrack.helper__parse_vague_date_end(col) }} as timestamp) as {{ name }}_end
        , {{ sattrack.helper__parse_vague_date_precision(col) }} as {{ name }}_precision
{%- endmacro %}
