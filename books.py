import pandas as pd
import yaml
from constants import STORES_PATH


def count_unique_authors(path=f"data/{STORES_PATH[0]}/books.yaml"):
  with open(path, "r") as file:
    data = yaml.safe_load(file)

  books_df = pd.DataFrame(data)

  author_sets = books_df[":author"].apply(
    lambda authors: frozenset(authors.split(", "))
  )

  return author_sets.nunique()
