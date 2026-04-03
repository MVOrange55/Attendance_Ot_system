import streamlit as st
import pandas as pd
from datetime import datetime, time

# --- 1. PERMANENT NAVIGATION LOCK ---
NAV_OPTIONS = [
    "Attendance Muster (Monthly)", 
    "Attendance Summary", 
    "Exception Report", 
    "Half Day Report", 
    "Continuous Absenteeism", 
    "Late Penalty Report"
]

st.set_page_config(page_title="Orange House HR Dashboard", layout="wide")

# --- 2. CUSTOM STYLING ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #FFF5EE; border-right: 2px solid #FF4500; }
    .main-title { color: #D35400; font-size: 35px; font-weight: bold; text-align: center; margin-top: -50px; }
    .report-box { background-color: #FF4500; color: white; padding: 10px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00']: return None
    try:
        if isinstance(v, time): return v
        if isinstance(v, datetime): return v.time()
        return datetime.strptime(str(v).strip()[:5], '%H:%M').time()
    except: return None

def get_duration_str(hrs):
    if hrs <= 0: return "0 Hours 0 Minutes"
    h = int(hrs)
    m = int(round((hrs - h) * 60))
    return f"{h} Hours {m} Minutes"

# --- 4. CORE ENGINE (POSITION BASED) ---
def process_data(df, hols):
    # Position based logic: 0 = ID, 1 = Name
    df.columns = [str(c).strip() for c in df.columns]
    id_col = df.columns[0]
    name_col = df.columns[1]
    
    # Fill ID and Name downwards for the 4-row blocks
    df[id_col] = df[id_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    dates = [c for c in df.columns if c.isdigit()]
    output = []

    for eid in df[id_col].unique():
        if pd.isna(eid) or "id" in str(eid).lower(): continue
        block = df[df[id_col] == eid].reset_index(drop=True)
        if len(block) < 4: continue
        
        ename = block.iloc[0][name_col]
        # ID format fix: 1045.0 to 1045
        clean_id = str(int(float(eid))) if str(eid).replace('.','').isdigit() else str(eid)
        
        for d in dates:
            # 0=Status, 1=In, 2=Out, 3=Total
            st_val = str(block.iloc[0][d]).strip().upper()
            tin, tout = parse_t(block.iloc[1][d]), parse_t(block.iloc[2][d])
            try:
                raw_dur = str(block.iloc[3][d])
                dur = (int(raw_dur.split(':')[0]) + int(raw_dur.split(':')[1])/60) if ':' in raw_dur else float(raw_dur)*24
            except: dur = 0
            
            ish = (int(d) in hols) or any(x in st_val for x in ['WO', 'W'])
            
            row = {"Emp ID": clean_id, "Name": ename, "Date": int(d), "In": tin, "Out": tout, "Dur": dur}
            
            if tin and tout:
                row["Late"] = 1 if tin > time(9, 35) else 0
                row["Early"] = 1 if dur < 8.5 and not ish else 0
                row["Status"] = "HD" if 3.5 <= dur <= 5.5 else (st_val if ish else "P")
                if not ish and tin >= time(10, 16): row["Status"] = "AB/"
                row["Miss"] = 0
            elif tin or tout:
                row["Status"], row["Miss"], row["Late"], row["Early"] = "A", 1, 0, 0
            else:
                row["Status"] = st_val if ish else "A"
                row["Miss"], row["Late"], row["Early"] = 0, 0, 0
            output.append(row)
            
    return pd.DataFrame(output)

# --- 5. SIDEBAR ---
if 'processed_db' not in st.session_state: st.session_state.processed_db = None

with st.sidebar:
    st.markdown("### 🍊 Admin Panel")
    f = st.file_uploader("Upload Excel", type=['xlsx'])
    h = st.multiselect("Holidays:", range(1, 32))
    st.markdown("---")
    # PERMANENTLY LOCKED NAVIGATION
    mode = st.selectbox("Navigation Menu:", NAV_OPTIONS)

# --- 6. MAIN DISPLAY ---
st.markdown('<p class="main-title">Orange House Pvt Ltd.</p>', unsafe_allow_html=True)

if f:
    if st.session_state.processed_db is None:
        st.session_state.processed_db = process_data(pd.read_excel(f), h)
    
    res = st.session_state.processed_db
    st.markdown(f'<div class="report-box"><h3>{mode}</h3></div>', unsafe_allow_html=True)
    st.write("")

    if mode == "Attendance Muster (Monthly)":
        # Using exact column names created in process_data
        m = res.pivot(index=["Emp ID", "Name"], columns="Date", values="Status").reset_index()
        m.insert(0, 'Sr No', range(1, len(m) + 1))
        st.dataframe(m, use_container_width=True, hide_index=True)

    elif mode == "Attendance Summary":
        s = res.groupby(["Emp ID", "Name"]).agg(Present=('Status', lambda x: (x == 'P').sum()), Absent=('Status', lambda x: (x == 'A').sum()), Late=('Late', 'sum')).reset_index()
        s.insert(0, 'Sr No', range(1, len(s) + 1))
        st.table(s)

    elif mode == "Exception Report":
        e = res.groupby(["Emp ID", "Name"]).agg(Late_In=('Late', 'sum'), Early_Out=('Early', 'sum'), Miss_Punch=('Miss', 'sum')).reset_index()
        e.insert(0, 'Sr No', range(1, len(e) + 1))
        st.table(e)

    elif mode == "Half Day Report":
        hd = res[res["Status"] == "HD"].copy()
        hd["Working Duration"] = hd["Dur"].apply(get_duration_str)
        hd_view = hd[["Emp ID", "Name", "Date", "In", "Out", "Working Duration"]].reset_index(drop=True)
        hd_view.insert(0, 'Sr No', range(1, len(hd_view) + 1))
        st.table(hd_view)

    elif mode == "Late Penalty Report":
        l = res.groupby(["Emp ID", "Name"]).agg(Total_Late=('Late', 'sum')).reset_index()
        l.insert(0, 'Sr No', range(1, len(l) + 1))
        st.table(l)

    elif mode == "Continuous Absenteeism":
        c = res[res["Status"] == "A"].groupby(["Emp ID", "Name"]).size().reset_index(name='Total Absents')
        c = c[c['Total Absents'] >= 3]
        c.insert(0, 'Sr No', range(1, len(c) + 1))
        st.table(c)
else:
    st.info("Kripya Excel file upload karein.")
