
from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth.transport.requests import Request
from google.auth import default
from googleapiclient.discovery import build
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials

from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import math
import seaborn as sns
import pandas as pd

def clean_dfs(df, resume_book):
    df_cols_to_clean = ['Email ', 'Email Address', "First Name", "Last Name"]
    resume_cols_to_clean = ['Email', 'First Name', "Last Name"]

    for col in df_cols_to_clean:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().str.replace(r'\s+', '', regex=True)

    for col in resume_cols_to_clean:
        if col in resume_book.columns:
            resume_book[col] = resume_book[col].astype(str).str.lower().str.replace(r'\s+', '', regex=True)

    return df, resume_book
    
def request_history(df):
    today = datetime.now().date()

    days_of_week = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
    grid = np.zeros((3, 7)) 
    start_of_week = today - timedelta(days=today.weekday() + 1) 

    date_counts = df['Timestamp'].dt.date.value_counts().to_dict()

    for row in range(3):
        for col in range(7):
            cell_date = start_of_week - timedelta(days=(2 - row) * 7 - col)  
            if cell_date <= today: 
                grid[row, col] = date_counts.get(cell_date, 0)

    mask = np.zeros_like(grid, dtype=bool)
    for row in range(3):
        for col in range(7):
            cell_date = start_of_week - timedelta(days=(2 - row) * 7 - col)
            if cell_date > today:
                mask[row, col] = True

    fig = plt.figure(figsize=(10, 4))
    sns.set(style='white')
    ax = sns.heatmap(grid, annot=True, fmt=".0f", cmap='coolwarm', mask=mask, 
                    cbar_kws={'label': 'Count'}, linewidths=0)

    ax.set_xticks(np.arange(7) + 0.5)
    ax.set_xticklabels(days_of_week, ha="center", size=14)
    ax.set_yticks(np.arange(3) + 0.5)
    ax.set_yticklabels(["2 wks ago", "Last wk", "This wk"], size=14)

    plt.title(f"Requests - Week View (Today: {today})", size=20)
    plt.tight_layout()
    return fig


def request_times(df):
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    today = datetime.today()
    end_of_week = today + timedelta(days=(6 - today.weekday() + 1) % 7)
    start_of_three_weeks = end_of_week - timedelta(weeks=3)

    filtered_df = df[(df['Timestamp'] >= start_of_three_weeks) & (df['Timestamp'] <= end_of_week)]

    filtered_df['Time_Hour'] = filtered_df['Timestamp'].dt.hour + \
                               filtered_df['Timestamp'].dt.minute / 60.0

    fig = plt.figure(figsize=(10, 2.2))

    for time in filtered_df['Time_Hour']:
        plt.axvline(x=time, color='orange', alpha=0.7)

    plt.xlim(0, 24)
    plt.xlabel('Time of Day (Hours)', size=14)
    plt.title('Request Times', size=20)
    plt.xticks(range(0, 25, 1), size=14)
    plt.yticks([])

    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)

    plt.grid(False)
    plt.tight_layout()
    return fig

def update_all_requested(df, resume_book):
    df_update_cols = df.loc[:, "First Name":"Upload Resume"].columns.tolist()
    df_update_cols = [col for col in df_update_cols if col != "Do you want to add, update, or remove your resume?"]
    
    update_rows = df[df["Do you want to add, update, or remove your resume?"] == "I already have a resume in this book and want to update it to a newer version or update my information in the survey."]
    init_len = len(update_rows)
    update_rows = update_rows.drop_duplicates(subset=["Email "], keep="last")
    update_rows = update_rows.drop_duplicates(subset=["First Name", "Last Name"], keep="last")
    print(f"{init_len - len(update_rows)} same-user updates removed. {len(update_rows)} updates to make.")

    update_rows_new = update_rows[df_update_cols]
    update_rows_new.columns = resume_book.columns

    resume_book = pd.concat([resume_book, update_rows_new], ignore_index=True)
    
    for index, row in (update_rows.iterrows()):
        email = row["Email "]
        email2 = row['Email Address']

        if ((pd.isna(email) and pd.isna(email2)) or email == ""):
            raise ValueError(f"Email is missing for row {index} where resume removal is requested.")

        matching_rows = resume_book[(resume_book["Email"] == email) | (resume_book["Email"] == email2)]

        if len(matching_rows) > 1:
            later_matching_row_index = matching_rows.index.max()
            resume_book = resume_book.drop(matching_rows.index[matching_rows.index != later_matching_row_index])

        firstname = row['First Name']
        lastname = row['Last Name']

        matching_rows = resume_book[(resume_book["First Name"] == firstname) & (resume_book["Last Name"] == lastname)]

        if len(matching_rows) > 1:
            later_matching_row_index = matching_rows.index.max()
            resume_book = resume_book.drop(matching_rows.index[matching_rows.index != later_matching_row_index])
        
    return resume_book
                
