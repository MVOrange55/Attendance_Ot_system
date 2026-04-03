import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- 1. CONFIG & NAVIGATION ---
NAV_OPTIONS = [
    "Attendance Muster (Monthly)", 
    "Attendance Summary", 
    "Exception Report", 
    "Half Day Report", 
    "Continuous Absenteeism", 
    "Late Penalty Report"
]
st.set_page_config(page_title="Orange House HR Dashboard", layout="wide")

# --- 2. PROFESSIONAL UI STYLE ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #FFF5EE; border-right: 2px solid #FF4500; }
    .main-title { color: #D35400; font-size: 35px; font-weight: bold; text-align: center; margin-top: -50px; }
    .report-box { background-color: #FF4500; color: white; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 20px;}
    .stDataFrame { border: 1px solid #FF4500; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. UTILITY FUNCTIONS ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00']: return None
    try:
        if isinstance(v, time): return v
        return datetime.strptime(str(v).strip()[:5], '%H:%M').time()
    except: return None

def time_to_min(t):
    return t.hour * 60 + t.minute if t else 0

def format_min_to_str(total_min):
    if total_min <= 0: return ""
    h, m = divmod(int(total_min), 60)
    return f"{h}h {m}m"

# --- 4. CORE DATA ENGINE ---
def process_data(df, hols):
    df.columns = [str(c).strip() for c in df.columns]
    id_col, name_col = df.columns[0], df.columns[1]
    df[id_col] = df[id_col].ffill()
    df[name_col] = df[name_col].ffill()
    dates = [c for c in df.columns if c.isdigit()]
    output = []

    for eid in df[id_col].unique():
        if pd.isna(eid) or "id" in str(eid).lower(): continue
        block = df[df[id_col] == eid].reset_index(drop=True)
        if len(block) < 4: continue
        ename = block.iloc[0][name_col]
        clean_id = str(int(float(eid))) if str(eid).replace('.','').isdigit() else str(eid)
        
        for d in dates:
            st_val = str(block.iloc[0][d]).strip().upper()
            tin, tout = parse_t(block.iloc[1][d]), parse_t(block.iloc[2][d])
            try:
                raw_dur = str(block.iloc[3][d])
                dur = (int(raw_dur.split(':')[0]) + int(raw_dur.split(':')[1])/60) if ':' in raw_dur else float(raw_dur)*24
            except: dur = 0
            
            ish, is_wo = (int(d) in hols), any(x in st_val for x in ['WO', 'WOP'])
            row = {"Emp ID": clean_id, "Name": ename, "Date": int(d), "In": tin, "Out": tout, "Dur": dur}
            
            # --- Late In Calculation (Standard 09:35 AM) ---
            late_m = max(0, time_to_min(tin) - time_to_min(time(9, 35))) if tin else 0
            row["Late_Time"] = format_min_to_str(late_m)
            row["Late"] = 1 if late_m > 0 else 0
            
            # --- Early Out Calculation (Standard 06:00 PM / 18:00) ---
            early_m = max(0, time_to_min(time(18, 0)) - time_to_min(tout)) if tout and tout < time(18, 0) else 0
            row["Early_Time"] = format_min_to_str(early_m)
            row["Early"] = 1 if early_m > 0 else 0

            # --- Status Logic ---
            if tin and tout:
                if 3.5 <= dur <= 5.5: row["Status"] = "HD"
                elif ish: row["Status"] = "NH"
                elif is_wo: row["Status"] = "WO"
                elif tin >= time(10, 16): row["Status"] = "AB/"
                else: row["Status"] = "P"
                row["Miss"] = 0
            elif tin or tout:
                row["Status"], row["Miss"] = "A", 1
            else:
                row["Status"] = "NH" if ish else ("WO" if is_wo else "A")
                row["Miss"] = 0
            output.append(row)
    return pd.DataFrame(output)

# --- 5. MAIN DASHBOARD ---
if 'db' not in st.session_state: st.session_state.db = None
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/912/912318.png", width=80)
    f = st.file_uploader("Upload Excel", type=['xlsx'])
    h = st.multiselect("National Holidays (Dates):", range(1, 32))
    mode = st.selectbox("Navigation Menu:", NAV_OPTIONS)

st.markdown('<p class="main-title">Orange House Pvt Ltd.</p>', unsafe_allow_html=True)

if f:
    if st.session_state.db is None or st.sidebar.button("Refresh Data"):
        st.session_state.db = process_data(pd.read_excel(f), h)
    
    db = st.session_state.db
    st.markdown(f'<div class="report-box"><h3>{mode}</h3></div>', unsafe_allow_html=True)

    # --- 6. ATTENDANCE SUMMARY REPORT ---
    if mode == "Attendance Summary":
        summ = db.groupby(["Emp ID", "Name"]).agg(
            Present=('Status', lambda x: (x == 'P').sum()),
            Absent=('Status', lambda x: (x == 'A').sum() + (x == 'AB/').sum()),
            HD=('Status', lambda x: (x == 'HD').sum()),
            Late_Count=('Late', 'sum'),
            # Dates of Late Coming
            Late_Dates=('Date', lambda x: ", ".join(db.loc[x.index][db.loc[x.index, 'Late']==1]['Date'].astype(str)))
        ).reset_index()
        summ.insert(0, 'Sr No', range(1, len(summ) + 1))
        st.dataframe(summ, use_container_width=True, hide_index=True)

    # --- 7. EXCEPTION REPORT (DETAILED) ---
    elif mode == "Exception Report":
        # Filter rows where there's an exception (Late, Early, or Miss Punch)
        ex_db = db[(db['Late'] == 1) | (db['Early'] == 1) | (db['Miss'] == 1)].copy()
        
        # Select and rename columns for clarity
        ex_view = ex_db[["Emp ID", "Name", "Date", "In", "Late_Time", "Out", "Early_Time", "Status"]]
        ex_view.columns = ["Emp ID", "Name", "Date", "In Time", "Late By", "Out Time", "Early By", "Status"]
        
        ex_view.insert(0, 'Sr No', range(1, len(ex_view) + 1))
        st.dataframe(ex_view, use_container_width=True, hide_index=True)

    # --- 8. ATTENDANCE MUSTER (MONTHLY) ---
    elif mode == "Attendance Muster (Monthly)":
        m = db.pivot(index=["Emp ID", "Name"], columns="Date", values="Status").reset_index()
        m.insert(0, 'Sr No', range(1, len(m) + 1))
        st.dataframe(m, use_container_width=True, hide_index=True)

    # ... Other reports can be added similarly ...
else:
    st.info("Sidebar se Excel file upload karein.")
