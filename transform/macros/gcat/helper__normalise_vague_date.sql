{#- normalised core: single spaces, flags stripped -#}
{% macro helper__normalise_vague_date(col) -%}
regexp_replace(regexp_replace(regexp_replace(trim({{ sattrack.helper__quote_column(col) }}), '\s+', ' ', 'g'), '\?$', ''), '(\d)s$', '\1')
{%- endmacro %}
