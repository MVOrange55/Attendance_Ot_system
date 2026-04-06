import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Orange House HR Dashboard", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .login-container {
        max-width: 450px; margin: auto; padding: 30px;
        background: white; border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border-top: 6px solid #FF4B1F; margin-top: 50px;
    }
    .header-text { text-align: center; color: #333; font-family: 'Arial'; }
    </style>
""", unsafe_allow_html=True)

def check_login():
    if 'auth' not in st.session_state:
        st.session_state.auth = False

    if not st.session_state.auth:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown('<h2 class="header-text">🍊 Orange House Pvt Ltd</h2>', unsafe_allow_html=True)
            st.markdown('<p class="header-text">HR Administration Dashboard</p>', unsafe_allow_html=True)
            u = st.text_input("User Name", key="user_val", placeholder="Orange_Hr")
            p = st.text_input("Password", type="password", key="pass_val", placeholder="Orange_Admin")
            if st.button("Sign In"):
                if u == "Orange_Hr" and p == "Orange_Admin":
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
            st.markdown('</div>', unsafe_allow_html=
