{#
    Use custom schema names as-is (staging, intermediate, marts) instead of dbt's default
    "<target_schema>_<custom_schema>", so BI tools see clean schema names. See ADR 0003.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
