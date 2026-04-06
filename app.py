import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIG ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")
st.title("📊 Orange House HR Master System")

# --- 2. HELPERS ---
def parse_time_safe(val):
    if pd.isna(val) or str(val).strip().lower() in ['', 'nan', '0', '00:00', 'none', 'null']: 
        return None
    try:
        v = str(val).strip()
        if ':' in v: return datetime.strptime(v[:5], '%H:%M').time()
        else: return (datetime(1900, 1, 1) + timedelta(days=float(v))).time()
    except: return None

def get_ot(work_hrs, status, is_h):
    # Rule: Agar Holiday/Sunday (is_h) hai, toh Pura Time OT hai.
    if is_h: 
        ot_val = work_hrs 
    elif status == "AB/": 
        ot_val = max(0, work_hrs - 4.0)
    else: 
        ot_val = max(0, work_hrs - 8.5)
    
    if ot_val <= 0: return 0
    h = int(ot_val)
    m = (ot_val - h) * 60
    # 15-min Rounding Logic
    if m < 15: rm = 0
    elif m < 30: rm = 0.25
    elif m < 45: rm = 0.50
    elif m < 60: rm = 0.75
    else: h += 1; rm = 0
    return h + rm

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.header("Settings")
uploaded_file = st.sidebar.file_uploader("1. Upload Attendance Excel", type=['xlsx'])

# Dynamic Holiday Selection (Aap khud dates select karein)
selected_holidays = st.sidebar.multiselect(
    "2. Select Holidays/Sundays (Full OT Days)",
    options=list(range(1, 32)),
    default=[] # Aap yahan 1, 8, 15... select kar sakte hain
)

report_choice = st.sidebar.selectbox("3. Select Report to View", 
    ["1. Attendance Muster", "2. OT Report", "3. Exception Summary", "4. Exception Detailed", "5. Miss Punch", "6. Final Summary"])

# --- 4. PROCESSING ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [str(c).strip() for c in df.columns]
        id_col, name_col = df.columns[0], df.columns[1]
        df[id_col], df[name_col] = df[id_col].ffill(), df[name_col].ffill()
        date_cols = [c for c in df.columns if c.replace('.0','').isdigit()]
        
        if not date_cols:
            st.error("❌ Excel mein Dates (1, 2, 3...) nahi mili. Headers check karein.")
            st.stop()

        muster, ot_rep, ex_sum, ex_det, miss_list, final_sum = [], [], [], [], [], []

        for eid in df[id_col].unique():
            if pd.isna(eid): continue
            e_data = df[df[id_col] == eid].reset_index(drop=True)
            ename, type_col = str(e_data.iloc[0][name_col]), e_data.columns[2]
            in_row = e_data[e_data[type_col].astype(str).str.contains('In', case=False, na=False)].head(1)
            out_row = e_data[e_data[type_col].astype(str).str.contains('Out', case=False, na=False)].head(1)
