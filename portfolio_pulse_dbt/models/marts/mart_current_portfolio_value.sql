{{ config(
    materialized='table',
    schema='marts'
) }}


WITH latest_ngn_price AS (
    SELECT
        y.ticker,
        ROUND(s.conversion_rate_ngn,2) AS latest_fx_rate_ngn
    FROM {{ref('stg_yfinance_prices')}} y
    INNER JOIN {{ref('stg_exchange_rates')}} s
    ON y.price_date = s.updated_at
),

current_portfolio_value AS (
    SELECT 
        l.ticker,
        m.latest_value_usd AS position_value_usd,
        (m.latest_value_usd * l.latest_fx_rate_ngn) AS position_value_ngn
    FROM latest_ngn_price l
    INNER JOIN {{ref('mart_profit_loss')}} m
    ON l.ticker = m.ticker
)

SELECT
    ROUND(SUM(position_value_usd),2) AS portfolio_value_usd,
    ROUND(SUM(position_value_ngn), 2) AS portfolio_value_ngn

FROM current_portfolio_value