from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

import pandas as pd

from constants import DATA_DIR, STORES_PATH


USD_PER_EUR = Decimal("1.20")


def _default_orders_path():
    return DATA_DIR / STORES_PATH[0] / "orders.parquet"


def analyze_duplicate_orders_parquet(path=None):
    orders = pd.read_parquet(path or _default_orders_path(), engine="pyarrow")
    orders.attrs["identical_duplicate_rows"] = int(orders.duplicated().sum())
    orders.attrs["repeated_order_ids"] = int(orders.duplicated("id").sum())
    return orders


def clean_quantity_orders(path=None):
    orders = analyze_duplicate_orders_parquet(path).copy()
    quantities = pd.to_numeric(orders["quantity"], errors="coerce")
    valid = quantities.notna() & quantities.gt(0) & quantities.mod(1).eq(0)
    orders = orders.loc[valid].copy()
    orders["quantity"] = quantities.loc[valid].astype("int64")
    return orders


def convert_to_usd(value):
    if pd.isna(value):
        return None
    text = str(value).strip().upper()
    currencies = re.findall(r"EUR|USD|€|\$", text)
    kinds = {"EUR" if token in {"EUR", "€"} else "USD" for token in currencies}
    if len(kinds) != 1:
        return None

    if "¢" in text:
        digit_groups = re.findall(r"\d+", text)
        if len(digit_groups) != 2 or len(digit_groups[1]) != 2:
            return None
        amount_text = f"{digit_groups[0]}.{digit_groups[1]}"
    else:
        number = re.sub(r"EUR|USD|€|\$", "", text).strip()
        match = re.fullmatch(r"(\d+)(?:\.(\d{1,2}))?\.?", number)
        if not match:
            return None
        whole, fraction = match.group(1), match.group(2)
        amount_text = f"{whole}.{fraction or '0'}"
    try:
        amount = Decimal(amount_text)
    except InvalidOperation:
        return None
    if "EUR" in kinds:
        amount *= USD_PER_EUR
    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def normalize_unit_price_orders(path=None):
    orders = clean_quantity_orders(path)
    orders["unit_price_usd"] = orders["unit_price"].map(convert_to_usd)
    return orders


def normalize_date_orders(path=None):
    orders = normalize_unit_price_orders(path)
    normalized = (
        orders["timestamp"].astype("string").str.strip()
        .str.replace(r"(?i)A\.M\.|P\.M\.", lambda match: match.group().replace(".", ""), regex=True)
        .str.replace(";", " ", regex=False).str.replace(",", " ", regex=False)
    )
    orders["parsed_timestamp"] = pd.to_datetime(normalized, format="mixed", errors="coerce")
    orders["date"] = orders["parsed_timestamp"].dt.date
    return orders


def calculate_paid_price_orders(path=None):
    orders = normalize_date_orders(path)
    orders["paid_price"] = (orders["quantity"] * orders["unit_price_usd"]).round(2)
    return orders

