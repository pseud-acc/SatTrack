{#- Title-case a Space-Track name, including words after '/' and '(' ("(INTELSAT)" -> "(Intelsat)"). -#}
{% macro helper__title_case_name(expr) -%}
replace(replace(
    array_to_string(list_transform(
        string_split(replace(replace(lower({{ expr }}), '/', ' / '), '(', '( '), ' '),
        lambda w: upper(left(w, 1)) || substr(w, 2)), ' '),
    '( ', '('), '  ', ' ')
{%- endmacro %}
