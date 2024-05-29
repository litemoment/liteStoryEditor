# ***********************************************************
# * Copyright (c) 2024 litemoment.com. All rights reserved. *
# ***********************************************************
# Contact: webmaster@litemoment.com

import streamlit as st
import gspread
# from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime

# Set up Google Sheets API credentials
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
            "https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"
        ],
)

client = gspread.authorize(creds)

# Function to reload sheet names
def get_sheet_names():
    return sorted([worksheet.title for worksheet in sheet.worksheets()], reverse=True)

# Initialize session state for sheet selection and slider position
if 'selected_sheet' not in st.session_state:
    st.session_state.selected_sheet = None
if 'slider_position' not in st.session_state:
    st.session_state.slider_position = 1

# Open the Google Sheet by title
sheet = client.open("Game-Notebook")

# Top of the page - Sheet selection
selected_sheet = st.selectbox("Select a sheet", get_sheet_names(), key="sheet_dropdown")

# If the selected sheet has changed, reset session values and rerun app
if selected_sheet != st.session_state.selected_sheet:
    st.session_state.selected_sheet = selected_sheet
    st.session_state.slider_position = 1  # Reset slider position
    st.rerun()

# Load the selected sheet into a DataFrame
worksheet = sheet.worksheet(selected_sheet)
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# Ensure the PageID column is treated as integer
df['PageID'] = df['PageID'].astype(int)

# Sort DataFrame by PageID
df = df.sort_values(by='PageID')

# Create a sorted list of available PageIDs
available_page_ids = df['PageID'].tolist()
page_count = len(available_page_ids)

# Check if available_page_ids is not empty before accessing its elements
page_id = None

# st.write(f"available_page_ids:{available_page_ids}")
if available_page_ids:
    page_id = available_page_ids[st.session_state.slider_position - 1]

# Display the selected data
try:
    if page_id:
        row = df[df["PageID"] == page_id].iloc[0]
        if 'DateTime' in row and 'Story' in row and 'Video URL' in row:
            # st.markdown(f"**DateTime:** {row['DateTime']}")
            
            # Editable textarea for Story
            edited_story = st.text_area("Edit Story", value=row['Story'], key="story_text", placeholder="Write your comment here...")

            # Update button
            if st.button("Update"):
                # Update the DataFrame with the new Story value
                df.loc[df["PageID"] == page_id, "Story"] = edited_story

                # Find the row number of the current PageID in the Google Sheet
                cell = worksheet.find(str(page_id))
                row_number = cell.row

                # Update the Google Sheet with the new Story value
                worksheet.update_cell(row_number, df.columns.get_loc("Story") + 1, edited_story)

                st.success("Story updated successfully!")

            st.video(row['Video URL'], start_time=0)

            # Set a comfortable width for the video
            st.markdown(
                f"""
                <style>
                .stVideo > video {{
                    width: 90%;
                    max-width: 90%;
                    height: auto;
                    margin: auto;
                    display: block;
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.error("The selected sheet does not have the expected columns.")
except Exception as e:
    st.error(f"An error occurred: {e}")

# Bottom of the page - Navigation buttons and slider
prev_button, next_button = st.columns([1, 1])

# Apply custom CSS to align the next button to the right
st.markdown(
    """
    <style>
    .stButton button {
        width: 100%;
    }
    .stButton:last-child button {
        float: right;
    }
    </style>
    """,
    unsafe_allow_html=True
)

with prev_button:
    if st.button("Previous") and st.session_state.slider_position > 1:
        st.session_state.slider_position -= 1
        st.rerun()
with next_button:
    if st.button("Next") and st.session_state.slider_position < page_count:
        st.session_state.slider_position += 1
        st.rerun()

# PageID slider
new_slider_position = st.slider(
    "PageID",
    min_value=1,
    max_value=page_count,
    step=1,
    value=st.session_state.slider_position
)

# Check if slider position changed
if new_slider_position != st.session_state.slider_position:
    st.session_state.slider_position = new_slider_position
    st.rerun()
