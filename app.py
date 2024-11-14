import streamlit as st
from PIL import Image
import pandas as pd

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
    
     </style>
     """,
     unsafe_allow_html=True
 )

# load data
csv_url = f"https://docs.google.com/spreadsheets/d/1IgOnbPhOoCRDBcTf9FIHwP54rHwcqSyKSJTE-XKNnJw/export?format=csv&gid=523778578"
df = pd.read_csv(csv_url)
df = df[df['Done?'] != 'yes']

csv_url = f"https://docs.google.com/spreadsheets/d/1xqvrDynnWfslrSnOymMtJCrMvmAQBka70L7i8USc5Bs/export?format=csv&gid=0"
resume_book = pd.read_csv(csv_url)

with st.container():
    
    col1, col2 = st.columns([1.3, 3.5], vertical_alignment='top')

    with col1:
        image = Image.open('peer_adviser_logo.png')
        st.image(image)

    with col2:
        st.header('Resume Book Tools')
        st.write("For advisers, streamline and automate the process of managing student requests and updating the Allen School resume book. For recruiters, filter through resumes to find talent to fit your specific needs!")

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.write(f"There are **<span style='color:#dfbdf5;'>{len(df)}</span>** updates to make.", unsafe_allow_html=True)

    possible_values = {
        "I already have a resume in this book and want to update it to a newer version or update my information in the survey.": 0,
        "Add my first resume to this resume book": 0,
        "I am no longer looking for a position and wish to remove my resume.": 0
    }

    value_counts = df['Do you want to add, update, or remove your resume?'].value_counts().sort_index()
    
    for value in value_counts.index:
        possible_values[value] = value_counts[value]

    col3, col4, col5 = st.columns([1, 1, 1])
    columns = [col3, col4, col5]
    values = list(possible_values.keys())

    i = 1
    for col, value in zip(columns, values):
        i += 1
        with col:
            st.markdown(
                f"""
                <div style="background-color:#f0f0f0; padding: 10px; border-radius: 5px">
                    <h4 style = "color: black; text-align: left; padding: 15px">{value}</h4>
                    <p style = "color: black; text-align: left; padding: 15px">Count: {possible_values[value]}</p>
                </div>
                <br/>
                """,
                unsafe_allow_html=True
            )
            

            if st.button(f"{i}) Approve requests"):
                st.write(f"You approved {possible_values[value]} requests.")
                
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
