import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2 import service_account
import matplotlib.pyplot as plt
import seaborn as sns

# Set page title
st.title("User Leaderboard")

# Function to fetch data from Google Sheets
@st.cache_data(ttl=600)  # Cache the data for 10 minutes
def fetch_data():
    # Set up Google Sheets API credentials from secrets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    try:
        # Get credentials from Streamlit secrets
        credentials_dict = json.loads(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(
            credentials_dict, 
            scopes=scope
        )
    except Exception as e:
        st.error(f"Error loading credentials from secrets: {e}")
        st.info("If running locally, make sure to set up your .streamlit/secrets.toml file")
        return pd.DataFrame()
    
    client = gspread.authorize(creds)
    
    try:
        # Open the Google Sheet (replace with your sheet name)
        sheet = client.open('UOA Leaderboard').sheet1
        
        # Get all data from the sheet
        data = sheet.get_all_records()
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error fetching data from Google Sheets: {e}")
        return pd.DataFrame()

# Try to fetch data
df = fetch_data()

if not df.empty:
    # Clean and prepare data
    df['feed_won_to_spent_ratio'] = pd.to_numeric(df['feed_won_to_spent_ratio'], errors='coerce')
    df['feed_spent_total'] = pd.to_numeric(df['feed_spent_total'], errors='coerce')
    df['feed_won_total'] = pd.to_numeric(df['feed_won_total'], errors='coerce')
    
    # Calculate rank based on ratio
    df['rank'] = df['feed_won_to_spent_ratio'].rank(ascending=False, method='dense')
    df = df.sort_values('rank')
    
    # Display leaderboard
    st.subheader("Top Performers")
    
    # Select columns to display
    display_cols = ['username', 'feed_won_total', 'feed_spent_total', 'feed_won_to_spent_ratio', 'rank']
    display_df = df[display_cols].copy()
    
    # Rename columns for better display
    column_mapping = {
        'username': 'Username',
        'feed_won_total': 'Total Winnings',
        'feed_spent_total': 'Total Spent',
        'feed_won_to_spent_ratio': 'ROI',
        'rank': 'Rank'
    }
    
    # Display the top performers
    st.dataframe(
        display_df.head(10).rename(columns=column_mapping),
        column_config={
            "ROI": st.column_config.NumberColumn(format="%.2f"),
            "Rank": st.column_config.NumberColumn(format="%d"),
        },
        hide_index=True,
    )
    
    # Create visualization
    st.subheader("Top 10 Users by ROI")
    
    fig, ax = plt.figure(figsize=(10, 6)), plt.subplot()
    top_users = display_df.sort_values('feed_won_to_spent_ratio', ascending=False).head(10)
    
    colors = sns.color_palette("viridis", 10)
    bars = ax.barh(top_users['username'], top_users['feed_won_to_spent_ratio'], color=colors)
    
    ax.set_xlabel('Return on Investment (ROI)')
    ax.set_title('Top 10 Users by ROI')
    
    # Add data labels
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f'{width:.2f}', 
                ha='left', va='center')
    
    st.pyplot(fig)
    
    # Add filters
    st.sidebar.header("Filters")
    
    # Filter by minimum ROI
    min_roi = st.sidebar.slider("Minimum ROI", 
                              min_value=float(df['feed_won_to_spent_ratio'].min()), 
                              max_value=float(df['feed_won_to_spent_ratio'].max()),
                              value=float(df['feed_won_to_spent_ratio'].min()))
    
    filtered_df = df[df['feed_won_to_spent_ratio'] >= min_roi]
    
    st.subheader("Filtered Results")
    st.dataframe(
        filtered_df[display_cols].rename(columns=column_mapping),
        column_config={
            "ROI": st.column_config.NumberColumn(format="%.2f"),
            "Rank": st.column_config.NumberColumn(format="%d"),
        },
        hide_index=True
    )
    
    # Add additional stats
    st.subheader("User Statistics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", len(df))
    with col2:
        st.metric("Average ROI", f"{df['feed_won_to_spent_ratio'].mean():.2f}")
    with col3:
        st.metric("Total Contests", df['contests_count_total'].sum())
        
else:
    st.error("No data loaded. Please check your Google Sheets connection.")
