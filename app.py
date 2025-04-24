import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2 import service_account
import numpy as np

# Set page title and layout
st.set_page_config(page_title="User Leaderboard", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: white;
    }
    .leaderboard-title {
        text-align: center;
        font-size: 3.5rem;
        font-weight: bold;
        margin-bottom: 40px;
        color: gold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
    }
    .total-participants {
        text-align: center;
        margin-top: 30px;
        color: #8ecae6;
        font-size: 1.5rem;
        font-weight: bold;
    }
    [data-testid="stDataFrame"] {
        background: rgba(13, 27, 42, 0.7);
        border-radius: 15px;
        overflow: hidden;
        padding: 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    [data-testid="stDataFrame"] > div {
        border: none !important;
    }
    [data-testid="stDataFrame"] th {
        background-color: #1d3557 !important;
        color: white !important;
        font-weight: bold !important;
        text-align: center !important;
        padding: 12px 8px !important;
        border-bottom: 2px solid #457b9d !important;
    }
    [data-testid="stDataFrame"] tbody tr {
        border-bottom: 1px solid rgba(69, 123, 157, 0.2) !important;
        transition: background-color 0.2s ease;
    }
    [data-testid="stDataFrame"] tbody tr:hover {
        background-color: rgba(69, 123, 157, 0.2) !important;
    }
    [data-testid="stDataFrame"] tbody tr:nth-child(1) td:first-child {
        background-color: gold !important;
        color: black !important;
        font-weight: bold !important;
    }
    [data-testid="stDataFrame"] tbody tr:nth-child(2) td:first-child {
        background-color: silver !important;
        color: black !important;
        font-weight: bold !important;
    }
    [data-testid="stDataFrame"] tbody tr:nth-child(3) td:first-child {
        background-color: #cd7f32 !important;
        color: black !important;
        font-weight: bold !important;
    }
    [data-testid="stDataFrame"] td {
        text-align: center !important;
        padding: 12px 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# Page Title
st.markdown('<div class="leaderboard-title">🏆 UOA LEADERBOARD 🏆</div>', unsafe_allow_html=True)

# Fetch data from Google Sheets
@st.cache_data(ttl=600)
def fetch_data():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        credentials_dict = json.loads(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(credentials_dict, scopes=scope)
    except Exception as e:
        st.error(f"Error loading credentials from secrets: {e}")
        st.info("If running locally, make sure to set up your .streamlit/secrets.toml file")
        return pd.DataFrame()

    try:
        client = gspread.authorize(creds)
        sheet = client.open('UOA Leaderboard').sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching data from Google Sheets: {e}")
        return pd.DataFrame()

# Load and clean data
df = fetch_data()

if not df.empty:
    # Convert relevant columns to numeric
    df['feed_spent_total'] = pd.to_numeric(df['feed_spent_total'], errors='coerce')
    df['feed_won_total'] = pd.to_numeric(df['feed_won_total'], errors='coerce')
    df['feed_won_to_spent_ratio'] = pd.to_numeric(df['feed_won_to_spent_ratio'], errors='coerce')
    df['contests_count_total'] = pd.to_numeric(df['contests_count_total'], errors='coerce')
    df['lineups_count_total'] = pd.to_numeric(df['lineups_count_total'], errors='coerce')

    # Drop users with missing ROI (optional)
    df = df.dropna(subset=['feed_won_to_spent_ratio'])

    # Assign ranks using 'first' to keep order
    df['rank'] = df['feed_won_to_spent_ratio'].rank(ascending=False, method='first').astype(int)

    # Sort by rank
    df = df.sort_values('rank')

    # Add medal icons
    def format_rank(rank):
        if rank == 1:
            return "🥇 1"
        elif rank == 2:
            return "🥈 2"
        elif rank == 3:
            return "🥉 3"
        else:
            return str(rank)

    df['rank_display'] = df['rank'].apply(format_rank)

    # Select and rename columns
    display_cols = ['rank_display', 'username', 'contests_count_total', 'lineups_count_total',
                    'feed_spent_total', 'feed_won_total', 'feed_won_to_spent_ratio']
    column_mapping = {
        'rank_display': 'Rank',
        'username': 'Username',
        'contests_count_total': 'Contests Participated',
        'lineups_count_total': 'Total Entries',
        'feed_spent_total': 'Total Spent (FEED)',
        'feed_won_total': 'Total Earned (FEED)',
        'feed_won_to_spent_ratio': 'ROI'
    }

    # Display leaderboard table
    with st.container():
        col1, col2, col3 = st.columns([1, 10, 1])
        with col2:
            st.dataframe(
                df[display_cols].rename(columns=column_mapping),
                column_config={
                    "Rank": st.column_config.TextColumn(width="small"),
                    "Username": st.column_config.TextColumn(width="medium"),
                    "Contests Participated": st.column_config.NumberColumn(format="%d"),
                    "Total Entries": st.column_config.NumberColumn(format="%d"),
                    "Total Spent (FEED)": st.column_config.NumberColumn(format="%.2f"),
                    "Total Earned (FEED)": st.column_config.NumberColumn(format="%.2f"),
                    "ROI": st.column_config.NumberColumn(format="%.2f")
                },
                use_container_width=True,
                hide_index=True
            )

    # Show total participants
    st.markdown(f"<div class='total-participants'>👥 Total Participants: {len(df)}</div>", unsafe_allow_html=True)
else:
    st.error("No data loaded. Please check your Google Sheets connection.")
