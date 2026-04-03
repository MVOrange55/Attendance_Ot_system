import streamlit as st
import pandas as pd
from datetime import datetime, time

# --- 1. PERMANENT NAVIGATION LOCK ---
NAV_MENU = [
    "Attendance Muster (Monthly)", 
    "Attendance Summary", 
    "Exception Report", 
    "Half Day Report", 
    "Continuous Absenteeism", 
    "Late Penalty Report"
]

# --- 2. PAGE CONFIG & BRANDING ---
st.set_page_config(page_title="Orange House HR System", layout="wide")

# --- 3. CUSTOM CSS ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #FFF5EE; border-right: 2px solid #FF4500; }
    .main-title { color: #D35400; font-size: 38px; font-weight: bold; text-align: center; text-decoration: underline; margin-top: -60px; }
    .report-header { background: linear-gradient(90deg, #FF4500, #FFA500); color: white; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. UTILS ---
def parse_time_safe(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '00:00']: return None
    try:
        if isinstance(val, time): return val
        if isinstance(val, datetime): return val.time()
        return datetime.strptime(str(val).strip()[:5], '%H:%M').time()
    except: return None

def format_duration(hours_decimal):
    if hours_decimal <= 0: return "0 Hours 0 Minutes"
    h = int(hours_decimal)
    m = int((hours_decimal - h) * 60)
    return f"{h} Hours {m} Minutes"

# --- 5. DATA ENGINE (4-ROW PATTERN) ---
def process_hr_data(df, hols):
    df.columns = [str(c).strip() for c in df.columns]
    eid_col, name_col = df.columns[0], df.columns[1]
    df[eid_col] = df[eid_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    date_cols = [c for c in df.columns if c.isdigit()]
    processed_data = []

    for eid in df[eid_col].unique():
        if pd.isna(eid) or "id" in str(eid).lower(): continue
        block = df[df[eid_col] == eid].reset_index(drop=True)
        if len(block) < 4: continue
        
        emp_name = block.iloc[0][name_col]
        # ID format fix: 1045.0 to 1045
        clean_eid = str(int(float(eid))) if str(eid).replace('.','').isdigit() else str(eid)
        
        for d in date_cols:
            st_val = str(block.iloc[0][d]).strip().upper()
            in_t, out_t = parse_time_safe(block.iloc[1][d]), parse_time_safe(block.iloc[2][d])
            try:
                raw_d = str(block.iloc[3][d])
                dur = (int(raw_d.split(':')[0]) + int(raw_d.split(':')[1])/60) if ':' in raw_d else float(raw_d)*24
            except: dur = 0
            
            is_holiday = (int(d) in hols) or any(x in st_val for x in ['WO', 'W'])
            res = {"Emp ID": clean_eid, "Name": emp_name, "Date": int(d), "In": in_t, "Out": out_t, "Dur": dur, "Is_H": is_holiday}
            
            if in_t and out_t:
                res["Late"] = 1 if in_t > time(9, 35) else 0
                res["Early"] = 1 if dur < 8.5 and not is_holiday else 0
                res["Status"] = "HD" if 3.5 <= dur <= 5.5 else (st_val if is_holiday else "P")
                if not is_holiday and in_t >= time(10, 16): res["Status"] = "AB/"
                res["Miss"] = 0
            elif in_t or out_t:
                res["Status"], res["Miss"] = "A", 1
            else:
                res["Status"] = st_val if is_holiday else "A"
                res["Miss"] = 0
            processed_data.append(res)
    return pd.DataFrame(processed_data)

# --- 6. SIDEBAR ---
if 'final_db' not in st.session_state: st.session_state.final_db = None

with st.sidebar:
    st.markdown("## 🍊 Orange House HR")
    uploaded_file = st.file_uploader("📤 Upload Attendance Excel", type=['xlsx'])
    sel_hols = st.multiselect("🗓️ Select Holidays:", range(1, 32))
    report_choice = st.selectbox("Switch Report View:", NAV_MENU)

# --- 7. MAIN DASHBOARD ---
st.markdown('<p class="main-title">Orange House Pvt Ltd.</p>', unsafe_allow_html=True)

if uploaded_file:
    if st.session_state.final_db is None:
        st.session_state.final_db = process_hr_data(pd.read_excel(uploaded_file), sel_hols)
    
    db = st.session_state.final_db
    st.markdown(f'<div class="report-header"><h3>{report_choice}</h3></div>', unsafe_allow_html=True)

    if report_choice == "Attendance Muster (Monthly)":
        muster = db.pivot(index=["Emp ID", "Name"], columns="Date", values="Status").reset_index()
        muster.index = range(1, len(muster) + 1)
        muster.index.name = "Sr No"
        st.dataframe(muster.reset_index(), use_container_width=True)

    elif report_choice == "Attendance Summary":
        summ = db.groupby(["Emp ID", "Name"]).agg(Present=('Status', lambda x: (x == 'P').sum()), Absent=('Status', lambda x: (x == 'A').sum()), Late=('Late', 'sum')).reset_index()
        summ.index = range(1, len(summ) + 1)
        summ.index.name = "Sr No"
        st.table(summ.reset_index())

    elif report_choice == "Exception Report":
        ex = db.groupby(["Emp ID", "Name"]).agg(Late_In=('Late', 'sum'), Early_Out=('Early', 'sum'), Miss_Punch=('Miss', 'sum')).reset_index()
        ex.index = range(1, len(ex) + 1)
        ex.index.name = "Sr No"
        st.table(ex.reset_index())

    elif report_choice == "Half Day Report":
        hd = db[db["Status"] == "HD"].copy()
        hd["Duration"] = hd["Dur"].apply(format_duration)
        hd_disp = hd[["Emp ID", "Name", "Date", "In", "Out", "Duration"]].reset_index(drop=True)
        hd_disp.index = range(1, len(hd_disp) + 1)
        hd_disp.index.name = "Sr No"
        st.table(hd_disp.reset_index())

    elif report_choice == "Late Penalty Report":
        lp = db.groupby(["Emp ID", "Name"]).agg(Total_Late=('Late', 'sum')).reset_index()
        lp.index = range(1, len(lp) + 1)
        lp.index.name = "Sr No"
        st.table(lp.reset_index())

    elif report_choice == "Continuous Absenteeism":
        ca = db[db["Status"] == "A"].groupby(["Emp ID", "Name"]).size().reset_index(name='Total Absents')
        ca.index = range(1, len(ca) + 1)
        ca.index.name = "Sr No"
        st.table(ca.reset_index())
else:
    st.info("Sidebar se file upload karein.")
