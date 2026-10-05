
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
DROP TABLE IF EXISTS raw.yfinance_prices;
CREATE TABLE IF NOT EXISTS raw.yfinance_prices (
    ticker      VARCHAR(10) NOT NULL,
    price_date  DATE NOT NULL,
    price_usd   NUMERIC(18, 4) NOT NULL,
    sector      VARCHAR(100),
    

    PRIMARY KEY (ticker, price_date)
);
"""

UPSERT_SQL = """
    INSERT INTO raw.yfinance_prices (
        ticker,
        price_date,
        price_usd,
        sector
        
    )
    VALUES (%(ticker)s, %(price_date)s, %(price_usd)s, %(sector)s)
    ON CONFLICT (ticker, price_date)
    DO UPDATE SET
        price_usd = EXCLUDED.price_usd,
        sector = EXCLUDED.sector;
"""

# GET LATEST STOCK PRICES

def get_yfinance_data(TICKERS):
    """
    Fetches the latest closing price and sector info 
    for all configured tickers.
    """


    print("\nFetching latest stock prices from yfinance...")

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
            # 1. Isolate the specific ticker's table segment
            ticker_df = data[ticker]
            
            # 2. Extract the absolute last row available
            # latest_row = ticker_df.iloc[-1]
            latest_row = ticker_df.dropna(subset=["Close"]).iloc[-1]
            closing_price = latest_row['Close']
            
            # 3. Pull the date directly from the DataFrame index name
            # .name extracts the timestamp value; strftime converts it to 'YYYY-MM-DD'
            trading_date = latest_row.name.strftime('%Y-%m-%d')
            
            # 4. Fetch the company profile sector
            stock_profile = yf.Ticker(ticker)
            sector = stock_profile.info.get('sector', 'Unknown Sector')
            
            # 5. Append as an object perfectly modeled for database columns
            stock_data.append({
                "ticker": ticker,
                "price_date": trading_date,
                "price_usd": round(float(closing_price), 2),
                "sector": sector
            })
        except Exception as e:
            print(f"Error parsing data for {ticker}: {e}")

    return stock_data

# --- TEST EXECUTION ---
# MY_TICKERS = ['AAPL', 'MSFT']
# db_payload = get_yfinance_data(MY_TICKERS)
# print(db_payload)



def load_to_postgres(dsn: str, stock_data: list):
    """Load the stock data into the postgres database"""
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    
    # Batch insert ALL stock data at once 
    # Pass the list of dicts directly to executemany
    cursor.executemany(UPSERT_SQL, stock_data)
    conn.commit()
    cursor.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Fetch latest stock prices and load into Postgres.")
    parser.add_argument(
        "--dsn",
        required=True,
        help="Postgres DSN connection string"
    )
    args = parser.parse_args()

    print("Starting yfinance data ingestion...")

    try:
        data = get_yfinance_data(TICKERS)
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
