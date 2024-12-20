from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

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