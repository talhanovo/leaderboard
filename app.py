import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2 import service_account

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
        # Open the Google Sheet
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
    
    # Calculate rank based on ratio and sort
    df['rank'] = df['feed_won_to_spent_ratio'].rank(ascending=False, method='dense')
    df = df.sort_values('feed_won_to_spent_ratio', ascending=False)
    
    # Select and rename columns for display
    display_cols = ['username', 'feed_won_total', 'feed_spent_total', 'feed_won_to_spent_ratio', 'rank']
    column_mapping = {
        'username': 'Username',
        'feed_won_total': 'Total Winnings',
        'feed_spent_total': 'Total Spent',
        'feed_won_to_spent_ratio': 'ROI',
        'rank': 'Rank'
    }
    
    # Display the full leaderboard
    st.dataframe(
        df[display_cols].rename(columns=column_mapping),
        column_config={
            "ROI": st.column_config.NumberColumn(format="%.2f"),
            "Rank": st.column_config.NumberColumn(format="%d"),
            "Total Winnings": st.column_config.NumberColumn(format="%.2f"),
            "Total Spent": st.column_config.NumberColumn(format="%.2f"),
        },
        hide_index=True,
    )
        
else:
    st.error("No data loaded. Please check your Google Sheets connection.")
