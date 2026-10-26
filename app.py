
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from books import count_unique_authors, find_bestseller_author
from constants import DATA_DIR, STORES_PATH
from orders import calculate_paid_price_orders
from users import find_most_spent_customer, find_unique_users


def daily_revenue(orders):
    revenue = (
        orders.dropna(subset=["date", "paid_price"])
        .groupby("date", as_index=False)["paid_price"].sum()
        .rename(columns={"paid_price": "daily_revenue"})
        .sort_values("date", kind="stable")
        .reset_index(drop=True)
    )
    revenue["daily_revenue"] = revenue["daily_revenue"].round(2)
    return revenue


def top_five_revenue_days(revenue):
    return (
        revenue.sort_values(["daily_revenue", "date"], ascending=[False, True], kind="stable")
        .head(5)
        .rename(columns={"date": "Date", "daily_revenue": "Daily revenue ($)"})
        .reset_index(drop=True)
    )


def create_daily_revenue_figure(revenue, store):
    fig, axis = plt.subplots(figsize=(12, 5))
    axis.plot(revenue["date"], revenue["daily_revenue"], color="#2563eb", linewidth=2)
    axis.fill_between(revenue["date"], revenue["daily_revenue"], color="#bfdbfe", alpha=0.45)
    axis.set(title=f"Daily revenue — {store}", xlabel="Date", ylabel="Revenue (USD)")
    locator = mdates.AutoDateLocator()
    axis.xaxis.set_major_locator(locator)
    axis.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    axis.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    return fig


def get_store_statistics(store):
    if store not in STORES_PATH:
        raise ValueError(f"Unknown store: {store}")
    directory = Path(DATA_DIR) / store
    orders = calculate_paid_price_orders(directory / "orders.parquet")
    revenue = daily_revenue(orders)
    users = find_unique_users(directory / "users.csv")
    return {
        "daily_revenue": revenue,
        "top_five_days": top_five_revenue_days(revenue),
        "unique_users": int(users["real_user_id"].nunique()),
        "best_customers": find_most_spent_customer(directory),
        "unique_author_sets": count_unique_authors(directory / "books.yaml"),
        "popular_author_sets": find_bestseller_author(directory),
        "valid_revenue_orders": int(orders["paid_price"].notna().sum()),
        "excluded_revenue_orders": int(orders[["paid_price", "date"]].isna().any(axis=1).sum()),
    }


def main():
    for store in STORES_PATH:
        statistics = get_store_statistics(store)
        print(f"{store}: {statistics['unique_users']} real users; {statistics['unique_author_sets']} author sets")
        print(statistics["top_five_days"].to_string(index=False))


if __name__ == "__main__":
    main()
