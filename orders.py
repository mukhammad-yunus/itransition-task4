import pandas as pd
import re
import dateparser
from constants import STORES_PATH

def analyze_duplicate_orders_parquet(path=f"data/{STORES_PATH[0]}/orders.parquet"):
    orders_original_df = pd.read_parquet(path, engine="pyarrow")
    print("Analysis started...")
    identical_rows = orders_original_df[
        orders_original_df.duplicated(keep=False)
    ]

    duplicate_ids = orders_original_df[
        orders_original_df.duplicated(subset=["id"], keep=False)
    ]

    print("Completely identical rows:", len(identical_rows))
    print("Rows with repeated order IDs:", len(duplicate_ids))

    if not identical_rows.empty:
        print(identical_rows)

    if not duplicate_ids.empty:
        print(duplicate_ids)

    return orders_original_df

def clean_quantity_orders(path=f"data/{STORES_PATH[0]}/orders.parquet"):
    orders_df = analyze_duplicate_orders_parquet(path=path)
    print("Quantity cleaning started...")
    numeric_values = pd.to_numeric(orders_df["quantity"], errors="coerce")

    valid = (
        orders_df["quantity"].notna()
        & numeric_values.notna()
        & numeric_values.gt(0)
        & numeric_values.mod(1).eq(0)
    )

    orders_df = orders_df.loc[valid].copy()
    orders_df["quantity"] = numeric_values.loc[valid]

    return orders_df

def convert_to_usd(value):
    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    if "€" in value or "EUR" in value:
        currency = "EUR"
    elif "$" in value or "USD" in value:
        currency = "USD"
    else:
        return None

    cents_format = re.fullmatch(
        r"\s*(?:EUR|USD)?\s*(\d+)\s*[€$]\s*(\d{2})\s*¢\s*"
        r"|\s*[€$]\s*(\d+)\s*¢\s*(\d{2})\s*"
        r"|\s*(\d+)\s*[€$]\s*(\d{2})\s*¢\s*",
        value
    )

    if cents_format:
        groups = cents_format.groups()
        if groups[0] is not None:
            amount = float(f"{groups[0]}.{groups[1]}")
        elif groups[2] is not None:
            amount = float(f"{groups[2]}.{groups[3]}")
        else:
            amount = float(f"{groups[4]}.{groups[5]}")
    else:
        cleaned = re.sub(r"EUR|USD|€|\$", "", value).strip()

        if not re.fullmatch(r"\d+(?:\.\d{1,2})?", cleaned):
            return None

        amount = float(cleaned)

    if currency == "EUR":
        amount *= 1.2

    return round(amount, 2)
def normalize_unit_price_orders(path=f"data/{STORES_PATH[0]}/orders.parquet"):
    orders_df = clean_quantity_orders(path=path)
    print("Normalizing unit_price started...")
    orders_df["unit_price_usd"] = orders_df["unit_price"].apply(convert_to_usd)
    return orders_df

def normalize_date_orders(path=f"data/{STORES_PATH[0]}/orders.parquet"):
    orders_df = normalize_unit_price_orders(path=path)
    print("Timestamp normalizing started...")
    orders_df["date"] = orders_df["timestamp"].apply(
        lambda x: dateparser.parse(str(x)) if pd.notna(x) else pd.NaT
    )

    orders_df["date"] = pd.to_datetime(orders_df["date"]).dt.date

    return orders_df

def calculate_paid_price_orders(path=f"data/{STORES_PATH[0]}/orders.parquet"):
    orders_df = normalize_date_orders(path=path)
    orders_df["paid_price"] = orders_df["quantity"] * orders_df["unit_price_usd"]

    return orders_df

