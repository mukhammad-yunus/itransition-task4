import pandas as pd
import yaml
from constants import STORES_PATH
from orders import clean_quantity_orders


def get_books_yaml_df(path=f"data/{STORES_PATH[0]}/books.yaml"):
  with open(path, "r") as file:
    data = yaml.safe_load(file)
  return pd.DataFrame(data)

def count_unique_authors(path=f"data/{STORES_PATH[0]}/books.yaml"):
  books_df = get_books_yaml_df(path=path)

  author_sets = books_df[":author"].apply(
    lambda authors: frozenset(authors.split(", "))
  )

  return author_sets.nunique()

def find_bestseller_author(dir_path=f"data/{STORES_PATH[0]}"):
  orders_df = clean_quantity_orders(path=f"{dir_path}/orders.parquet")

  book_sales = (
    orders_df
    .groupby("book_id", as_index=False)["quantity"]
    .sum()
  )

  books = get_books_yaml_df(path=f"{dir_path}/books.yaml")

  merged_df = pd.merge(
    book_sales,
    books,
    how="left",
    left_on="book_id",
    right_on=":id"
  )

  merged_df["author_set"] = merged_df[":author"].apply(
    lambda x: frozenset(str(x).split(", "))
  )

  author_sales = (
    merged_df
    .groupby("author_set", as_index=False)["quantity"]
    .sum()
  )

  max_sales = author_sales["quantity"].max()

  return author_sales.loc[
    author_sales["quantity"] == max_sales,
    ["author_set", "quantity"]
  ]