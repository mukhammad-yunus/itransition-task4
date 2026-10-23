import pandas as pd
from itertools import combinations
from constants import STORES_PATH
from networkx.utils.union_find import UnionFind


def count_unique_users(path=f"data/{STORES_PATH[0]}/users.csv"):
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

    unique_users = users["real_user_id"].nunique()

    print(f"Total user records: {len(users)}")
    print(f"Unique real users: {unique_users}")

    return unique_users, users[["id", "real_user_id"]]
