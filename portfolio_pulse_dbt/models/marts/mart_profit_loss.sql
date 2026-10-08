{{ config(
    materialized='table',
    schema='marts'
) }}

WITH stock_prices AS (
    SELECT
        ticker,
        price_date,
        price_usd,
        ROW_NUMBER() OVER(PARTITION BY ticker ORDER BY price_date DESC) AS row_num
    FROM {{ ref('stg_yfinance_prices') }}
),

latest_prices AS (
    SELECT
        y.ticker,
        y.price_usd AS latest_price_usd,
        ROUND((y.price_usd * COALESCE(s.current_shares, 0)),2) AS latest_value_usd,
        ROUND((s.total_usd_spent / NULLIF(s.shares_bought, 0)), 2) AS average_buy_cost,
        s.shares_bought,
        s.current_shares AS active_shares,
        s.total_usd_spent
    FROM stock_prices y
    LEFT JOIN {{ ref('int_transaction_summary') }} s
    ON y.ticker = s.ticker
    WHERE y.row_num = 1
)

SELECT
    ticker,

    active_shares,
    latest_value_usd,
    ROUND(( average_buy_cost * active_shares),2) AS total_cost_basis_usd,
    
    --calculating profit/loss in usd
    ROUND(
        (latest_value_usd - ( average_buy_cost * active_shares)
        ), 2
    ) AS profit_loss_usd,

    --calculating ROI in percentage
    ROUND(
        (((latest_price_usd - average_buy_cost) / average_buy_cost) * 100), 2
    ) AS ROI_usd

FROM latest_prices

