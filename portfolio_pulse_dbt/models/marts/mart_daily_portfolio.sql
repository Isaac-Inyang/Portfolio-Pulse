{{ config(
    materialized='table',
    schema='marts'
) }}


WITH ranked_dates AS (
    SELECT
        ticker,
        price_date,
        price_usd,
        ROW_NUMBER() OVER(PARTITION BY ticker ORDER BY price_date DESC) AS row_n
    FROM {{ref('stg_yfinance_prices')}}
),

top_2_dates AS (
    SELECT
        ticker,
        MAX(CASE WHEN row_n = 1 THEN price_date END) AS todays_date,
        MAX(CASE WHEN row_n = 1 THEN price_usd END) AS todays_price,
        MAX(CASE WHEN row_n = 2 THEN price_usd END) AS yesterdays_price
    FROM ranked_dates
    WHERE row_n <= 2
    GROUP BY ticker
    
),

daily_price_comparison AS (
    SELECT
        p.todays_date AS market_date,
        p.ticker,
        s.current_shares AS active_shares,
        ROUND((s.current_shares * p.todays_price), 2) AS todays_value,
        ROUND((s.current_shares * p.yesterdays_price), 2) AS yesterdays_value
    FROM top_2_dates p
    INNER JOIN {{ref('int_transaction_summary')}} s
    ON p.ticker = s.ticker

)

SELECT 
    market_date,
    ROUND(SUM(todays_value), 2) AS todays_value,
    ROUND(SUM(yesterdays_value), 2) AS yesterdays_value
FROM daily_price_comparison
GROUP BY market_date