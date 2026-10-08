{{ config(
    materialized='view',
    schema='intermediate'
) }}

WITH transaction_summary AS (
    SELECT
        ticker,

        ROUND(
            SUM(
                CASE
                    WHEN transaction_type = 'Buy' THEN shares
                    ELSE 0 END
            ), 2
        ) AS shares_bought,

        ROUND(
            SUM(
                CASE 
                    WHEN transaction_type = 'Buy' THEN shares
                    WHEN transaction_type = 'Sell' THEN -shares
                    ELSE 0 
                END
            ), 2
        ) AS current_shares,

        ROUND(
            SUM(
                CASE
                    WHEN transaction_type = 'Buy' THEN (shares * price_usd)
                    ELSE 0 END
            ) , 2
        ) AS total_usd_spent,

        -- Net Cash Invested (Total Buy Capital spent minus Capital Recovered from Sales)
        ROUND(
            SUM(
                CASE 
                    WHEN transaction_type = 'Buy' THEN (shares * price_usd)
                    WHEN transaction_type = 'Sell' THEN -(shares * price_usd)
                    ELSE 0 
                END
            ), 2
        ) AS net_cash_invested_usd,

        ROUND(
            SUM(
                CASE 
                    WHEN transaction_type = 'Buy' THEN (shares * price_usd * fx_rate_ngn)
                    WHEN transaction_type = 'Sell' THEN -(shares * price_usd * fx_rate_ngn)
                    ELSE 0 
                END
            ), 2
        ) AS net_cash_invested_ngn,

        --Total Sales Performance (Realized Revenue)
        ROUND(
            SUM(
                CASE 
                    WHEN transaction_type = 'Sell' THEN (shares * price_usd)
                    ELSE 0 
                END
            ), 2
        ) AS sales_amount_usd,

        ROUND(
            SUM(
                CASE 
                    WHEN transaction_type = 'Sell' THEN (shares * price_usd * fx_rate_ngn)
                    ELSE 0 
                END
            ), 2
        ) AS sales_amount_ngn,

        -- 4. Tracking Totals to compute Average Buy Cost Basis accurately
        SUM(CASE WHEN transaction_type = 'Buy' THEN shares ELSE 0 END) AS total_shares_bought,
        SUM(CASE WHEN transaction_type = 'Buy' THEN (shares * price_usd) ELSE 0 END) AS total_capital_spent_usd

    FROM {{ ref('stg_stock_transactions') }}
    GROUP BY ticker
)

SELECT 
    ticker,
    shares_bought,
    current_shares,
    total_usd_spent,
    net_cash_invested_usd,
    net_cash_invested_ngn,
    sales_amount_usd,
    sales_amount_ngn

FROM transaction_summary
