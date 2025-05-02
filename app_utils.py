import re
import colorsys
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.colors as mcolors
from googleapiclient.discovery import build
from wordcloud import STOPWORDS
from google.oauth2.service_account import Credentials
import gspread
from gspread_dataframe import set_with_dataframe
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

    creds = Credentials.from_service_account_file("google_credentials.json", scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])    
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

def parse_rgb_string(rgb_str):
    return tuple(map(int, re.findall(r'\d+', rgb_str)))

def generate_shades(base_color, n_shades):
    rgb = mcolors.to_rgb(base_color)
    h, l, s = colorsys.rgb_to_hls(*rgb)

    lightness_values = [l + (i - n_shades//2)*(0.8/n_shades) for i in range(n_shades)]
    lightness_values = [min(max(0.15, lv), 0.9) for lv in lightness_values]

    shades = [colorsys.hls_to_rgb(h, lv, s) for lv in lightness_values]
    return [mcolors.to_hex(rgb) for rgb in shades]


def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'\b\w*\d\w*\b', '', text)
    text = re.sub(r'\b\w*[^a-zA-Z\s]\w*\b', '', text)
    text = ' '.join([w for w in text.split() if not (w.startswith('i') and len(w) <= 2)])
    text = ' '.join([w for w in text.split() if not re.match(r'^(.)\1+$', w)])
    return text

def analyze_cooccurrence(st, user_input, alpha=1.0, beta=0.5):
    df = st.session_state['text_series'].apply(preprocess_text)
    vectorizer = TfidfVectorizer(stop_words=list(STOPWORDS), min_df=1)
    tfidf_matrix = vectorizer.fit_transform(df)
    feature_names = vectorizer.get_feature_names_out()
    word_index = {word: i for i, word in enumerate(feature_names)}

    if user_input not in word_index:
        st.warning(f"'{user_input}' not found in vocabulary.")
        return

    user_idx = word_index[user_input]
    user_presence = tfidf_matrix[:, user_idx].toarray().flatten() > 0
    count_with_user = user_presence.sum()

    if count_with_user == 1:
        print("User word occurs in only 1 resume")
        filter_threshold = 1
    else:
        filter_threshold = 2

    co_word_counts = {}
    for idx, present in enumerate(user_presence):
        if present:
            row = tfidf_matrix[idx].toarray().flatten()
            for i, val in enumerate(row):
                if val > 0 and i != user_idx:
                    word = feature_names[i]
                    co_word_counts[word] = co_word_counts.get(word, 0) + 1

    filtered_words = {w for w, count in co_word_counts.items() if count >= filter_threshold}
    final_scores = {}

    for word in filtered_words:
        w_idx = word_index[word]
        resumes_with_word = tfidf_matrix[:, w_idx].toarray().flatten() > 0
        a = ((user_presence) & (resumes_with_word)).sum()
        b = ((~user_presence) & (resumes_with_word)).sum()
        score = alpha * a - beta * b
        final_scores[word] = (score, a, b)

    sorted_words = sorted(final_scores.items(), key=lambda x: x[1][0], reverse=True)

    # st.write("Top related words:")
    # for word, (score, a, b) in sorted_words[:10]:
    #     st.write(f"{word}: score={score:.2f} (with={a}, without={b})")

    fig = plot_related_words(user_input, sorted_words)

    return fig


def plot_related_words(user_input, sorted_words, top_n=15):
    sorted_words = sorted_words[:top_n]
    angles = np.linspace(0, 2 * np.pi, len(sorted_words), endpoint=False)

    scores = np.array([score for (_, (score, _, _)) in sorted_words])
    min_length = 1.5
    max_length = 4.0
    norm_scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-6)
    lengths = max_length - norm_scores * (max_length - min_length)

    x = lengths * np.cos(angles)
    y = lengths * np.sin(angles)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-max_length - 1, max_length + 1)
    ax.set_ylim(-max_length - 1, max_length + 1)
    ax.axis('off')

    ax.text(0, 0, user_input, fontsize=14, ha='center', va='center', bbox=dict(facecolor='pink', boxstyle='circle'))

    for i, ((word, (score, a, b)), xi, yi) in enumerate(zip(sorted_words, x, y)):
        ax.plot([0, xi], [0, yi], color='gray', linewidth=1)
        ax.text(xi, yi, word, fontsize=10, ha='center', va='center', bbox=dict(facecolor='lightgreen', boxstyle='round'))

    return fig