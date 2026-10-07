{{ config(materialized='view') }}

SELECT 
    trade_id::VARCHAR AS transaction_id,
    trade_date::DATE AS transaction_date,
    ticker::VARCHAR,
    transaction_type::VARCHAR,
    shares::NUMERIC(20,4),
    price_usd::NUMERIC(20,2),
    fx_rate_at_trade_ngn::NUMERIC(20,4) AS fx_rate_ngn
FROM {{ source('raw', 'raw_stock_transactions') }}