def add_all_requested(df, resume_book):
    df_update_cols = df.loc[:, "First Name":"Upload Resume"].columns.tolist()
    df_update_cols = [col for col in df_update_cols if col != "Do you want to add, update, or remove your resume?"]

    add_rows = df[df["Do you want to add, update, or remove your resume?"] == "Add my first resume to this resume book"]
    add_rows = add_rows[df_update_cols]
    add_rows.columns = resume_book.columns

    resume_book = pd.concat([resume_book, add_rows], ignore_index=True)
    return resume_book
    
def remove_all_requested(df, resume_book):
    remove_rows = df[df["Do you want to add, update, or remove your resume?"] == "I am no longer looking for a position and wish to remove my resume."]
    print(f"Deleting rows for {remove_rows['Email ']}")

    for index, row in (remove_rows.iterrows()):
        email = row["Email "]
        email2 = row['Email Address']

        if ((pd.isna(email) and pd.isna(email2)) or email == ""):
            raise ValueError(f"Email is missing for row {index} where resume removal is requested.")

        matching_rows = resume_book[(resume_book["Email"] == email) | (resume_book["Email"] == email2)]

        if len(matching_rows) > 1:
            print(f"Warning: Multiple rows found in resume_book with the email {email} or {email2}. Deleting all matching rows.")

        resume_book = resume_book[resume_book["Email"] != email]

        if len(matching_rows) == 0:
            # resort to name
            firstname = row['First Name']
            lastname = row['Last Name']
            matching_rows = resume_book[(resume_book["First Name"] == firstname) & (resume_book["Last Name"] == lastname)]

        if len(matching_rows) > 1:
            print(f"Warning: Multiple rows found in resume_book with the email {email} or {email2}. Abort deletion.")

        else:
            resume_book = resume_book[(resume_book["First Name"] != firstname) & (resume_book["Last Name"] != lastname)]
    return resume_book

def postop_clean_resume_book(resume_book):
    resume_book = resume_book.reset_index(drop=True)
    resume_book['First Name'] = resume_book['First Name'].str.capitalize()
    resume_book['Last Name'] = resume_book['Last Name'].str.capitalize()
    return resume_book

def update_gs_resume_book(resume_book):

    # creds = Credentials.from_service_account_file("google_credentials.json", scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    
    spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1xqvrDynnWfslrSnOymMtJCrMvmAQBka70L7i8USc5Bs/edit?gid=0#gid=0')
    sheet = spreadsheet.get_worksheet(1)
    sheet.clear()
    set_with_dataframe(sheet, resume_book)
    print("Sheet updated successfully.")
    
    num_rows = math.ceil(len(resume_book) / 100) * 100

    sheet_id = '1xqvrDynnWfslrSnOymMtJCrMvmAQBka70L7i8USc5Bs'
    service = build('sheets', 'v4', credentials=creds)

    body = {
        "requests": [
            # Resize rows
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": 0,
                        "dimension": "ROWS",
                        "startIndex": 0,
                        "endIndex": num_rows
                    },
                    "properties": {
                        "pixelSize": 21
                    },
                    "fields": "pixelSize"
                }
            },
            # Set text clipping
            {
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 0,
                        "startColumnIndex": 10,
                        "endColumnIndex": 13
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "wrapStrategy": "WRAP"
                        }
                    },
                    "fields": "userEnteredFormat.wrapStrategy"
                }
            }
        ]
    }

    response = service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body=body
    ).execute()

    print("Rows resized and text clipping set successfully.")
    
def update_gs_requests(df):
    creds = Credentials.from_service_account_file("google_credentials.json", scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    
    spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1IgOnbPhOoCRDBcTf9FIHwP54rHwcqSyKSJTE-XKNnJw/edit?gid=523778578#gid=523778578')
    sheet = spreadsheet.get_worksheet(0)
    sheet.clear()
    set_with_dataframe(sheet, df)
    print("Sheet updated successfully.")