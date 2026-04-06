import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIG ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")
st.title("📊 Orange House HR Master System")

# --- 2. INTERNAL RULES & HELPERS ---
FIXED_WO = [1, 4, 8, 15, 21, 22, 29] # Sundays & Specific Holidays

def parse_time_safe(val):
    if pd.isna(val) or str(val).strip().lower() in ['', 'nan', '0', '00:00', 'none', 'null']: 
        return None
    try:
        v = str(val).strip()
        if ':' in v:
            return datetime.strptime(v[:5], '%H:%M').time()
        else:
            # Handle Excel float time
            return (datetime(1900, 1, 1) + timedelta(days=float(v))).time()
    except:
        return None

def get_ot(work_hrs, status, is_wo):
    if is_wo: 
        ot_val = work_hrs 
    elif status == "AB/": 
        ot_val = max(0, work_hrs - 4.0)
    else: 
        ot_val = max(0, work_hrs - 8.5)
    
    if ot_val <= 0: return 0
    # 15-min Rounding
    h = int(ot_val)
    m = (ot_val - h) *
