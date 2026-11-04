{# Small generic tests, implemented here to keep the project free of external packages. #}

{% test positive_values(model, column_name) %}
    select {{ column_name }}
    from {{ model }}
    where {{ column_name }} <= 0
{% endtest %}


{% test unique_combination_of_columns(model, combination_of_columns) %}
    {%- set columns = combination_of_columns | join(', ') %}
    select {{ columns }}, count(*) as occurrences
    from {{ model }}
    group by {{ columns }}
    having count(*) > 1
{% endtest %}
