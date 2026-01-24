import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# 1. Connect to the Database
# NOTE: We use "postgres" as the host name because we are inside the Docker network
db_connection_str = 'postgresql://user:password@postgres:5432/prices_db'
try:
    db_connection = create_engine(db_connection_str)
except Exception as e:
    st.error(f"Error connecting to database: {e}")
    st.stop()

st.set_page_config(page_title="Tata 1mg Tracker", layout="wide")
st.title("💊 Live Tata 1mg Price Tracker")
st.markdown("Real-time monitoring and analytics for **Tata 1mg** products.")

# 2. Load Data
try:
    # NEW QUERY (Shows only the latest price for each product)
    query = """
    SELECT DISTINCT ON (p.name) 
        p.name, 
        p.url, 
        p.pack_size,
        p.rating,
        p.rating_count,
        p.image_url,
        h.price, 
        h.scraped_at
    FROM products p
    JOIN prices h ON p.id = h.product_id
    ORDER BY p.name, h.scraped_at DESC;
    """ 
    df = pd.read_sql(query, db_connection)
    
    # 3. Data Cleaning & Preprocessing
    # Convert numeric columns that might be text
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    df['rating_count'] = pd.to_numeric(df['rating_count'], errors='coerce')
    df['scraped_at'] = pd.to_datetime(df['scraped_at'])
    
    # Fill NaN for visualization safety
    df['rating'].fillna(0, inplace=True)
    df['rating_count'].fillna(0, inplace=True)
    df['price'].fillna(0, inplace=True)

    # 4. Sidebar Filters
    st.sidebar.header("🔍 Filters")
    
    # Price Range Slider
    if not df.empty:
        min_price, max_price = int(df['price'].min()), int(df['price'].max())
        price_range = st.sidebar.slider("Price Range (₹)", min_price, max_price, (min_price, max_price))
        
        # Rating Range Slider
        min_rating, max_rating = float(df['rating'].min()), float(df['rating'].max())
        rating_range = st.sidebar.slider("Rating Range", min_rating, max_rating, (min_rating, max_rating))
        
        # Apply Filters
        filtered_df = df[
            (df['price'].between(price_range[0], price_range[1])) & 
            (df['rating'].between(rating_range[0], rating_range[1]))
        ]
    else:
        filtered_df = df

    # 5. KPI Metrics
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products", len(filtered_df))
    col2.metric("Avg Price", f"₹{filtered_df['price'].mean():.2f}")
    col3.metric("Avg Rating", f"{filtered_df['rating'].mean():.1f} ⭐")
    col4.metric("Total Reviews", f"{int(filtered_df['rating_count'].sum()):,}")

    st.markdown("---")

    # 6. Advanced Visualizations
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("💰 Price Distribution")
        fig_hist = px.histogram(filtered_df, x='price', nbins=20, title="Price Frequency", color_discrete_sequence=['#1f77b4'])
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with col_chart2:
        st.subheader("⭐ Price vs. Rating")
        fig_scatter = px.scatter(
            filtered_df, 
            x='price', 
            y='rating', 
            size='rating_count', 
            hover_data=['name'],
            title="Does Price correlate with Rating?",
            color='rating',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.subheader("🔥 Most Popular Products (by Review Count)")
    top_popular = filtered_df.nlargest(10, 'rating_count')
    fig_bar = px.bar(
        top_popular, 
        x='name', 
        y='rating_count', 
        color='price', 
        title="Top 10 Reviewed Products",
        labels={'rating_count': 'Review Count', 'name': 'Product Name'}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # 7. Raw Data Table with Images
    st.subheader("📋 Product List")
    # Show image if available
    st.dataframe(
        filtered_df[['name', 'price', 'rating', 'rating_count', 'pack_size', 'url']],
        column_config={
            "url": st.column_config.LinkColumn("Product Link")
        },
        use_container_width=True
    )

except Exception as e:
    st.error(f"Error loading data: {e}")