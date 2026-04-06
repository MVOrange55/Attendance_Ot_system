import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. PAGE CONFIG & STYLING (Aesthetic UI) ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    
    # /* Compact & Attractive Login Box */
    .login-container {
        max-width: 400px;
        margin: auto;
        padding: 30px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        border-top: 5px solid #ff5722;
        margin-top: 50px;
        text-align: center;
    }
    
    # /* Gradient Sidebar for Colorful Navigation */
    .css-1d391kg {
        background-image: linear-gradient(180deg, #ff5722 0%, #ff8a65 100%);
        color: white;
    }
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg p {
        color: white !important;
    }
    
    # /* Sidebar Navigation Icons & Fonts */
    .css-1d391kg .css-1b1576k { font-size: 1.1rem; }
    
    # /* Status Colors Definition */
    .AB_col { color: white; background-color: #3498db; }
    .P_col { color: white; background-color: #2ecc71; }
    .A_col { color: white; background-color: #e74c3c; }
    .Miss_col { color: white; background-color: #e67e22; }
    .H_col { color: white; background-color: #bdc3c7; }
    .SL_col { color: black; background-color: #f1c40f; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION (Login System) ---
def check_login():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.image("
