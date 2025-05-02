    
from datetime import datetime
import re
from matplotlib import pyplot as plt
import streamlit as st
from PIL import Image
import pandas as pd
import plotly.express as px
import plotly.colors as pc
from app_utils import analyze_cooccurrence, generate_shades, parse_rgb_string, preprocess_text
from wordcloud import WordCloud, STOPWORDS

st.markdown(
     f"""
     <style>
        
    .stApp {{
        background: linear-gradient(to top, purple, black, purple);
        background-size: 100% 200%;
        animation: moveGradient 180s ease-in-out infinite;
        background-attachment: fixed;
    }}

    @keyframes moveGradient {{
        0% {{
            background-position: 0% 0%;
        }}
        50% {{
            background-position: 0% 100%;
        }}
        100% {{
            background-position: 0% 0%;
        }}
    }}
    
    *{{
        color: white;
        text-align: center
    }}
    
    .st-emotion-cache-0.e1f1d6gn0{{
        display: block;
        margin-top: auto;
        margin-bottom: auto;
        align-items: center;
        justify-content: center;
    }}
    
    .st-emotion-cache-1xf0csu.e115fcil1 img {{
        border-radius: 20px;
        width: 300px
    }}
    
    .custom-divider {{
        border-top: 2px solid lightblue; 
        margin-top: 20px;
        margin-bottom: 20px;
    }}
    
    .stButton button{{
        background-color: darkgray;
        padding: 20px
    }}
    
    [data-testid="stBaseButton-secondary"] {{
        background-color: darkgray;
        padding: 20px
    }}
    
    [data-testid="stSelectbox"] div div{{
        background-color: darkgray;
        color: white
    }}
    
    [data-testid="stSelectboxVirtualDropdown"] div div li{{
        background-color: black;
    }}
    
    [data-testid="stSelectboxVirtualDropdown"] div div li:hover{{
        background-color: #5a2e64;
    }}
    
    .st-emotion-cache-1hyd1ho.e121c1cl0{{
        color: black;
        font-weight: bold
    }}
    
    .st-an.st-ao.st-ap.st-aq.st-ak.st-ar.st-am.st-as.st-at.st-au.st-av.st-aw.st-ax.st-ay.st-az.st-b0.st-b1.st-b2.st-b3.st-b4.st-b5.st-b6.st-eb.st-ec.st-ed.st-ee.st-bb.st-bc{{
        background-color: white;
        color: black
    }}
    
    .st-eh.st-al.st-c1.st-c2.st-cd.st-c3.st-c4.st-c5.st-c6.st-c7.st-an.st-ap.st-aq.st-ao.st-ei.st-ep.st-eq div > div li{{
        background-color: white;
        color: black
    }}

    
     </style>
     """,
     unsafe_allow_html=True
 )

# load data
if 'resume_book' not in st.session_state:
    csv_url = f"https://docs.google.com/spreadsheets/d/1xqvrDynnWfslrSnOymMtJCrMvmAQBka70L7i8USc5Bs/export?format=csv&gid=0"
    st.session_state['resume_book'] = pd.read_csv(csv_url)

