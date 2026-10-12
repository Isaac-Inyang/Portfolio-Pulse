# Metrics and Business Logic

PortfolioPulse distinguishes portfolio valuation from transaction cash flows and investment performance.

## Current market value

The estimated current market value of a position is calculated using the active shares held and the latest available market price:

`Position market value = Active shares × Latest available price`

Portfolio market value in USD is the sum of the market values of all active positions.

## Portfolio value in NGN

The NGN valuation converts the USD portfolio value using the selected USD–NGN exchange rate:

`Portfolio value (NGN) = Portfolio value (USD) × Selected USD–NGN rate`

The selected exchange rate and its effective date should be documented so readers can understand how the converted value was obtained.

## Historical portfolio value

Historical market value is calculated by valuing the holdings attributable to each valuation date using the corresponding market prices:

`Historical portfolio value = Sum of (Shares held at date × Price at date)`

This is a market-value measure, not a cumulative sum of purchase costs or net cash invested. The implementation should define how weekends, market holidays, missing prices, and dates with no new transactions are handled.

## Unrealized profit or loss

Unrealized profit or loss compares the market value of active holdings with their allocated cost basis:

`Unrealized P/L = Market value of active holdings − Cost basis of active holdings`

The cost-basis method used by the project—such as weighted-average cost or FIFO—must be documented and consistently applied. The result should not be described as realized profit or loss.

## Unrealized ROI

`Unrealized ROI (%) = Unrealized P/L ÷ Cost basis of active holdings × 100`

For a portfolio-level ROI, calculate total unrealized profit or loss divided by total cost basis of active holdings. Do not use a simple average of individual ticker ROI percentages as a substitute for the portfolio-level calculation.

## Net cash invested

Net cash invested is a cash-flow measure:

`Net cash invested = Purchase costs − Sale proceeds`

It is not necessarily the same as the cost basis of the shares currently held. Sale proceeds also do not, on their own, represent realized profit or loss; realized profit or loss requires the cost basis of the shares sold.

## Portfolio allocation

For market-value allocation:

`Ticker allocation (%) = Ticker market value ÷ Total portfolio market value × 100`


These definitions describe the intended business logic.