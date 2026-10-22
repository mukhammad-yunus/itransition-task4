from constants import STORES_PATH
from orders import calculate_paid_price_orders
def main(path=f"data/{STORES_PATH[0]}/orders.parquet"):
    orders_df = calculate_paid_price_orders(path=path)
    top_five_dates = (
        orders_df
        .groupby("date", as_index=False)["paid_price"]
        .sum()
        .sort_values(by=["paid_price", "date"], ascending=[False, True])
        .head(5)
        .rename(columns={
        'date': 'Date',
        'paid_price': 'Daily revenue'
    })
    )
    print(top_five_dates)
    
main()