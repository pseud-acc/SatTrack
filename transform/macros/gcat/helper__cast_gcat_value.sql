{% macro helper__cast_gcat_value(col, type) -%}
try_cast({{ sattrack.helper__clean_gcat_text(col) }} as {{ type }})
{%- endmacro %}
