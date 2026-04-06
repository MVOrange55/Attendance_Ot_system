import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

# Styling for better visibility
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #FF5722 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .report-title { color: #FF5722; font-weight: bold; font-size: 24px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIN SYSTEM ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write("### 🍊 Orange House HR Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u == "Orange_Hr" and p == "Orange_Admin":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Wrong User/Pass")
    st.stop()

# --- 3. HELPERS ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00', '0']: return None
    try:
        s = str(v).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(1900,1,1)+timedelta(days=float(s))).time()
    except: return None

def get_ot(hrs, status, is_sp):
    # Sunday/Holiday pe pura OT, baaki din 8.5 ke baad
    v = hrs if is_sp else (max(0, hrs-4.0) if status == "AB/" else max(0, hrs-8.5))
    if
