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
    
    .st-emotion-cache-1hyd1ho.e121c1cl0{{
        color: black;
        font-weight: bold
    }}
    
     </style>
     """,
     unsafe_allow_html=True
 )

# load data
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

    st.markdown('<hr class="custom-divider" style="border-top: 2px solid lightblue">', unsafe_allow_html=True)
    