import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

# --- 2. HELPER FUNCTIONS ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '0', '00:00']: return None
    try:
        v = str(val).strip()
        if ':' in v: return datetime.strptime(v[:5], '%H:%M').time()
        else: return (datetime(1900, 1, 1) + timedelta(days=float(v))).time()
    except: return None

def calculate_ot_final(work_hrs, status, is_wo):
    # Rule: Sunday/Holiday par Full OT. AB/ par 4 hrs ke upar OT. P par 8.5 ke upar.
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
def process_hr_master(df):
    # Fixed Holidays & Sundays as per your instruction
    fixed_wo = [1, 4, 8, 15, 21, 22, 29] 
    
    df.columns = [str(c).strip() for c in df.columns]
    id_col, name_col = df.columns[0], df.columns[1]
    df[id_col] = df[id_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    dates = [c for c in df.columns if str(c).replace('.0','').isdigit()]
    muster, ot_rep, ex_sum, ex_det, miss_p, final_sum = [], [], [], [], [], []
