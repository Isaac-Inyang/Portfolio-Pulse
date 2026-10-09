{{ config(
    materialized='table',
    schema='marts'
) }}

WITH latest_fx AS (
    SELECT
        conversion_rate_ngn
    FROM {{ ref('stg_exchange_rates') }}
    ORDER BY updated_at DESC
    LIMIT 1
),

current_positions AS (
    SELECT
        ticker,
        latest_value_usd
    FROM {{ ref('mart_profit_loss') }}
    WHERE active_shares > 0
)

SELECT
    ROUND(SUM(p.latest_value_usd), 2)
        AS portfolio_value_usd,

    ROUND(
        SUM(p.latest_value_usd) * fx.conversion_rate_ngn,
        2
    ) AS portfolio_value_ngn

FROM current_positions p
CROSS JOIN latest_fx fx
GROUP BY fx.conversion_rate_ngn