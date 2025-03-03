import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2 import service_account

# Set page title and app styling
st.set_page_config(page_title="User Leaderboard", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(to bottom, #1e3c72, #2a5298);
        color: white;
    }
    .leaderboard-title {
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 30px;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Title with custom styling
st.markdown('<div class="leaderboard-title">🏆 User Leaderboard 🏆</div>', unsafe_allow_html=True)

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
    df['contests_count_total'] = pd.to_numeric(df['contests_count_total'], errors='coerce')
    df['lineups_count_total'] = pd.to_numeric(df['lineups_count_total'], errors='coerce')
    
    # Calculate rank based on ratio and sort
    df['rank'] = df['feed_won_to_spent_ratio'].rank(ascending=False, method='dense')
    df = df.sort_values('feed_won_to_spent_ratio', ascending=False)
    
    # Select and rename columns for display
    display_cols = ['rank', 'username', 'contests_count_total', 'lineups_count_total']
    column_mapping = {
        'rank': 'Rank',
        'username': 'Username',
        'contests_count_total': 'Contests Participated',
        'lineups_count_total': 'Lineups Entered'
    }
    
    # Display the full leaderboard
    st.dataframe(
        df[display_cols].rename(columns=column_mapping),
        column_config={
            "Rank": st.column_config.NumberColumn(
                format="%d",
                help="Position on leaderboard based on ROI"
            ),
            "Username": st.column_config.TextColumn(
                width="medium",
                help="User's name"
            ),
            "Contests Participated": st.column_config.NumberColumn(
                format="%d",
                help="Total number of contests entered"
            ),
            "Lineups Entered": st.column_config.NumberColumn(
                format="%d",
                help="Total number of lineups created"
            )
        },
        use_container_width=True,
        hide_index=True,
    )
    
    # Display total participants
    st.markdown(f"<h3 style='text-align: center; margin-top: 20px;'>👥 Total Participants: {len(df)}</h3>", unsafe_allow_html=True)
    
else:
    st.error("No data loaded. Please check your Google Sheets connection.")
