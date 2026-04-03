import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- Page Config ---
st.set_page_config(page_title="Monthly HR Master Pro", layout="wide")
st.title("🛡️ Final HR Automation System (Locked Rules)")

# --- Helper Functions ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() == '' or str(val).lower() == 'nan': return None
    try:
        if isinstance(val, time): return val
        if isinstance(val, datetime): return val.time()
        val_str = str(val).strip()
        if ':' in val_str: return datetime.strptime(val_str[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(val))).time()
    except: return None

def get_ot_decimal_slab(total_hours):
    """15-Min Slab Logic: 15=.25, 30=.50, 45=.75, 60=1.0"""
    hours = int(total_hours)
    minutes = round((total_hours - hours) * 60)
    if minutes < 15: slab_dec = 0.0
    elif minutes < 30: slab_dec = 0.25
    elif minutes < 45: slab_dec = 0.50
    elif minutes < 60: slab_dec = 0.75
    else: 
        hours += 1
        slab_dec = 0.0
    return float(hours + slab_dec)

def
