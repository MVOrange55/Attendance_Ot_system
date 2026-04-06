import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #FF5722 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .report-title { color: #d35400; font-weight: bold; font-size: 24px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HELPERS ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00']: return None
    try:
        s = str(v).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(s))).time()
    except: return None

def style_muster(v):
    if v in ['WO', 'H']: return 'background-color: #d4edda; color: #155724;'
    if v == 'AB/': return 'background-color: #f8d7da; color: #721c24;'
    if v == 'Miss': return 'background-color: #fff3cd; color: #856404;'
    if v == 'P (SL)': return 'background-color: #e2e3e5; color: #383d41;'
    return ''

# --- 3. CORE PROCESSING ENGINE ---
def process
