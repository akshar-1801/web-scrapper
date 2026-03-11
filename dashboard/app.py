import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import os
from ai_helper import AIHelper

# 1. Connect to the Database
db_host = os.getenv('DB_HOST', 'postgres')
db_connection_str = f'postgresql://user:password@{db_host}:5432/prices_db'

try:
    db_connection = create_engine(db_connection_str)
except Exception as e:
    st.error(f"Error connecting to database: {e}")
    st.stop()

# Initialize AI Helper
ai_helper = AIHelper()

st.set_page_config(page_title="Tata 1mg Tracker", layout="wide", page_icon="💊")
st.title("💊 Live Tata 1mg Price Tracker")

# 2. Sidebar - Session & Category Management
st.sidebar.header("🗓️ Scrape Session")

try:
    # Get available scrape sessions (distinct timestamps, rounded to hour)
    session_query = """
    SELECT DISTINCT date_trunc('hour', scraped_at) as session_time 
    FROM prices 
    ORDER BY session_time DESC
    """
    sessions_df = pd.read_sql(session_query, db_connection)
    
    if not sessions_df.empty:
        # Add "All Time" option
        all_time_option = pd.to_datetime("1900-01-01") # Dummy value
        
        session_options = sessions_df['session_time'].tolist()
        
        # Format for display
        display_map = {t: t.strftime('%Y-%m-%d %H:00') for t in session_options}
        display_map[all_time_option] = "All Time (Latest Prices)"
        
        selected_session = st.sidebar.selectbox(
            "Select Scan Session", 
            [all_time_option] + session_options, 
            format_func=lambda x: display_map[x],
            index=0 # Default to All Time
        )
    else:
        st.warning("No data found.")
        st.stop()

    # Function to load data (cached)
    @st.cache_data(ttl=3600)
    def load_data(query):
        return pd.read_sql(query, db_connection)

    # 3. Load Data for Selected Session
    if selected_session == all_time_option:
         # Show latest price for EVERY product found
         where_clause = ""
         title_prefix = "All Time"
    else:
         # Show products scraped in that specific hour window
         where_clause = f"WHERE date_trunc('hour', h.scraped_at) = '{selected_session}'"
         title_prefix = selected_session.strftime('%Y-%m-%d %H:00')

    data_query = f"""
    SELECT DISTINCT ON (p.name) 
        p.name, 
        p.category,
        p.url, 
        p.pack_size,
        p.rating,
        p.rating_count,
        p.image_url,
        p.description,
        p.key_ingredients,
        p.safety_information,
        p.directions_for_use,
        h.price, 
        h.scraped_at
    FROM products p
    JOIN prices h ON p.id = h.product_id
    {where_clause}
    ORDER BY p.name, h.scraped_at DESC;
    """ 
    
    with st.spinner('Fetching latest data...'):
        df = load_data(data_query)
    
    # Cleaning
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
    df['rating_count'] = pd.to_numeric(df['rating_count'], errors='coerce').fillna(0)
    
    # Sidebar - Category Counts
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Categories")
    
    if 'category' in df.columns:
        # Calculate counts
        category_counts = df['category'].value_counts()
        
        # "All" option
        all_count = len(df)
        selected_category = st.sidebar.radio(
            f"Select Category",
            ["All"] + list(category_counts.index),
            format_func=lambda x: f"{x} ({category_counts[x]})" if x != "All" else f"All ({all_count})"
        )
        
        # Filter Logic
        if selected_category != "All":
            filtered_df = df[df['category'] == selected_category]
        else:
            filtered_df = df
    else:
        st.sidebar.warning("Category data missing.")
        filtered_df = df

    # 4. Main View
    col1, col2, col3 = st.columns(3)
    col1.metric("Products Found", len(filtered_df))
    col2.metric("Avg Price", f"₹{filtered_df['price'].mean():.2f}")
    col3.metric("Avg Rating", f"{filtered_df['rating'].mean():.1f} ⭐")
    
    st.markdown("---")

    # 5. Visualizations
    if not filtered_df.empty:
        # Intelligent Brand Extraction
        def extract_brand(name):
            if not isinstance(name, str): return "Unknown"
            
            name_parts = name.split()
            if not name_parts: return "Unknown"
            
            first_word = name_parts[0]
            
            # 1. Known Multi-word Brands
            known_brands = [
                "Tata 1mg", "Dr Batra's", "Organic India", "Mamaearth", 
                "The Man Company", "Wow Skin Science", "Dr. Morepen",
                "Kapiva Ayurveda", "Sri Sri Tattva", "Apollo Pharmacy"
            ]
            for kb in known_brands:
                if name.lower().startswith(kb.lower()):
                    return kb
            
            # 2. Prefix Handling (Dr, St, etc.)
            prefixes = ["Dr", "Dr.", "St", "St.", "Mrs", "Mr"]
            if first_word in prefixes and len(name_parts) > 1:
                return f"{first_word} {name_parts[1]}"
            
            # 3. Default: First Word
            return first_word

        filtered_df['brand'] = filtered_df['name'].apply(extract_brand)
        
        tab1, tab2, tab3 = st.tabs(["📋 Data View", "📈 Market Insights", "🤖 AI Assistant"])
        
        with tab1:
            # Search
            search_term = st.text_input("Search Products", "")
            if search_term:
                display_df = filtered_df[filtered_df['name'].str.contains(search_term, case=False, na=False)]
            else:
                display_df = filtered_df
                
            st.dataframe(
                display_df[['image_url', 'name', 'brand', 'category', 'price', 'rating', 'rating_count', 'pack_size', 'url']],
                column_config={
                    "image_url": st.column_config.ImageColumn("Image"),
                    "url": st.column_config.LinkColumn("Link"),
                    "price": st.column_config.NumberColumn("Price (₹)"),
                    "rating": st.column_config.NumberColumn("Rating", format="%.1f ⭐"),
                },
                use_container_width=True,
                height=600
            )

        with tab2:
            st.header("🧠 Market Intelligence")
            
            # A. Brand Leaderboard
            st.subheader("🏆 Top Brands")
            
            # Sort Option
            rank_metric = st.selectbox(
                "Rank Brands By:",
                ["Product Count (Availability)", "Average Rating (Quality)", "Total Reviews (Popularity)"]
            )
            
            # Group by Brand
            brand_stats = filtered_df.groupby('brand').agg({
                'name': 'count',
                'rating': 'mean',
                'rating_count': 'sum'
            }).reset_index()
            
            # Rename columns
            brand_stats.columns = ['brand', 'count', 'avg_rating', 'total_reviews']
            
            # Sort Logic
            if "Availability" in rank_metric:
                sort_col = 'count'
                x_axis = 'count'
                title = "Top 15 Brands by Product Count"
                color_scale = 'Bluered'
            elif "Quality" in rank_metric:
                # Filter out brands with very few reviews/products to avoid noise
                brand_stats = brand_stats[brand_stats['count'] > 2] 
                sort_col = 'avg_rating'
                x_axis = 'avg_rating'
                title = "Top 15 Brands by Average Rating (min 3 products)"
                color_scale = 'Viridis'
            else:
                sort_col = 'total_reviews'
                x_axis = 'total_reviews'
                title = "Top 15 Brands by Total Reviews"
                color_scale = 'Magma'
                
            brand_stats = brand_stats.sort_values(sort_col, ascending=False).head(15)
            
            fig_brand = px.bar(
                brand_stats, 
                x=x_axis, 
                y='brand', 
                orientation='h', 
                title=title, 
                color=sort_col, 
                color_continuous_scale=color_scale,
                text_auto='.1f' if "Quality" in rank_metric else '.2s'
            )
            fig_brand.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_brand, use_container_width=True)
            
            # B. Category Landscape (Bubble Chart)
            if 'category' in filtered_df.columns:
                st.subheader("🗺️ Category Landscape: Price vs Quality")
                cat_stats = filtered_df.groupby('category').agg({
                    'price': 'mean',
                    'rating': 'mean',
                    'rating_count': 'sum',
                    'name': 'count'
                }).reset_index()
                
                fig_cat = px.scatter(
                    cat_stats, 
                    x='price', 
                    y='rating', 
                    size='rating_count', 
                    color='category', 
                    hover_name='category',
                    size_max=60,
                    title="Category Performance (Size = Total Reviews)",
                    labels={'price': 'Avg Price', 'rating': 'Avg Rating'}
                )
                st.plotly_chart(fig_cat, use_container_width=True)

            # C. Hidden Gems
            st.subheader(f"💎 Hidden Gems in {selected_category}")
            st.caption("High rated (>4.5), Affordable (Below Avg Price), but Undiscovered (<100 reviews)")
            
            avg_price = filtered_df['price'].mean()
            gems = filtered_df[
                (filtered_df['rating'] >= 4.5) & 
                (filtered_df['rating_count'] > 10) & 
                (filtered_df['rating_count'] < 500) &
                (filtered_df['price'] < avg_price)
            ].sort_values('rating', ascending=False).head(8)
            
            if not gems.empty:
                cols = st.columns(4)
                for idx, row in enumerate(gems.itertuples()):
                    with cols[idx % 4]:
                        st.image(row.image_url if row.image_url else "https://via.placeholder.com/150", width=100)
                        st.markdown(f"**[{row.name}]({row.url})**")
                        st.markdown(f"⭐ **{row.rating}** ({int(row.rating_count)})")
                        st.markdown(f"💰 **₹{row.price}**")
                        st.markdown("---")
            else:
                st.info("No hidden gems found with current filters.")

        with tab3:
            st.header("🤖 AI Health Assistant")
            
            if not ai_helper.is_configured():
                st.error("AI API not configured. Please add OPENAI_API_KEY or GOOGLE_API_KEY to `.env` file.")
            else:
                st.markdown("Ask questions or compare products using the power of AI.")
                
                subtab1, subtab2 = st.tabs(["⚖️ Product Comparison", "💬 Health Consultant"])
                
                with subtab1:
                     st.subheader("Compare Products")
                     # Select products
                     product_names = filtered_df['name'].unique().tolist()
                     selected_products_to_compare = st.multiselect("Select products to compare (Max 3)", product_names, max_selections=3)
                     
                     if st.button("Compare Products"):
                         if len(selected_products_to_compare) < 2:
                             st.warning("Please select at least 2 products to compare.")
                         else:
                             # Get details
                             products_data = []
                             for pname in selected_products_to_compare:
                                 row = filtered_df[filtered_df['name'] == pname].iloc[0]
                                 products_data.append(row.to_dict())
                             
                             with st.spinner("Analyzing products..."):
                                 comparison_result = ai_helper.compare_products(products_data)
                                 st.markdown(comparison_result)

                with subtab2:
                    st.subheader("Health Consultation")
                    # Select context
                    st.markdown("Select a product to ask specific questions about it, or leave empty for general queries.")
                    context_product_name = st.selectbox("Select Product Context (Optional)", ["None"] + product_names)
                    
                    user_query = st.chat_input("Ask a question (e.g., 'Is this safe for kids?', 'When should I take this?')")
                    
                    if "messages" not in st.session_state:
                        st.session_state.messages = []

                    for message in st.session_state.messages:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])

                    if user_query:
                        # Display user message
                        with st.chat_message("user"):
                            st.markdown(user_query)
                        st.session_state.messages.append({"role": "user", "content": user_query})
                        
                        # Get AI response
                        with st.spinner("Consulting AI..."):
                            context = None
                            if context_product_name != "None":
                                context = filtered_df[filtered_df['name'] == context_product_name].iloc[0].to_dict()
                            
                            ai_response = ai_helper.consult_health(user_query, context)
                            
                        # Display AI response
                        with st.chat_message("assistant"):
                            st.markdown(ai_response)
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
