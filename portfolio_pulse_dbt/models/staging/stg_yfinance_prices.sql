{{ config(materialized='view') }}

SELECT
        -- Combining ticker and date into a single unique MD5 text hash string
    md5(cast(UPPER(TRIM(ticker)) as varchar) || '-' || cast(price_date as varchar)) as price_id,
    UPPER(TRIM(ticker))::VARCHAR AS ticker,
    price_date::DATE,
    price_usd::NUMERIC(20,2)
FROM {{ source('raw', 'raw_yfinance_prices') }}
ORDER BY price_date DESC , ticker ASC