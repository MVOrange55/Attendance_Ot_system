import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Orange House HR Portal", layout="wide", page_icon="🍊")

# Custom CSS for Orange Theme
st.markdown("""
    <style>
    .main { background-color: #fff9f0; }
    header {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #ffedd5; border-radius: 5px; padding: 10px; color: #9a3412; font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #fb923c !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE CORE FUNCTIONS (LOCKED) ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00']: return None
    try:
        s = str(v).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        # Handle Excel float time
        return (datetime(1900, 1, 1) + timedelta(days=float(s))).time()
    except: return None

def get_slab_ot(extra_hrs):
    if extra_hrs < 0.25: return 0.0
    h = int(extra_hrs)
    m = round((extra_hrs - h) * 60)
    if 15 <= m < 30: slab = 0.25
    elif 30 <= m < 45: slab = 0.50
    elif 45 <= m < 60: slab = 0.75
    elif m >= 60: h += 1; slab = 0.0
    else: slab = 0.0
    return float(h + slab)

def run_hr_engine(df, holidays, corrections):
    if df is None: return None, None, None, None, None
    df_w = df.copy()
    id_c, name_c = df_w.columns[0], df_w.columns[1]
    df_w[id_c], df_w[name_c] = df_w[id_c].ffill(), df_w[name_c].ffill()
    
    # APPLY CORRECTIONS (Update & Transfer
    
