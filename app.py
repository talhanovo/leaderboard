import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2 import service_account
import matplotlib.pyplot as plt
import seaborn as sns

# Set page title
st.title("User Leaderboard")

# Initialize df as a global variable with a default empty DataFrame
df = pd.DataFrame()
display_cols = []

# Function to fetch data from Google Sheets
@st.cache_data(ttl=600)  # Cache the data for 10 minutes
def fetch_data():
    # Set up Google Sheets API credentials from secrets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # Get credentials from Streamlit secrets
    credentials_dict = json.loads(st.secrets["gcp_service_account"])
    creds = service_account.Credentials.from_service_account_info(
        credentials_dict, 
        scopes=scope
    )
    
    client = gspread.authorize(creds)
    
    # Open the Google Sheet (replace with your sheet name)
    sheet = client.open('UOA Leaderboard').sheet1
    
    # Get all data from the sheet
    data = sheet.get_all_records()
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    return df

# Rest of your code remains the same...
