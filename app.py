import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

# CSS for better UI
st.markdown("""
    <style>
    .main { background-color: #fdf2e9; }
    .stDataFrame { border: 1px solid #d35400; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '0', '00:00', 'None']: return None
    try:
        v = str(val).strip()
        if ':' in v: return datetime.strptime(v[:5], '%H:%M').time()
        else: return (datetime(1900, 1, 1) + timedelta(days=float(v))).time()
    except: return None

def calculate_ot_logic(work_hrs, status, is_wo):
    # Rule: Sunday/Holiday (Full OT), AB/ (Above 4 hrs), P (Above 8.5 hrs)
    if is_wo: ot_exact = work_hrs 
    elif status == "AB/": ot_exact = max(0, work_hrs - 4.0)
    else: ot_exact = max(0, work_hrs - 8.5)
    
    if ot_exact <= 0: return 0
    h = int(ot_exact)
    m = (ot_exact - h) * 60
    if m < 15: rm = 0
    elif m < 30: rm = 0.25
    elif m < 45: rm = 0.50
    elif m < 60: rm = 0.75
    else: h += 1; rm = 0
    return h + rm

# --- 3. CORE PROCESSING ENGINE ---
def process_data(df):
    fixed_wo = [1, 4, 8, 15, 21, 22, 29] # Sundays & Holidays
    df.columns = [str(c
