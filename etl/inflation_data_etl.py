import logging
import os
import re
from pathlib import Path
from urllib.parse import quote_plus
from urllib.parse import urljoin

import jdatetime
import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.dialects.mssql import TINYINT
from sqlalchemy.types import NVARCHAR, SMALLINT, DATE

urllib3.disable_warnings()
# ====================================================================
# Project Paths
# ====================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "raw_data"
LOGS_DIR = BASE_DIR / "logs"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
# ====================================================================
# Extract Configuration
# ====================================================================
page_url = "https://amar.org.ir/prices"
target_id = "28579"
download_dir = "../raw_data"
os.makedirs(download_dir, exist_ok=True)

# ====================================================================
# Database Configuration
# ====================================================================
server = r"localhost"
database = "ecoMonitoringDB"
connection_string = ("DRIVER={ODBC Driver 18 for SQL Server};"
                     f"SERVER={server};"
                     f"DATABASE={database};"
                     "Trusted_Connection=yes;"
                     "TrustServerCertificate=yes;")
engine = create_engine("mssql+pyodbc:///?odbc_connect=" + quote_plus(connection_string))

# ====================================================================
# Logging Configuration
# ====================================================================
os.makedirs("../logs", exist_ok=True)

logging.basicConfig(filename="logs/inflation_etl.log", level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s", encoding="utf-8", )


# ====================================================================
# Helper Functions
# ====================================================================
def download_inflation_excel_file():
    session = requests.Session()
    session.verify = False
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    response = session.get(page_url, timeout=60)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    modal = soup.find(id=f"id{target_id}")
    if modal is None:
        logging.exception(f"Target id {target_id} not found")
        raise ValueError(f"Target id {target_id} not found")

    download_link = modal.find("a", class_="downloadable")
    if download_link is None:
        logging.exception(f"download link no found for id {target_id}")
        raise ValueError(f"download link no found for id {target_id}")

    file_url = urljoin(page_url, download_link["href"])
    file_name = file_url.split("/")[-1]
    file_path = download_dir / file_name

    # print(f"downloading {file_name}")
    logging.info(f"downloading {file_name}")
    file_response = session.get(file_url, timeout=120)
    file_response.raise_for_status()

    # Save downloaded file
    with open(file_path, "wb") as file:
        file.write(file_response.content)
    # print("downloaded")
    logging.info("downloaded")

    return file_path


def normalize_fa_text(value):
    if pd.isna(value):
        return None
    value = str(value)
    # replace arabic letters to persian
    value = value.replace("ي", "ی")
    value = value.replace("ك", "ک")
    # remove unwanted spaces around the names
    value = value.strip()
    # remove extra spaces
    value = re.sub(r"\s+", " ", value)
    return value


def split_group(value):
    value = str(value).strip()
    match = re.match(r"^(\d+)\s*-\s*(.+)$", value)
    if match:
        return match.group(1), match.group(2).strip()
    return None, value


def read_monthly_sheet(excel_path, sheet_name, month_map):
    df_raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

    # Extract year row
    year_row = df_raw.iloc[1].copy()
    year_row = year_row.ffill().infer_objects(copy=False)

    # Extract month row
    month_row = df_raw.iloc[2].copy()

    # Generate column names
    new_columns = []
    for column_index in range(df_raw.shape[1]):
        # First column contains group names
        if column_index == 0:
            new_columns.append("group_name")
        else:
            year = year_row.iloc[column_index]
            month = month_row.iloc[column_index]
            new_columns.append(f"{year}_{month}")

    df_data = df_raw.iloc[3:].copy()
    df_data.columns = new_columns

    # Drop empty columns (no data has entered)
    df_data = df_data.dropna(axis=1, how="all")

    # Convert wide format to long format
    df_long = df_data.melt(id_vars="group_name", var_name="period", value_name="raw_value")

    # Extract year and month
    df_long[["year", "month_name"]] = (df_long["period"].str.split("_", n=1, expand=True))
    df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
    df_long["month"] = (df_long["month_name"].map(month_map))

    df_long = df_long[["group_name", "year", "month", "raw_value"]]
    df_long = df_long.dropna(subset=["group_name", "year", "month"])
    df_long["year"] = (df_long["year"].astype("int16"))
    df_long["month"] = (df_long["month"].astype("int8"))
    df_long["raw_value"] = (df_long["raw_value"].astype("string"))

    return df_long


def load_to_raw(df_long, table_name):
    key_columns = ["group_name", "year", "month"]

    # Load existing keys
    existing_query = f"""
    SELECT
        group_name,
        [year],
        [month]
    FROM raw.{table_name}
    """
    df_existing = pd.read_sql(existing_query, con=engine)

    # Keep only new records
    df_new = df_long.merge(df_existing, on=key_columns, how="left", indicator=True)
    df_new = (df_new[df_new["_merge"] == "left_only"].drop(columns="_merge"))
    # print(table_name, " New raw records: ", len(df_new))
    logging.info(f"New raw records: {len(df_new)}")

    if not df_new.empty:
        df_new.to_sql(name=table_name, con=engine, schema="raw", if_exists="append", index=False, chunksize=1000,
                      dtype={"group_name": NVARCHAR(500), "year": SMALLINT(), "month": TINYINT(),
                             "raw_value": NVARCHAR(100)})
        # print("Raw inserted.")
        logging.info("Raw inserted.")

    else:
        # print("No new raw data.")
        logging.info("No new raw data.")


def prepare_dbo(df_long):
    df_dbo = df_long.copy()

    # Split group code and Persian name
    split_result = (df_dbo["group_name"].apply(split_group).apply(pd.Series))
    split_result.columns = ["group_code", "group_name_fa"]
    df_dbo = pd.concat([df_dbo, split_result], axis=1)

    # Load group name mapping
    df_mapping = pd.read_sql("""
        SELECT
            group_name_fa,
            group_name_en
        FROM dbo.cpi_group_mapping
        """, con=engine)

    # Normalize Persian text before merge
    df_dbo["group_name_fa"] = df_dbo["group_name_fa"].apply(normalize_fa_text)
    df_mapping["group_name_fa"] = df_mapping["group_name_fa"].apply(normalize_fa_text)

    df_dbo = df_dbo.merge(df_mapping, on="group_name_fa", how="left")

    # Convert values to numeric
    df_dbo["value"] = pd.to_numeric(df_dbo["raw_value"], errors="coerce")
    df_dbo = df_dbo[["group_code", "group_name_fa", "group_name_en", "year", "month", "value"]]

    df_dbo = create_date_columns(df_dbo)
    df_dbo = df_dbo[["group_code", "group_name_fa", "group_name_en", "year", "month", "date_j", "date_g", "value"]]

    return df_dbo


def create_date_columns(df):
    def convert_date(row):
        year = int(row["year"])
        month = int(row["month"])
        # set month last day
        if month <= 6:
            day = 31
        elif month <= 11:
            day = 30
        else:
            # esfand
            day = 29
        jalali_date = f"{year:04d}-{month:02d}-{day:02d}"
        gregorian_date = jdatetime.date(year, month, day).togregorian()
        return pd.Series([jalali_date, gregorian_date])

    df[["date_j", "date_g"]] = df.apply(convert_date, axis=1)

    return df


def load_to_dbo(df_long, table_name):
    # Load existing keys
    existing_query = f"""
    SELECT
        group_code,
        group_name_fa,
        [year],
        [month]
    FROM dbo.{table_name}
    """
    df_existing = pd.read_sql(existing_query, con=engine)

    # Keep only new records
    df_new = df_long.merge(df_existing, on=["group_code", "group_name_fa", "year", "month"], how="left", indicator=True)
    df_new = (df_new[df_new["_merge"] == "left_only"].drop(columns="_merge"))

    # print(table_name, "new dbo records:", len(df_new))
    logging.info(f"New dbo records: {len(df_new)}")

    if not df_new.empty:

        df_new.to_sql(name=table_name, con=engine, schema="dbo", if_exists="append", index=False, chunksize=1000,
                      dtype={"group_code": NVARCHAR(20), "group_name_fa": NVARCHAR(500), "group_name_en": NVARCHAR(500),
                             "year": SMALLINT(), "month": TINYINT(), "date_j": NVARCHAR(10), "date_g": DATE()})

        # print("Dbo inserted.")
        logging.info("Dbo inserted.")

    else:
        # print("No new dbo data.")
        logging.info("No new dbo data.")


def main():
    try:
        logging.info("========== ETL START ==========")
        # Download Source File
        file_path = download_inflation_excel_file()

        # Load Excel workbook
        excel_file = pd.ExcelFile(file_path)

        # Sheets Configuration
        sheets_config = [{"sheet": excel_file.sheet_names[2], "table": "monthly_cpi_main_group"},
                         {"sheet": excel_file.sheet_names[3], "table": "monthly_inflation_main_group"},
                         {"sheet": excel_file.sheet_names[4], "table": "monthly_point_inflation_main_group"},
                         {"sheet": excel_file.sheet_names[5], "table": "monthly_annual_inflation_main_group"}, ]

        month_mapping = {"فروردین": 1, "اردیبهشت": 2, "خرداد": 3, "تیر": 4, "مرداد": 5, "شهریور": 6, "مهر": 7,
                         "آبان": 8, "آذر": 9, "دی": 10, "بهمن": 11, "اسفند": 12}

        # Process each worksheet
        for item in sheets_config:
            # print("\nProcessing:", item["sheet"])
            logging.info(f"Processing: {item['table']}")
            long_df = read_monthly_sheet(file_path, item["sheet"], month_mapping)
            load_to_raw(long_df, item["table"])
            dbo_df = prepare_dbo(long_df)
            load_to_dbo(dbo_df, item["table"])
        # print("ALL DONE")
        logging.info("========== ETL SUCCESS ==========")
    except Exception as e:
        logging.exception("========== ETL FAILED ==========")
        logging.exception(e)
        raise


if __name__ == "__main__":
    main()
