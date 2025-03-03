import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
import seaborn as sns

# Set page title
st.title("Leaderboard")

# Function to fetch data from Google Sheets
@st.cache_data(ttl=600)  # Cache the data for 10 minutes
def fetch_data():
    # Set up Google Sheets API credentials
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('service_account_credentials.json', scope)
    client = gspread.authorize(creds)
    
    # Open the Google Sheet (replace with your sheet name)
    sheet = client.open('UOA Leaderboard').sheet1
    
    # Get all data from the sheet
    data = sheet.get_all_records()
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    return df

# Try to fetch data, handle potential errors
try:
    # Load data
    df = fetch_data()
    
    # Show a loading spinner while processing data
    with st.spinner("Processing data..."):
        # Clean and prepare data
        if 'feed_won_to_spent_ratio' in df.columns:
            df['feed_won_to_spent_ratio'] = pd.to_numeric(df['feed_won_to_spent_ratio'], errors='coerce')
        
        if 'spent_total' in df.columns:
            df['spent_total'] = pd.to_numeric(df['spent_total'], errors='coerce')
        
        if 'feed_won_total' in df.columns:
            df['feed_won_total'] = pd.to_numeric(df['feed_won_total'], errors='coerce')
        
        # Extract username from email if available
        if 'email' in df.columns:
            df['username'] = df['email'].apply(lambda x: x.split('@')[0] if isinstance(x, str) else x)
        
        # Calculate rank based on winnings ratio
        if 'feed_won_to_spent_ratio' in df.columns:
            df['rank'] = df['feed_won_to_spent_ratio'].rank(ascending=False, method='dense')
            df = df.sort_values('rank')
    
    # Display leaderboard
    st.subheader("Top Performers")
    
    # Select columns to display
    display_cols = ['username', 'feed_won_total', 'spent_total', 'feed_won_to_spent_ratio', 'rank']
    display_df = df[display_cols].copy()
    
    # Format columns for display
    display_df['feed_won_to_spent_ratio'] = display_df['feed_won_to_spent_ratio'].round(2)
    
    # Rename columns for better display
    display_df.columns = ['Username', 'Total Winnings', 'Total Spent', 'ROI', 'Rank']
    
    # Display the leaderboard
    st.dataframe(
        display_df.head(10),
        column_config={
            "ROI": st.column_config.NumberColumn(
                format="%.2f",
            ),
            "Rank": st.column_config.NumberColumn(
                format="%d",
            ),
        },
        hide_index=True,
    )
    
    # Create visualization
    st.subheader("Top 10 Users by ROI")
    
    fig, ax = plt.figure(figsize=(10, 6)), plt.subplot()
    top_users = display_df.sort_values('ROI', ascending=False).head(10)
    
    colors = sns.color_palette("viridis", 10)
    bars = ax.barh(top_users['Username'], top_users['ROI'], color=colors)
    
    ax.set_xlabel('Return on Investment (ROI)')
    ax.set_title('Top 10 Users by ROI')
    
    # Add a data labels
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f'{width:.2f}', 
                ha='left', va='center')
    
    st.pyplot(fig)

except Exception as e:
    st.error(f"Error fetching or processing data: {e}")
    st.info("Please ensure your Google Sheets API credentials are correctly set up.")
    
# Add filters and more interactive elements
st.sidebar.header("Filters")

# Filter by minimum ROI
if 'feed_won_to_spent_ratio' in df.columns:
    min_roi = st.sidebar.slider("Minimum ROI", 
                                min_value=float(df['feed_won_to_spent_ratio'].min()), 
                                max_value=float(df['feed_won_to_spent_ratio'].max()),
                                value=float(df['feed_won_to_spent_ratio'].min()))
    
    filtered_df = df[df['feed_won_to_spent_ratio'] >= min_roi]
    
    st.subheader("Filtered Results")
    st.dataframe(
        filtered_df[display_cols].rename(
            columns={'username': 'Username', 
                    'feed_won_total': 'Total Winnings', 
                    'spent_total': 'Total Spent', 
                    'feed_won_to_spent_ratio': 'ROI', 
                    'rank': 'Rank'}
        ),
        hide_index=True
    )
