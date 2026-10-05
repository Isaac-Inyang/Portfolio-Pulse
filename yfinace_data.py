
import argparse

import pandas as pd
import psycopg2
import yfinance as yf


# =========================================================
# CONFIGURATION
# =========================================================

TICKERS = [
    "AAPL",
    "MSFT",
    "AMZN",
    "GOOGL",
    "JPM",
    "JNJ",
    "XOM",
    "WMT",
]



# =========================================================
# CREATE DATABASE TABLE
# =========================================================

CREATE_TABLE_SQL = """
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.yfinance_prices (
    ticker      VARCHAR(10) NOT NULL,
    price_usd   NUMERIC(18, 4) NOT NULL,
    sector      VARCHAR(100),
    price_date  DATE NOT NULL,

    PRIMARY KEY (ticker, price_date)
);
"""


# =========================================================
# GET LATEST STOCK PRICES
# =========================================================

def get_latest_prices():
    """
    Download the latest available daily closing prices
    for all configured tickers.
    """

    print("\nFetching latest stock prices from yfinance...")

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
        raise ValueError(
            "No stock price data was returned by yfinance."
        )

    return data


# =========================================================
# GET SECTOR INFORMATION
# =========================================================

def get_sectors():
    """
    Retrieve the sector for each ticker.
    """

    sectors = {}

    print("\nFetching sector information...")

    for ticker_symbol in TICKERS:

        print(f"Getting sector for {ticker_symbol}...")

        ticker = yf.Ticker(ticker_symbol)

        try:
            sector = ticker.info.get("sector")

        except Exception as error:
            print(
                f"Warning: Could not retrieve sector for "
                f"{ticker_symbol}: {error}"
            )
            sector = None

        sectors[ticker_symbol] = sector

    return sectors


# =========================================================
# TRANSFORM DATA
# =========================================================

def transform_data(stock_data, sectors):
    """
    Prepare the latest price for each ticker for database loading.
    """

    records = []

    print("\nTransforming data...")

    for ticker in TICKERS:

        try:
            ticker_data = stock_data[ticker].copy()

        except KeyError:
            print(
                f"Warning: No data returned for {ticker}. "
                "Skipping ticker."
            )
            continue

        # Remove rows where Close is missing
        ticker_data = ticker_data.dropna(subset=["Close"])

        if ticker_data.empty:
            print(
                f"Warning: No valid closing price found for {ticker}."
            )
            continue

        # Get the most recent available trading day
        latest_row = ticker_data.iloc[-1]

        price = latest_row["Close"]
        price_date = ticker_data.index[-1]

        # Convert pandas Timestamp to Python date
        price_date = pd.Timestamp(price_date).date()

        # Get sector
        sector = sectors.get(ticker)

        records.append(
            (
                ticker,
                float(price),
                sector,
                price_date
            )
        )

        print(
            f"{ticker}: "
            f"${float(price):,.2f} | "
            f"{sector} | "
            f"{price_date}"
        )

    if not records:
        raise ValueError(
            "No valid records were prepared for loading."
        )

    return records


# =========================================================
# LOAD DATA INTO NEON
# =========================================================

def load_to_neon(dsn, records):
    """
    Create the raw table and load the daily records into Neon.
    """

    print("\nConnecting to Neon...")

    connection = psycopg2.connect(dsn)

    try:

        with connection.cursor() as cursor:

            # Create schema and table
            cursor.execute(CREATE_TABLE_SQL)

            # Insert records
            insert_sql = """
                INSERT INTO raw.yfinance_prices (
                    ticker,
                    price_usd,
                    sector,
                    price_date
                )
                VALUES %s

                ON CONFLICT (ticker, price_date)
                DO UPDATE SET
                    price_usd = EXCLUDED.price_usd,
                    sector = EXCLUDED.sector;
            """

            execute_values(
                cursor,
                insert_sql,
                records
            )

        connection.commit()

        print(
            f"\nSuccessfully loaded {len(records)} "
            "records into Neon."
        )

    except Exception as error:

        connection.rollback()

        print(
            "\nDatabase transaction failed."
        )

        print(f"Error: {error}")

        raise

    finally:

        connection.close()

        print("Neon connection closed.")


def parse_arguments():
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Fetch the latest daily stock prices from yfinance "
            "and load them into Neon PostgreSQL."
        )
    )

    parser.add_argument(
        "--dsn",
        required=True,
        help="Neon PostgreSQL connection string"
    )

    return parser.parse_args()


# =========================================================
# MAIN
# =========================================================

def main():

    # Get command-line arguments
    args = parse_arguments()

    print("=" * 60)
    print("PortfolioPulse - yfinance Daily Ingestion")
    print("=" * 60)

    print(
        f"Tickers: {', '.join(TICKERS)}"
    )

    # -----------------------------------------------------
    # EXTRACT
    # -----------------------------------------------------

    stock_data = get_latest_prices()

    # -----------------------------------------------------
    # EXTRACT SECTOR INFORMATION
    # -----------------------------------------------------

    sectors = get_sectors()

    # -----------------------------------------------------
    # TRANSFORM
    # -----------------------------------------------------

    records = transform_data(
        stock_data,
        sectors
    )

    # -----------------------------------------------------
    # LOAD
    # -----------------------------------------------------

    load_to_neon(
        args.dsn,
        records
    )

    print("\n" + "=" * 60)
    print("Ingestion completed successfully.")
    print("=" * 60)


# =========================================================
# SCRIPT ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()