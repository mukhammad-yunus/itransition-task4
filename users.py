import pandas as pd
from itertools import combinations
from constants import STORES_PATH
from orders import normalize_unit_price_orders
from networkx.utils.union_find import UnionFind


def find_unique_users(path=f"data/{STORES_PATH[0]}/users.csv"):
    users = pd.read_csv(path)
    columns = ["name", "address", "phone", "email"]

    uf = UnionFind(range(len(users)))
    found = {}

    for i, row in users.iterrows():
        for fields in combinations(columns, 3):
            values = tuple(row[field] for field in fields)

            # Do not match records using missing values.
            if any(pd.isna(value) for value in values):
                continue

            match = (fields, values)

            if match in found:
                uf.union(i, found[match])
            else:
                found[match] = i

    users["real_user_id"] = [uf[i] for i in range(len(users))]

    return users

def find_most_spent_customer(dir_path=f"data/{STORES_PATH[0]}"):
    users = find_unique_users(f"{dir_path}/users.csv")

    orders_df = normalize_unit_price_orders(
        path=f"{dir_path}/orders.parquet"
    )

    orders_df["paid_price"] = (
        orders_df["quantity"] * orders_df["unit_price_usd"]
    )

    user_purchase = (
        orders_df
        .groupby("user_id", as_index=False)["paid_price"]
        .sum()
    )

    user_purchase = user_purchase.merge(
        users[["id", "real_user_id"]],
        how="left",
        left_on="user_id",
        right_on="id",
        validate="many_to_one"
    )

    if user_purchase["real_user_id"].isna().any():
        raise ValueError(
            f"Some orders in {dir_path} reference unknown user IDs."
        )

    customer_purchase = (
        user_purchase
        .groupby("real_user_id", as_index=False)["paid_price"]
        .sum()
    )

    if customer_purchase.empty:
        return pd.DataFrame(
            columns=["real_user_id", "paid_price", "user_ids"]
        )

    max_purchase = customer_purchase["paid_price"].max()

    best_customers = customer_purchase[
        customer_purchase["paid_price"] == max_purchase
    ]

    best_customer_ids = (
        users[
            users["real_user_id"].isin(
                best_customers["real_user_id"]
            )
        ]
        .groupby("real_user_id")["id"]
        .apply(list)
        .rename("user_ids")
    )

    result = best_customers.merge(
        best_customer_ids,
        on="real_user_id",
        how="left",
        validate="one_to_one"
    )

    return result