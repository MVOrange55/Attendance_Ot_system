import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #fdf2e9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #d35400; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '0,00', '0', '00:00']: return None
    try:
        # Handle excel float times or string times
        val_str = str(val).strip()
        if ':' in val_str:
            return datetime.strptime(val_str[:5], '%H:%M').time()
        else:
            return (datetime(1900, 1, 1) + timedelta(days=float(val_str))).time()
    except: return None

def calculate_final_ot(total_hrs, is_full_ot_day):
    # Agar WO/Holiday hai toh pura time, varna 8.5 hrs minus
    ot_exact = total_hrs if is_full_ot_day else max(0, total_hrs - 8.5)
    
    if ot_exact <= 0: return 0
    
    hours = int(ot_exact)
    minutes = (ot_exact - hours) * 60
    
    # 15-minute Rounding Logic
    if minutes < 15: rounded_min = 0
    elif minutes < 30: rounded_min = 0.25
    elif minutes < 45: rounded_min = 0.50
    elif minutes < 60: rounded_min = 0.75
    else:
        hours += 1
        rounded_min = 0
    return hours + rounded_min

def get_excel_download(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- 3. MASTER PROCESSING ENGINE ---
def process_hr_system(df, nh_list):
    df.columns = [str(c).strip() for c in df.columns]
    id_col, name_col = df.columns[0], df.columns[1]
    
    # Header logic (Status row identification)
    header_col = next((c for c in df.columns if any(x in str(c).lower() for x in ['date', 'type', 'status'])), df.columns[2])
    
    df[id_col] = df[id_col].ffill()
    df[name_col] = df[name_col].ffill()
    dates = [c for c in df.columns if str(c).replace('.0','').isdigit()]
    
    muster, ot_rep, ex_sum, ex_det, miss_p = [], [], [], [], []

    for eid in df[id_col].unique():
        if pd.isna(eid): continue
        block = df[df[id_col] == eid].reset_index(drop=True)
        ename, emp_id = block.iloc[0][name_col], str(eid).replace('.0','')
        
        row_m, row_ot = {"Emp ID": emp_id, "Name": ename}, {"Emp ID": emp_id, "Name": ename}
        l_cnt, e_cnt, ab_cnt, a_cnt, p_cnt, total_ot_month = 0, 0, 0, 0, 0, 0
        l_dt_tm, e_dt_tm, ab_dates = [], [], []
        sl_used_date = "--"

        for d in dates:
            # Row mapping: Status(0), In(1), Out(2)
            st_val = str(block.iloc[0][d]).strip().upper()
            t_in_raw = parse_t(block.iloc[1][d])
            t_out = parse_t(block.iloc[2][d])
            
            day_num = int(float(d))
            is_full_ot_day = (day_num in nh_list) or ('WO' in st_val)

            # Rule: Miss Punch
            if (t_in_raw and not t_out) or (not t_in_raw and t_out):
                miss_p.append({
                    "Emp ID": emp_id, "Name": ename, "Date
