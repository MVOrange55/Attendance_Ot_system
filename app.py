import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. SETTINGS & LOGIN ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #FF5722 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    </style>
""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.write("### 🍊 Orange House Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u == "Orange_Hr" and p == "Orange_Admin":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Wrong User/Pass")
    st.stop()

# --- 2. HELPERS ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00', '0']: return None
    try:
        s = str(v).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(19
