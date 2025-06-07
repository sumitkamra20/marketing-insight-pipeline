--Simple macros to categorize sales sizes and add timestamps.
-- Simple macro to generate current timestamp for audit fields
{% macro get_current_timestamp() %}
    {{ return("current_timestamp()") }}
{% endmacro %}

-- Simple macro to categorize sales amounts
{% macro categorize_sale_size(amount_column) %}
    case
        when {{ amount_column }} < 50 then 'Small'
        when {{ amount_column }} between 50 and 200 then 'Medium'
        when {{ amount_column }} between 201 and 500 then 'Large'
        else 'Extra Large'
    end
{% endmacro %}
