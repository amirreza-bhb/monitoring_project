import logging
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import jdatetime
import pandas as pd
import requests
from sqlalchemy import create_engine, text

# ====================================================================
# Database Configuration
# ====================================================================
server = "localhost"
database = "ecoMonitoringDB"

connection_string = ("DRIVER={ODBC Driver 18 for SQL Server};"
                     f"SERVER={server};"
                     f"DATABASE={database};"
                     "Trusted_Connection=yes;"
                     "TrustServerCertificate=yes;")

engine = create_engine("mssql+pyodbc:///?odbc_connect=" + quote_plus(connection_string))

# ====================================================================
# Source Configuration
# ====================================================================
sources = [{"name": "brent_oil", "table_name": "brent_oil_prices",
            "base_url": "https://api.tgju.org/v1/market/indicator/summary-table-data/energy-brent-oil",
            "pagination": {"offset_param": "start", "limit_param": "length"}, "response_key": "data",
            "raw_columns": ["open_value", "low_value", "high_value", "close_value", "change_value", "change_percent",
                            "date_gregorian", "date_jalali"],
            "clean_columns": ["open_value", "low_value", "high_value", "close_value", "date_g", "date_j"],
            "date_column_raw": "date_gregorian", "date_column_clean": "date_g", "date_converter": "gregorian",
            "numeric_columns": ["open_value", "low_value", "high_value", "close_value"], "numeric_cleaner": "comma"},
           {"name": "gold_18k", "table_name": "gold_prices_18k",
            "base_url": "https://api.tgju.org/v1/market/indicator/summary-table-data/geram18",
            "pagination": {"offset_param": "start", "limit_param": "length"}, "response_key": "data",
            "raw_columns": ["open_value", "low_value", "high_value", "close_value", "change_value", "change_percent",
                            "date_gregorian", "date_jalali"],
            "clean_columns": ["open_value", "low_value", "high_value", "close_value", "date_g", "date_j"],
            "date_column_raw": "date_gregorian", "date_column_clean": "date_g", "date_converter": "gregorian",
            "numeric_columns": ["open_value", "low_value", "high_value", "close_value"], "numeric_cleaner": "comma"},
           {"name": "gold_global", "table_name": "gold_prices_global",
            "base_url": "https://api.tgju.org/v1/market/indicator/summary-table-data/ons",
            "pagination": {"offset_param": "start", "limit_param": "length"}, "response_key": "data",
            "raw_columns": ["open_value", "low_value", "high_value", "close_value", "change_value", "change_percent",
                            "date_gregorian", "date_jalali"],
            "clean_columns": ["open_value", "low_value", "high_value", "close_value", "date_g", "date_j"],
            "date_column_raw": "date_gregorian", "date_column_clean": "date_g", "date_converter": "gregorian",
            "numeric_columns": ["open_value", "low_value", "high_value", "close_value"], "numeric_cleaner": "comma"},
           {"name": "usd_free", "table_name": "usd_free_market_rates",
            "base_url": "https://api.tgju.org/v1/market/indicator/summary-table-data/price_dollar_rl",
            "pagination": {"offset_param": "start", "limit_param": "length"}, "response_key": "data",
            "raw_columns": ["open_value", "low_value", "high_value", "close_value", "change_value", "change_percent",
                            "date_gregorian", "date_jalali"],
            "clean_columns": ["open_value", "low_value", "high_value", "close_value", "date_g", "date_j"],
            "date_column_raw": "date_gregorian", "date_column_clean": "date_g", "date_converter": "gregorian",
            "numeric_columns": ["open_value", "low_value", "high_value", "close_value"], "numeric_cleaner": "comma"},
           {"name": "usd_official", "table_name": "usd_official_rates",
            "base_url": "https://api.tgju.org/v1/market/indicator/summary-table-data/bank_usd",
            "pagination": {"offset_param": "start", "limit_param": "length"}, "response_key": "data",
            "raw_columns": ["open_value", "low_value", "high_value", "close_value", "change_value", "change_percent",
                            "date_gregorian", "date_jalali"],
            "clean_columns": ["open_value", "low_value", "high_value", "close_value", "date_g", "date_j"],
            "date_column_raw": "date_gregorian", "date_column_clean": "date_g", "date_converter": "gregorian",
            "numeric_columns": ["open_value", "low_value", "high_value", "close_value"], "numeric_cleaner": "comma"},
           {"name": "stock_index", "table_name": "tehran_stock_indices",
            "base_url": "https://api.tgju.org/v1/stocks/instrument/history-data/ش-کل-بورس",
            "pagination": {"offset_param": "start", "limit_param": "length"}, "response_key": "data",
            "raw_columns": ["date_j", "close_value", "low_value", "high_value"],
            # exception: date_j needs to be converted to date_g since this source does not take it
            "clean_columns": ["date_g", "date_j", "close_value", "low_value", "high_value"],
            "date_column_raw": "date_j", "date_column_clean": "date_g", "date_converter": "jalali",
            "numeric_columns": ["close_value", "low_value", "high_value"], "numeric_cleaner": "million"}]

# ====================================================================
# Project Paths
# ====================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"

LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ====================================================================
# Logging Configuration
# ====================================================================

