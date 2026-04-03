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

# --- 2. PAGE CONFIG ---
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
    m = int(round((hours_decimal - h) * 60))
    return f"{h} Hours {m} Minutes"

# --- 5. DATA ENGINE (FIXED FOR KEYERROR) ---
def process_hr_data(df, hols):
    # Column cleaning to avoid KeyError
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
        # Clean ID: 1045.0 -> 1045
        try:
            clean_eid = str(int(float(eid)))
        except:
            clean_eid = str(eid)
        
        for d in date_cols:
            st_val = str(block.iloc[0][d]).strip().upper()
            in_t = parse_time_safe(block.iloc[1][d])
            out_t = parse_time_safe(block.iloc[2][d])
            
            try:
                raw_d = str(block.iloc[3][d])
                dur = (int(raw_d.split(':')[0]) + int(raw_d.split(':')[1])/60) if ':' in raw_d else float(raw_d)*24
            except: dur = 0
            
            is_holiday = (int(d) in hols) or any(x in st_val for x in ['WO', 'W'])
            
            # Base entry with exact column names to match reports
            entry = {"Emp ID": clean_eid, "Name": emp_name, "Date": int(d), "In": in_t, "Out": out_t, "Dur": dur}
            
            if in_t and out_t:
                entry["Late"] = 1 if in_t > time(9, 35) else 0
                entry["Early"] = 1 if dur < 8.5 and not is_holiday else 0
                entry["Status"] = "HD" if 3.5 <= dur <= 5.5 else (st_val if is_holiday else "P")
                if not is_holiday and in_t >= time(10, 16): entry["Status"] = "AB/"
                entry["Miss"] = 0
            elif in_t or out_t:
                entry["Status"], entry["Miss"], entry["Late"], entry["Early"] = "A", 1, 0, 0
            else:
                entry["Status"] = st_val if is_holiday else "A"
                entry["Miss"], entry["Late"], entry["Early"] = 0, 0, 0
            
            processed_data.append(entry)
            
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
        # Using exact column names "Emp ID", "Name", "Date" and "Status"
        muster = db.pivot(index=["Emp ID", "Name"], columns="Date", values="Status").reset_index()
        muster.insert(0, 'Sr No', range(1, len(muster) + 1))
        st.dataframe(muster, use_container_width=True, hide_index=True)

    elif report_choice == "Attendance Summary":
        summ = db.groupby(["Emp ID", "Name"]).agg(
            Present=('Status', lambda x: (x == 'P').sum()),
            Absent=('Status', lambda x: (x == 'A').sum()),
            Late_Days=('Late', 'sum')
        ).reset_index()
        summ.insert(0, 'Sr No', range(1, len(summ) + 1))
        st.table(summ)

    elif report_choice == "Exception Report":
        # Fixed column names in aggregation
        ex = db.groupby(["Emp ID", "Name"]).agg(
            Late_In=('Late', 'sum'), 
            Early_Out=('Early', 'sum'), 
            Miss_Punch=('Miss', 'sum')
        ).reset_index()
        ex.insert(0, 'Sr No', range(1, len(ex) + 1))
        st.table(ex)

    elif report_choice == "Half Day Report":
        hd = db[db["Status"] == "HD"].copy()
        hd["Working Hours"] = hd["Dur"].apply(format_duration)
        hd_disp = hd[["Emp ID", "Name", "Date", "In", "Out", "Working Hours"]].reset_index(drop=True)
        hd_disp.insert(0, 'Sr No', range(1, len(hd_disp) + 1))
        st.table(hd_disp)

    elif report_choice == "Late Penalty Report":
        lp = db.groupby(["Emp ID", "Name"]).agg(Total_Late=('Late', 'sum')).reset_index()
        lp.insert(0, 'Sr No', range(1, len(lp) + 1))
        st.table(lp)

    elif report_choice == "Continuous Absenteeism":
        ca = db[db["Status"] == "A"].groupby(["Emp ID", "Name"]).size().reset_index(name='Total Absents')
        ca = ca[ca['Total Absents'] >= 3]
        ca.insert(0, 'Sr No', range(1, len(ca) + 1))
        st.table(ca)
else:
    st.info("Sidebar se file upload karein.")
