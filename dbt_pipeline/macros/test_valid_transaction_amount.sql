-- Custom generic test: ensures transaction amounts are reasonable
{% macro test_valid_transaction_amount(model, column_name, min_amount=0, max_amount=5000) %}

    select count(*)
    from {{ model }}
    where {{ column_name }} < {{ min_amount }}
       or {{ column_name }} > {{ max_amount }}
       or {{ column_name }} is null

{% endmacro %}