logging.basicConfig(filename=LOGS_DIR / "market_etl.log", level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s", )


# ====================================================================
# Helper Functions
# ====================================================================
def remove_html_tags(df):
    html_cols = [col for col in df.columns if df[col].astype(str).str.contains(r"<[^>]+>", regex=True, na=False).any()]

    for col in html_cols:
        df[col] = [re.sub(r"<[^>]*>", "", str(value)).strip() for value in df[col]]

    return df


def convert_value(value):
    value = str(value).strip()
    if "میلیون" in value:
        value = value.replace("میلیون", "").strip()
        return float(value.replace(",", "")) * 1_000_000

    return float(value.replace(",", ""))


def clean_numeric(df, columns, method):
    for col in columns:
        if method == "comma":
            df[col] = (df[col].astype(str).str.replace(",", "", regex=False))
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif method == "million":
            df[col] = df[col].apply(convert_value)
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def convert_date(df, column, method):
    if method == "gregorian":
        df[column] = pd.to_datetime(df[column], errors="coerce")
    elif method == "jalali":
        jalali_dates = df[column].apply(lambda x: jdatetime.datetime.strptime(str(x), "%Y/%m/%d"))
        df["date_g"] = jalali_dates.apply(lambda x: x.togregorian())
        df["date_g"] = pd.to_datetime(df["date_g"])

    return df


try:
    # ====================================================================
    # Process Each Data Source
    # ====================================================================
    logging.info("========== ETL START ==========")
    for source in sources:

        # print(f"\nProcessing: {source['table_name']}")
        logging.info(f"Processing: {source['table_name']}")

        length = 100
        offset = 0

        all_rows = []

        # ====================================================================
        # Extract Data
        # ====================================================================
        while True:
            params = {"lang": "fa", source["pagination"]["offset_param"]: offset,
                      source["pagination"]["limit_param"]: length, "draw": 1, }
            if source["name"] == "stock_index":
                params["market"] = 'index'

            response = requests.get(source["base_url"], params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            if source["response_key"] == "data":
                rows = result.get("data", [])
            elif source["response_key"] == "results":
                if isinstance(result, list):
                    rows = result
                else:
                    rows = result.get("results", [])
            else:
                rows = []
            if not rows:
                break
            all_rows.extend(rows)
            offset += length

        # print(f"Total records: {len(all_rows)}")
        logging.info(f"Total records: {len(all_rows)}")

        # ====================================================================
        # Create Raw DataFrame
        # ====================================================================
        raw_df = pd.DataFrame(all_rows, columns=source["raw_columns"])

        # ====================================================================
        # Raw Date Conversion
        # ====================================================================
        raw_df = convert_date(raw_df, source["date_column_raw"], source["date_converter"])

        # ====================================================================
        # Source-specific preprocessing
        # ====================================================================
        if source["table_name"] == "tehran_stock_indices":
            source['date_column_raw'] = 'date_g'

        # ====================================================================
        # Incremental Load - Raw Data
        # ====================================================================
        query_raw = text(f"""
            SELECT MAX({source["date_column_raw"]})
            FROM raw.{source["table_name"]}
            """)

        with engine.connect() as connection:
            last_raw_date = connection.execute(query_raw).scalar()

        if last_raw_date is None:
            raw_new = raw_df.copy()
        else:
            raw_new = raw_df[raw_df[source["date_column_raw"]] > pd.Timestamp(last_raw_date)].copy()

        if not raw_new.empty:
            raw_new["load_timestamp"] = datetime.now()
            raw_new.to_sql(name=source["table_name"], con=engine, schema="raw", if_exists="append", index=False,
                           chunksize=1000, )
            # print("Raw data inserted.")
            logging.info("Raw data inserted.")
        else:
            # print("No new raw data.")
            logging.info("No new raw data.")

        # ====================================================================
        # Build Clean DataFrame
        # ====================================================================
        if source["name"] == "stock_index":
            df = raw_df.copy()
        else:
            columns = source["clean_columns"]
            df = pd.DataFrame([row[:4] + row[6:] for row in all_rows], columns=columns)

        # ====================================================================
        # Remove HTML Tags
        # ====================================================================
        df = remove_html_tags(df)

        # ====================================================================
        # Date Processing
        # ====================================================================
        df["date_g"] = pd.to_datetime(df["date_g"], errors="coerce")

        # ====================================================================
        # Numeric Cleaning
        # ====================================================================
        df = clean_numeric(df, source["numeric_columns"], source["numeric_cleaner"])

        # ====================================================================
        # Incremental Load - Clean Data
        # ====================================================================
        query = text(f"""
            SELECT MAX({source["date_column_clean"]}) AS last_date
            FROM dbo.{source["table_name"]}
            """)

        with engine.connect() as connection:
            last_date = connection.execute(query).scalar()
        if last_date is None:
            df_new = df.copy()
        else:
            df_new = df[df[source["date_column_clean"]] > pd.Timestamp(last_date)].copy()
            # print(f"New records: {len(df_new)}")
            logging.info(f"New records: {len(df_new)}")

        # ====================================================================
        # Load Clean Data into SQL Server
        # ====================================================================
        if not df_new.empty:
            df_new.to_sql(name=source["table_name"], con=engine, schema="dbo", if_exists="append", index=False,
                          chunksize=1000, )
            # print("Clean data inserted.")
            logging.info("Cleaned data inserted.")
        else:
            # print("No new clean data.")
            logging.info("No new clean data.")
    # print("\nETL process completed successfully.")
    logging.info("========== ETL SUCCESS ==========")
except Exception as e:
    logging.exception("========== ETL FAILED ==========")
    logging.exception(e)
    raise
