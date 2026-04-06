import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. UI & LOGIN ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .login-box {
        max-width: 400px; margin: auto; padding: 2rem;
        background: white; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-top: 8px solid #FF5722; margin-top: 50px;
        text-align: center;
    }
    [data-testid="stSidebar"] { background: linear-gradient(#FF5722, #E64A19); }
    [data-testid="stSidebar"] * { color: white !important; }
    </style>
""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.header("🍊 Orange House Login")
        u = st.text_input("User Name", placeholder="Orange_Hr")
        p = st.text_input("Password", type="password", placeholder="Orange_Admin")
        if st.button("Login"):
            if u == "Orange_Hr" and p == "Orange_Admin":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Wrong User/Pass
