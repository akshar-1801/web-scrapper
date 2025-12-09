import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# 1. Connect to the Database
# NOTE: We use "postgres" as the host name because we are inside the Docker network
db_connection_str = 'postgresql://user:password@postgres:5432/prices_db'
db_connection = create_engine(db_connection_str)

st.title("📚 Live Price Tracker Dashboard")
st.markdown("Monitoring prices from **Books to Scrape**")

# 2. Load Data
try:
    # NEW QUERY (Shows only the latest price for each book)
    query = """
    SELECT DISTINCT ON (p.name) 
        p.name, 
        p.url, 
        h.price, 
        h.scraped_at
    FROM products p
    JOIN prices h ON p.id = h.product_id
    ORDER BY p.name, h.scraped_at DESC;
    """ 
    df = pd.read_sql(query, db_connection)
    
    # 3. KPI Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Books Tracked", len(df['url'].unique()))
    col2.metric("Average Price", f"£{df['price'].mean():.2f}")
    col3.metric("Most Expensive", f"£{df['price'].max()}")

    # 4. Visualization: Top 10 Most Expensive Books
    st.subheader("💰 Top 10 Most Expensive Books")
    top_books = df.nlargest(10, 'price')
    fig = px.bar(top_books, x='name', y='price', title="Price Distribution", color='price')
    st.plotly_chart(fig)

    # 5. Raw Data Table
    st.subheader("Recent Data Feed")
    st.dataframe(df)

except Exception as e:
    st.error(f"Error connecting to database: {e}")