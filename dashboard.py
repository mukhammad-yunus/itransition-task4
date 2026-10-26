import streamlit as st
from google import genai

from app import create_daily_revenue_figure, get_store_statistics
from constants import STORES_PATH
from chat import ask_gemini

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

st.set_page_config(page_title="Bookstore Dashboard", layout="wide")


@st.cache_data(show_spinner="Calculating store analytics…")
def load_statistics(store):
    return get_store_statistics(store)


st.title("Bookstore Analytics Dashboard")
st.caption("Revenue, customer, and book statistics are calculated independently for each store.")
store = st.selectbox("Select a store", STORES_PATH)
statistics = load_statistics(store)

revenue_tab, customers_tab, books_tab, ai_chat = st.tabs(["Revenue", "Customers", "Books", "AI chat"])

with revenue_tab:
    st.subheader("Revenue analysis")
    left, right = st.columns([2, 1])
    with left:
        st.pyplot(create_daily_revenue_figure(statistics["daily_revenue"], store), width="stretch")
    with right:
        total = statistics["daily_revenue"]["daily_revenue"].sum()
        st.metric("Total revenue", f"${total:,.2f}")
        st.metric("Orders included in revenue", statistics["valid_revenue_orders"])
        if statistics["excluded_revenue_orders"]:
            st.info(f"{statistics['excluded_revenue_orders']} orders were excluded because their price or timestamp could not be validated.")
    st.subheader("Top five days by revenue")
    st.dataframe(statistics["top_five_days"], hide_index=True, width="stretch",
                 column_config={"Daily revenue ($)": st.column_config.NumberColumn(format="$%.2f")})

with customers_tab:
    st.subheader("Customer analysis")
    st.metric("Unique real users", statistics["unique_users"])
    st.caption("Records are linked when three of name, address, phone, and email match.")
    st.subheader("Best customer(s) by total spending")
    best_customers = statistics["best_customers"].rename(columns={"paid_price": "Total spent ($)", "user_ids": "Original user IDs"})
    st.dataframe(best_customers[["Total spent ($)", "Original user IDs"]], hide_index=True, width="stretch",
                 column_config={"Total spent ($)": st.column_config.NumberColumn(format="$%.2f")})

with books_tab:
    st.subheader("Book analysis")
    st.metric("Unique author sets", statistics["unique_author_sets"])
    st.caption("Author order does not affect an author-set identity.")
    st.subheader("Most popular author set(s)")
    popular = statistics["popular_author_sets"][["authors", "books_sold"]].rename(columns={"authors": "Author set", "books_sold": "Books sold"})
    st.dataframe(popular, hide_index=True, width="stretch")

with ai_chat:
    st.subheader("Ask your data")

    question = st.text_input(
        "Ask a question about the selected store"
    )

    if st.button("Ask AI") and question.strip():
        with st.spinner("Analyzing your question..."):
            try:
                answer = ask_gemini(
                    client=client,
                    question=question,
                    store_name=store,
                    statistics=statistics,
                )

                st.markdown(answer)

            except Exception as exc:
                st.error(f"Could not get an AI response: {exc}")