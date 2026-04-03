import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- Page Config ---
st.set_page_config(page_title="HR Multi-Report System", layout="wide")
st.title("🛡️ Final HR Automation: 4-Row Sequential System")

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

def get_ot_decimal(total_hrs):
    """15-Min Slab: .25, .50, .75, 1.0"""
    h = int(total_hrs)
    m = round((total_hrs - h) * 60)
    if m < 15: dec = 0.0
    elif m < 30: dec = 0.25
    elif m < 45: dec = 0.50
    elif m < 60: dec = 0.75
    else: h += 1; dec = 0.0
    return float(h + dec)

def process_data(df, holidays):
    # Header cleaning
    df.columns = [str(c).strip().split('.')[0] for c in df.columns]
    cols = df.columns.tolist()
    eid_col, name_col = cols[0], cols[1]
    
    # Fill Emp ID and Name for all 4 rows of each employee
    df[eid_col] = df[eid_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    # Filter 1-31 Date Columns
    date_cols = [c for c in cols if c.isdigit() and 1 <= int(c) <= 31]
    
    master_records = []
    unique_ids = df[eid_col].unique()

    for eid in unique_ids:
        if pd.isna(eid) or str(eid).lower()
