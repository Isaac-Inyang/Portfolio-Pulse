{{ config(
    materialized='table',
    schema='marts'
) }}

WITH daily_portfolio_value AS (
    SELECT 
        transaction_date,

            -- Net Cash Invested (Total Buy Capital spent minus Capital Recovered from Sales)
            ROUND(
                SUM(
                    CASE 
                        WHEN transaction_type = 'Buy' THEN (shares * price_usd)
                        WHEN transaction_type = 'Sell' THEN -(shares * price_usd)
                        ELSE 0 
                    END
                ), 2
            ) AS net_cash_invested_usd

    FROM {{ ref('stg_stock_transactions') }}
    GROUP BY transaction_date
),

cummulative_portfolio_value AS (
    SELECT
        transaction_date,
        ROUND(
            SUM(net_cash_invested_usd) 
            OVER(
                ORDER BY transaction_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ), 2
        ) AS cumulative_portfolio_value_usd
    FROM daily_portfolio_value
),

current_prices AS (
    SELECT
        y.ticker,
        y.price_date,
        ROUND((y.price_usd * COALESCE(s.current_shares, 0)), 2) AS stock_value_usd
    FROM {{ ref('stg_yfinance_prices') }} y
    LEFT JOIN {{ ref('int_transaction_summary') }} s
    ON y.ticker = s.ticker
),

latest_stock_prices AS (
    SELECT
        price_date AS latest_price_date,
        ROUND(SUM(stock_value_usd), 2) AS latest_portfolio_value_usd
    FROM current_prices
    GROUP BY price_date
)

SELECT
    transaction_date::date,
    cumulative_portfolio_value_usd::numeric(20,2)
FROM cummulative_portfolio_value

UNION ALL

SELECT
    latest_price_date::date AS transaction_date,
    latest_portfolio_value_usd::numeric(20,2) AS cumulative_portfolio_value_usd
FROM latest_stock_prices

ORDER BY transaction_date ASC