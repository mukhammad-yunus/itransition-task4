import pandas as pd
from itertools import combinations
from pathlib import Path

from constants import DATA_DIR, STORES_PATH
from orders import normalize_unit_price_orders
from networkx.utils.union_find import UnionFind


IDENTITY_FIELDS = ["name", "address", "phone", "email"]


def _default_users_path():
    return DATA_DIR / STORES_PATH[0] / "users.csv"


def _canonical(value):
    if pd.isna(value):
        return None
    return " ".join(str(value).split()).casefold()


def find_unique_users(path=None):
    users = pd.read_csv(path or _default_users_path()).copy()

    uf = UnionFind(range(len(users)))
    found = {}

    for i, row in users.iterrows():
        values = {
            field: _canonical(row[field])
            for field in IDENTITY_FIELDS
        }

        for fields in combinations(IDENTITY_FIELDS, 3):
            signature = tuple(values[field] for field in fields)

            # Do not match records using missing values.
            if None in signature:
                continue

            match = (fields, signature)

            if match in found:
                uf.union(i, found[match])
            else:
                found[match] = i

    users["real_user_id"] = [
        uf[i] for i in range(len(users))
    ]

    return users


def find_most_spent_customer(dir_path=None):
    directory = Path(dir_path or DATA_DIR / STORES_PATH[0])

    users = find_unique_users(directory / "users.csv")

    orders_df = normalize_unit_price_orders(
        path=directory / "orders.parquet"
    ).copy()

    orders_df["paid_price"] = (
        orders_df["quantity"] * orders_df["unit_price_usd"]
    )

    orders_df = orders_df.dropna(subset=["paid_price"])

    purchases = orders_df.merge(
        users[["id", "real_user_id"]],
        how="left",
        left_on="user_id",
        right_on="id",
        validate="many_to_one",
    )

    if purchases["real_user_id"].isna().any():
        raise ValueError(
            f"Some orders in {directory} reference unknown user IDs."
        )

    totals = purchases.groupby(
        "real_user_id",
        as_index=False,
    )["paid_price"].sum()

    if totals.empty:
        return pd.DataFrame(
            columns=["real_user_id", "paid_price", "user_ids"]
        )

    top = totals[
        totals["paid_price"].eq(totals["paid_price"].max())
    ].copy()

    user_ids = (
        users.groupby("real_user_id")["id"]
        .apply(lambda values: sorted(values.tolist()))
        .rename("user_ids")
    )

    result = top.merge(
        user_ids,
        on="real_user_id",
        how="left",
        validate="one_to_one",
    )

    result["paid_price"] = result["paid_price"].round(2)

    return result.reset_index(drop=True)