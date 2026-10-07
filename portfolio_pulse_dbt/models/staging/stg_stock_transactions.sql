{{ config(materialized='view') }}

SELECT 
    TRIM(trade_id)::VARCHAR AS transaction_id,
    TRIM(trade_date)::DATE AS transaction_date,
    UPPER(TRIM(ticker))::VARCHAR AS ticker,
    INITCAP(TRIM(transaction_type))::VARCHAR AS transaction_type,
    shares::NUMERIC(20,4),
    price_usd::NUMERIC(20,2),
    fx_rate_at_trade_ngn::NUMERIC(20,4) AS fx_rate_ngn
FROM {{ source('raw', 'raw_stock_transactions') }}
WHERE transaction_type IN ('BUY', 'SELL')