{#- normalised core: single spaces, flags stripped, a three-digit year padded to four digits (GCAT orgs write e.g. '927 Jul 12', '843') -#}
{% macro helper__normalise_vague_date(col) -%}
regexp_replace(regexp_replace(regexp_replace(regexp_replace(trim({{ sattrack.helper__quote_column(col) }}), '\s+', ' ', 'g'), '\?$', ''), '(\d)s$', '\1'), '^(\d{3})( |$)', '0\1\2')
{%- endmacro %}
