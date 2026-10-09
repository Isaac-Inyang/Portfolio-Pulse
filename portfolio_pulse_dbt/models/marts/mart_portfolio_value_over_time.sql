{{ config(
    materialized ="table",
    schema= "marts"
)}}

WITH net_shares_basis AS (
    SELECT
        ticker,
        transaction_date,
        ROUND(
            SUM(
                CASE WHEN transaction_type = 'Buy' THEN shares
                    WHEN transaction_type = 'Sell' THEN -shares
                    ELSE 0 END
            ), 2
        ) AS shares_held
    FROM {{ref('stg_stock_transactions')}}
    GROUP BY ticker, transaction_date
),

historical_shares AS (
    SELECT
        ticker,
        transaction_date AS balance_date,
        shares_held,
        SUM(shares_held) OVER(
            PARTITION BY ticker ORDER BY transaction_date ASC
        ) AS shares_held_on_date
    FROM net_shares_basis
),

total_ticker_valuation AS (
    SELECT
        y.price_date,
        y.ticker,
        y.price_usd,
        b.shares_held_on_date AS raw_shares,
        ROW_NUMBER() OVER(
            PARTITION BY y.ticker, y.price_date ORDER BY b.balance_date DESC
        ) AS row_n
    FROM {{ref('stg_yfinance_prices')}} y
    LEFT JOIN historical_shares b
    ON y.ticker = b.ticker AND b.balance_date <= y.price_date
),

final_position AS (
    SELECT
        price_date,
        ticker,
        price_usd,
        COALESCE(raw_shares, 0) AS shares_held,
        COALESCE((raw_shares * price_usd),0) AS position_value_usd
    FROM total_ticker_valuation
    WHERE row_n = 1
)

SELECT 
    price_date,
    ROUND(
        SUM(position_value_usd), 2
    ) AS portfolio_value_usd
FROM final_position
GROUP BY price_date
ORDER BY price_date ASC    

