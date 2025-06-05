{{
    config(
        materialized='view'
    )
}}

with raw_spend as (
  select
    date             as raw_date,
    offline_spend    as offline_spend,
    online_spend     as online_spend
  from {{ source('raw','marketing_spend') }}
)

select
  try_to_date(raw_date, 'MM/DD/YYYY') as spend_date,
  offline_spend::NUMBER(38,0)   as offline_spend,
  online_spend::FLOAT           as online_spend
from raw_spend
