{{config(
    materialized='view'
)}}

SELECT
    time_last_update_utc::date AS updated_at,
    base_code::VARCHAR AS base_currency,
    conversion_rate::NUMERIC(20,2) AS conversion_rate_ngn
FROM {{ source('raw', 'raw_exchange_rate_ingestion') }}