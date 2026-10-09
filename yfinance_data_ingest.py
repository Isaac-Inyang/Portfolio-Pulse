
import sys
import yfinance as yf
import psycopg2
import argparse


"""
CONFIGURATION
"""

TICKERS = [
    "AAPL",
    "MSFT",
    "AMZN",
    "GOOGL",
    "JPM",
    "JNJ",
    "XOM",
    "WMT"
]


CREATE_TABLE_SQL = """
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.raw_yfinance_prices (
    ticker      VARCHAR(10) NOT NULL,
    price_date  DATE NOT NULL,
    price_usd   NUMERIC(18, 4) NOT NULL,
    

    PRIMARY KEY (ticker, price_date)
);
"""

UPSERT_SQL = """
    INSERT INTO raw.raw_yfinance_prices (
        ticker,
        price_date,
        price_usd
        
    )
    VALUES %s
    ON CONFLICT (ticker, price_date)
    DO UPDATE SET
        price_usd = EXCLUDED.price_usd
    ;
"""

# GET LATEST STOCK PRICES

def get_yfinance_data(TICKERS, mode: str):
    """
    Fetches either historical data at first run or the latest closing price and sector info 
    for all configured tickers.
    
    historical: From START_DATE through the latest available trading date.
    daily: Recent 5-calendar-day window.

    """
    print(f"\nFetching {mode} stock prices from yfinance...")

    if mode == "historical":
        START_DATE = "2021-01-11"
        data = yf.download(
            tickers=TICKERS,
            start=START_DATE,
            interval="1d",
            auto_adjust=False,
            group_by="ticker",
            progress=False,
            threads=True,
        )
    
    else:
        # Pulling a 5-day window guarantees we catch the last active trading session
        data = yf.download(
            tickers=TICKERS,
            period="5d",
            interval="1d",
            auto_adjust=False,
            group_by="ticker",
            progress=False,
            threads=True
        )

    if data.empty:
        raise ValueError("No stock price data was returned by yfinance.")

    stock_data = []

    for ticker in TICKERS:
        try:
            ticker_df = data[ticker]

            if mode== "historical":

                # Ignore dates where no closing price is available.
                ticker_df = ticker_df.dropna(subset=["Close"])

                for trading_date, row in ticker_df.iterrows():
                    closing_price = float(row["Close"])

                    # stock_data.append({
                    #     "ticker": ticker,
                    #     "price_date": trading_date.date(),
                    #     "price_usd": round(closing_price, 4)
                    # })
                    stock_data.append((
                        ticker,
                        trading_date.date().strftime('%Y-%m-%d'),
                        round(closing_price, 4)
                    ))

            else:
                # Ignore dates where no closing price is available.
                clean_df = ticker_df.dropna(subset=["Close"])
                if clean_df.empty:
                    print(f"No valid data records returned for {ticker}. Skipping.")
                    continue

                # Extract the absolute latest single row available
                latest_row = clean_df.iloc[-1]
                closing_price = float(latest_row["Close"])

                trading_date = latest_row.name.strftime('%Y-%m-%d')

                stock_data.append((
                    ticker,
                    trading_date,
                    round(closing_price, 4)
                ))

            print(
                f"{ticker}: collected {len(ticker_df)} daily price records."
            )

        except Exception as exc:
            print(f"Error processing {ticker}: {exc}")


    return stock_data


def load_to_postgres(dsn: str, stock_data: list):
    """Load the stock data into the postgres database"""
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)

    from psycopg2.extras import execute_values
    
    # Batch insert ALL stock data at once 
    # Pass the list of dicts directly to executemany
    execute_values(cursor, UPSERT_SQL, stock_data)
    # cursor.executemany(UPSERT_SQL, stock_data)
    conn.commit()
    cursor.close()
    conn.close()



def main():
    parser = argparse.ArgumentParser(description="Fetching historical or recent stock prices and load into Postgres.")
    parser.add_argument(
        "--dsn",
        required=True,
        help="Postgres DSN connection string"
    )

    parser.add_argument(
        "--mode",
        choices=["historical", "daily"],
        default= "daily"
    )
    args = parser.parse_args()

    print("Starting yfinance data ingestion...")

    try:
        data = get_yfinance_data(TICKERS, args.mode)
        print(f"Successfully fetched {len(data)} records from yfinance.")
    except Exception as e:
        print(f"ERROR: could not fetch yfinance data: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        load_to_postgres(args.dsn, data)
        print(f"Successfully loaded {len(data)} records into Postgres.")
    except Exception as e:
        print(f"ERROR: could not load data into Postgres: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
