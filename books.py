from pathlib import Path

import pandas as pd
import yaml

from constants import DATA_DIR, STORES_PATH
from orders import clean_quantity_orders


def _default_books_path():
    return DATA_DIR / STORES_PATH[0] / "books.yaml"


def get_books_yaml_df(path=None):
    with open(path or _default_books_path(), encoding="utf-8") as file:
        data = yaml.safe_load(file) or []
    return pd.DataFrame(data)


def author_set_key(authors):
    if pd.isna(authors):
        return None
    names = [" ".join(name.split()) for name in str(authors).split(",") if name.strip()]
    return tuple(sorted({name.casefold() for name in names})) or None


def author_set_label(authors):
    if pd.isna(authors):
        return None
    names = [" ".join(name.split()) for name in str(authors).split(",") if name.strip()]
    return " & ".join(sorted(set(names), key=str.casefold)) or None


def count_unique_authors(path=None):
    books = get_books_yaml_df(path)
    return int(books[":author"].map(author_set_key).dropna().nunique())


def find_bestseller_author(dir_path=None):
    directory = Path(dir_path or (DATA_DIR / STORES_PATH[0]))
    orders = clean_quantity_orders(directory / "orders.parquet")
    books = get_books_yaml_df(directory / "books.yaml")
    sales = orders.groupby("book_id", as_index=False)["quantity"].sum()
    merged = sales.merge(books[[":id", ":author"]], how="left", left_on="book_id", right_on=":id")
    merged["author_set"] = merged[":author"].map(author_set_key)
    merged = merged.dropna(subset=["author_set"])
    if merged.empty:
        return pd.DataFrame(columns=["author_set", "authors", "books_sold"])

    author_sales = merged.groupby("author_set", as_index=False)["quantity"].sum()
    labels = merged.drop_duplicates("author_set").set_index("author_set")[":author"].map(author_set_label)
    author_sales["authors"] = author_sales["author_set"].map(labels)
    author_sales = author_sales.rename(columns={"quantity": "books_sold"})
    maximum = author_sales["books_sold"].max()
    return author_sales.loc[author_sales["books_sold"].eq(maximum), ["author_set", "authors", "books_sold"]].sort_values("authors", kind="stable").reset_index(drop=True)
