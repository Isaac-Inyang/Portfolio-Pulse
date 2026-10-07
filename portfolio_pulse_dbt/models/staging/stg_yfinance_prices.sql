{{ config(materialized='view') }}

SELECT
        -- Combining ticker and date into a single unique MD5 text hash string
    md5(cast(UPPER(TRIM(ticker)) as varchar) || '-' || cast(price_date as varchar)) as price_id,
    UPPER(TRIM(ticker))::VARCHAR AS ticker,
    price_date::DATE,
    price_usd::NUMERIC(20,2),
    INITCAP(TRIM(sector))::VARCHAR AS sector
FROM {{ source('raw', 'yfinance_prices') }}
ORDER BY price_date , ticker ASC