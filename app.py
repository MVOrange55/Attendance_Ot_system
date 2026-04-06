import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #fdf2e9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #d35400; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '0', '00:00']: return None
    try:
        v = str(val).strip()
        if ':' in v: return datetime.strptime(v[:5], '%H:%M').time()
        else: return (datetime(1900, 1, 1) + timedelta(days=float(v))).time()
    except: return None

def calculate_ot_logic(work_hrs, status, is_sunday):
    """
    Rule: 
    1. Sunday: Full OT (No deduction).
    2. P or P(SL): Total - 8.5.
    3. AB/: Total - 4.0 (Sirf 4 hrs ke upar wala OT).
    """
    if is_sunday:
        ot_exact = work_hrs
    elif status == "AB/":
        ot_exact = max(0, work_hrs - 4.0)
    else: # P or P(SL)
        ot_exact = max(0, work_hrs - 8.5)
    
    if ot_exact <= 0: return 0
    
    # 15-minute Rounding Slabs
    h = int(ot_exact)
    m = (ot_exact - h) * 60
    if m < 15: rm = 0
    elif m < 30: rm = 0.25
    elif m < 45: rm = 0.50
    elif m < 60: rm = 0.75
    else: h += 1; rm = 0
    return h + rm

# --- 3. MASTER PROCESSING ENGINE ---
def process_hr_system(df, nh_list):
    df.columns = [str(c).strip() for c in df.columns]
    id_col, name_col = df.columns[0], df.columns[1]
    df[id_col] = df[id_col].ffill()
    df[name_col] = df[name_col].ffill()
