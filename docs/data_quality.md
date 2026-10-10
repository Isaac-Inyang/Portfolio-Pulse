#  Data Quality & Pipeline Testing Documentation

Data integrity is the foundational core of the **Portfolio Pulse** pipeline. Because this system drives high-stakes financial visualizations (such as net worth calculations and investment yields), the data transformation pipeline incorporates automated quality gates. 

Using **dbt Core**, tests are compiled and executed directly against the cloud PostgreSQL instance to trap data anomalies before they can distort the frontend Metabase dashboard metrics.

---

## Test Suite Architecture

The data testing strategy operates at two primary checkpoints in the ETL lifecycle:
1. **The Staging Layer Gate:** Validates raw inbound rows immediately after extraction from Google Sheets and APIs.
2. **The Analytics Marts Gate:** Hardens the aggregated calculations, date alignments, and currency structures before dashboard exposure.

### Summary of Core Test Constraints Applied
*   `not_null`: Assures that critical processing attributes (like currency exchange counts, transactional sizes, and dates) contain zero missing or blank cells.
*   `unique`: Prevents data amplification bugs by ensuring primary key constraints (like asset tickers and specific calendar dates) never duplicate across rows.

---

## Configured Tests Breakdown (`schema.yml`)

The following structural mapping defines the automated testing rules deployed across the core analytical models:

### A. Daily Performance Snapping (`mart_daily_portfolio_delta`)
*Tracks day-over-day total valuation movements for Metabase KPI trend widgets.*
*   **`market_date` (`not_null`):** Ensures that the chronological sequence is intact. A blank date would prevent Metabase from running its lookback functions.
*   **`todays_portfolio_value` (`not_null`):** Guarantees that today's live stock valuation is fully calculated.
*   **`yesterdays_portfolio_value` (`not_null`):** Assures that the comparative baseline is present, preventing mathematical errors when calculating the daily percentage shift.

### B. Unified Master Timeline (`mart_portfolio_value_trend`)
*Continuous daily timeline grid bridging 2021 history with modern live yfinance updates.*
*   **`transaction_date` (`not_null`):** Ensures every single calendar row has a valid date coordinate to map cleanly to the continuous line chart X-axis.
*   **`cumulative_portfolio_value_usd` (`not_null`):** Confirms that the running window function (`SUM() OVER`) successfully calculated a numerical dollar balance for every single day across the 5-year timeline.

### C. Open Positions Profitability Ledger (`mart_position_profit_loss`)
*Calculates unrealized performance yields and average cost basis per active stock holding.*
*   **`ticker` (`not_null` & `unique`):** **Critical Operational Gate.** Enforcing uniqueness on the asset column ensures that individual stock metrics (like AAPL or MSFT) never repeat horizontally. If a ticker appears twice, it signifies a critical duplication bug in the upstream joins.
*   **`active_shares` (`not_null`):** Assures that the inventory snapshot has a clear numerical volume count.
*   **`profit_loss_usd` (`not_null`):** Verifies that the net dollar gain calculation is fully computed for every active position.

---

## Execution & Automated CI/CD Integration

The data quality test suite is fully containerized and orchestrated automatically to ensure the dashboard remains verified over time.

### Local Manual Execution
To manually audit and run the data quality suite locally inside the PowerShell terminal environment, execute the native dbt testing framework command:
```powershell
dbt test
```

### GitHub Actions Integration Pipeline
During daily automated production cycles, the test runner is embedded straight into the deployment workflow:
1. At **8:00 PM (Monday–Friday)**, the Python engine ingests the US market closing prices.
2. `dbt run` compiles the analytical data layer.
3. `dbt test` instantly triggers. If a single constraint fails (e.g., a null price or duplicate ticker row is trapped), the pipeline immediately shuts down and flags an operational alert. This failsafe guarantees that corrupted records can never flow downstream into Metabase.

---

## Data Validation Metrics

By maintaining this defensive testing structure, the pipeline successfully isolates and handles extreme edge cases natively in the data warehouse layer:
*   **Zero Arithmetic Inversions:** The tests verify that all share volume tallies successfully resolve to non-null numeric properties.
*   **Precision Rounding Guardrails:** All calculations are strictly audited using `ROUND(..., 2)` rules to bypass standard system floating-point decimal anomalies.
*  **Data Cleaning Guardrails:** All import from raw to staging model follows a data cleaning framework which includes:
    - **Trim():** to eliminate whitespaces
    - **Data type casting:** To ensure only the right data type is allowed through the model for each column.