with st.container():
    col1, col2 = st.columns([1.3, 3.5], vertical_alignment='top')

    with col1:
        image = Image.open('peer_adviser_logo.png')
        st.image(image)

    with col2:
        st.header('Resume Book Tools')
        st.write("For advisers, streamline and automate the process of managing student requests and updating the Allen School resume book. For recruiters, filter through resumes to find talent to fit your specific needs!")

    st.markdown('<hr class="custom-divider" style="border-top: 2px solid lightblue">', unsafe_allow_html=True)
    
    st.html('''
            <strong>
            This resume book is updated on a weekly basis throughout the academic year. 
            If you're looking for the original Google Sheets (.csv) version of the resume book, 
            please click <a href = "https://docs.google.com/spreadsheets/d/1xqvrDynnWfslrSnOymMtJCrMvmAQBka70L7i8USc5Bs/edit?gid=180200061#gid=180200061"> here</a>. <br/> </strong>
            <br/>

            <div style = "color: #f6e8ff; background-color: #2a123a; padding: 40px; border-radius: 25px; border: 3px solid black">
            <strong style = "color: white"> While browsing the resume book, here are a few tips to keep in mind </strong>:
            <em><ol>
            <li style = "text-align: left;"> To the best of our knowledge, if a student's resume is present in this book, they are still actively searching for a position. </li>
            <li style = "text-align: left;"> For "What type of roles are you interested in?", students have the option of selecting: Software Development/Software Engineering, Project Management, Product Management, User Experience/User Interface, or writing in whatever other options they would like. </li>
            <li style = "text-align: left;"> Students were instructed to paste their entire resume into the form. This is NOT intended to be ultra-readable, but should help with when you want to search for particular key words. </li>
            </ol></em>
            </div>
            ''')
    
    # st.write( st.session_state['resume_book'].head())
    st.subheader("Graduation Overview", divider='violet')

    current_year = datetime.now().year

    year_counts =  st.session_state['resume_book']['Grad Year'].value_counts().reset_index()
    year_counts.columns = ['Grad Year', 'Count']

    base_colors = px.colors.qualitative.Prism_r
    year_color_map = {year: base_colors[i % len(base_colors)] for i, year in enumerate(sorted(year_counts['Grad Year']))}

    col1, col2 = st.columns([9, 5])

    with col1:
        st.subheader("Graduation Year")
        fig = px.pie(
            year_counts,
            names='Grad Year',
            values='Count',
            color='Grad Year',
            color_discrete_map=year_color_map,
            hole=0.3,
            height=490
        )
        fig.update_traces(textinfo='label+percent', hoverinfo='label+value+percent')
        fig.update_layout(
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.1),
            margin=dict(t=40, b=40, l=0, r=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        selected_year = st.selectbox(
            "Select a Grad Year to see breakdown",
            sorted(st.session_state['resume_book']['Grad Year'].dropna().unique()),
            index=list(st.session_state['resume_book']['Grad Year'].dropna().unique()).index(current_year)  # Default to current year
        )
        quarter_counts = st.session_state['resume_book'][
            st.session_state['resume_book']['Grad Year'] == selected_year
        ]['Grad Quarter'].value_counts().reset_index()
        quarter_counts.columns = ['Grad Quarter', 'Count']

        base_color = year_color_map.get(selected_year, "#636EFA")
        if base_color.startswith("rgb"):
            base_rgb = parse_rgb_string(base_color)
        else:
            base_rgb = pc.hex_to_rgb(base_color)

        lightness_scale = [0.4 + 0.5 * (i / max(1, len(quarter_counts) - 1)) for i in range(len(quarter_counts))]
        quarter_colors = [
            pc.label_rgb(tuple(min(int(c * l), 255) for c in base_rgb))
            for l in lightness_scale
        ]
        quarter_color_map = dict(zip(quarter_counts['Grad Quarter'], quarter_colors))

        fig_quarter = px.pie(
            quarter_counts,
            names='Grad Quarter',
            values='Count',
            color='Grad Quarter',
            color_discrete_map=quarter_color_map,
            hole=0.3,
            title=f'Quarterly Breakdown for {selected_year}',
        )
        fig_quarter.update_traces(textinfo='label+percent', hoverinfo='label+value+percent',
                                  domain={'x': [0.1, 0.9], 'y': [0.1, 0.9]})
        fig_quarter.update_layout(
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.1),
            margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig_quarter, use_container_width=True)
        
    st.subheader("Desired Positions", divider='violet')

    st.subheader("Position Preference")
    position_counts = st.session_state['resume_book']["Are you looking for an internship or full-time position?"].value_counts().reset_index()
    position_counts.columns = ["Position Type", "Count"]

    desired_order = ["Internship", "Full time", "Both"]
    position_counts["Position Type"] = pd.Categorical(position_counts["Position Type"], categories=desired_order, ordered=True)
    position_counts = position_counts.sort_values("Position Type")
    
    base_color = "#7451c1" 
    num_positions = len(position_counts)
    custom_colors = generate_shades(base_color, num_positions)

    fig_position = px.bar(
        position_counts,
        x="Count",
        y="Position Type",
        text="Count",
        color="Position Type",
        orientation='h',
        height=200,
        color_discrete_sequence = custom_colors
    )

    fig_position.update_layout(
        showlegend=False,
        xaxis_title="Number of Students",
        yaxis_title="",
        margin=dict(t=40, b=40)
    )

    fig_position.update_traces(textposition='outside')
    st.plotly_chart(fig_position, use_container_width=True)

    st.subheader("Preferred Roles")
    role_series = st.session_state['resume_book']["What types of roles are you looking for?"].dropna()
    all_roles = role_series.str.split(", ").explode()
    all_roles = all_roles[all_roles != ""]

    role_counts = all_roles.value_counts().reset_index()
    role_counts.columns = ["Role", "Count"]
    
    role_counts = role_counts[role_counts["Count"] >= 2]

    max_count = role_counts["Count"].max()
    min_count = role_counts["Count"].min()
    use_log_x = (max_count - min_count) > 50

    base_color = "#1f77b4" 
    num_roles = len(role_counts)
    custom_colors = generate_shades(base_color, num_roles)

    fig_roles = px.bar(
        role_counts,
        x="Count",
        y="Role",
        text="Count",
        color="Role",
        orientation="h",
        color_discrete_sequence = custom_colors
    )

    fig_roles.update_layout(
        showlegend=False,
        xaxis_title="Number of Students",
        yaxis_title="",
        margin=dict(t=40, b=40),
        xaxis_type="log" if use_log_x else "linear"
    )

    fig_roles.update_traces(textposition='outside')

    st.plotly_chart(fig_roles, use_container_width=True)
    
    st.subheader("Resume Keywords", divider='violet')
    
    if 'text_series' not in st.session_state:
        st.session_state['text_series'] = st.session_state['resume_book']['Resume Full Text'].dropna()
    full_text = " ".join(st.session_state['text_series'])

    full_text = re.sub(r'\d+', '', full_text)

    stopwords = STOPWORDS

    if 'wordcloud' not in st.session_state:
        st.session_state['wordcloud'] = WordCloud(
            width=800,
            height=400,
            background_color='white',
            stopwords=stopwords,
            collocations=False
        ).generate(full_text)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(st.session_state['wordcloud'], interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)
    
    user_input = st.text_input("Enter a word to analyze:")
    if user_input:
        user_input = preprocess_text(user_input.strip())
        fig2 = analyze_cooccurrence(st, user_input, alpha=1.0, beta=0.5)
        st.pyplot(fig2)
        
    st.subheader("Resume Filter Tool", divider='violet')

    QUARTERS = st.session_state['resume_book']['Grad Quarter'].dropna().unique()
    YEARS = st.session_state['resume_book']['Grad Year'].dropna().unique()
    
    min_year = int(YEARS.min())
    max_year = int(YEARS.max())

    mid_year = (min_year + max_year) // 2 
    start_default = max(min_year, mid_year - 2 // 2)
    end_default = min(max_year, start_default + 2)

    grad_year_range = st.slider("Select Graduation Year Range", min_value=min_year, max_value=max_year, value=(start_default, end_default))
    quarter_options = st.multiselect("Select Graduation Quarters", QUARTERS, default=QUARTERS)

    selected_roles = st.multiselect("Select Desired Role(s)", role_counts['Role'].unique(), default=['Data Science'])

    st.subheader("Keyword Filter (Resume MUST contain these)")
    default_keywords = ["python", "computer", "visualization"]
    num_keywords = st.number_input("How many keywords/phrases?", value=len(default_keywords), min_value=1, step=1)

    keywords = []
    for i in range(int(num_keywords)):
        default_value = default_keywords[i] if i < len(default_keywords) else ""
        keyword = st.text_input(f"Keyword {i+1}", value=default_value, key=f"kw_{i}")
        if keyword:
            keywords.append(keyword.lower())
        # --- Filter logic ---
    filtered_df = st.session_state['resume_book'][
        (st.session_state['resume_book']["Grad Year"] >= grad_year_range[0]) &
        (st.session_state['resume_book']["Grad Year"] <= grad_year_range[1]) &
        (st.session_state['resume_book']["Grad Quarter"].isin(quarter_options)) &
        (st.session_state['resume_book']["What types of roles are you looking for?"]
            .apply(lambda r: isinstance(r, str) and any(role in r for role in selected_roles)))
    ]
    
    filtered_df['Resume Full Text'] = filtered_df['Resume Full Text'].astype(str)

    st.subheader("Search Results")

    st.write(f"Total resumes matching requirements (ignoring keywords): {len(filtered_df)}")

    def keyword_match(row, keywords):
        text = row["Resume Full Text"].lower()
        matches = [kw for kw in keywords if kw in text]
        return matches

    filtered_df["matched_keywords"] = filtered_df.apply(lambda row: keyword_match(row, keywords), axis=1)
    filtered_df["match_count"] = filtered_df["matched_keywords"].apply(len)
    max_match = filtered_df["match_count"].max() if not filtered_df.empty else 0

    exact_matches = filtered_df[filtered_df["match_count"] == len(keywords)]
    partial_matches = filtered_df[(filtered_df["match_count"] < len(keywords)) & (filtered_df["match_count"] > 0)]

    if len(exact_matches) > 0:
        st.write(f"Resumes matching all keywords: {len(exact_matches)}")
    else:
        st.write(f"No resumes matched all keywords.")
        st.write(f"{len(partial_matches)} resumes matched at least one keyword.")
        st.write(f"The most matched keywords in a resume was {max_match}.")

    min_required = st.slider("Set minimum number of keyword matches to download resumes", min_value=1, max_value=max(2, len(keywords)), value=2)

    st.subheader("Download Resume Sets")
        
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download resumes (Requirements only)",
        data=csv,
        file_name='requirements_only.csv',
        mime='text/csv'
    )
    
    csv2 = filtered_df[filtered_df["match_count"] >= min_required].to_csv(index=False)
    st.download_button(
        label=f"Download resumes (≥ {min_required} keyword matches)",
        data=csv2,
        file_name=f'min_{min_required}_matches.csv',
        mime='text/csv'
    )
    
    csv3 = exact_matches.to_csv(index=False)
    st.download_button(
        label="Download resumes (All keyword matches)",
        data=csv3,
        file_name=f'all_keywords_matched.csv',
        mime='text/csv'
    )