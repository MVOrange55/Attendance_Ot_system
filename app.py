import streamlit as st
import pandas as pd
from datetime import datetime, time

# --- 1. PERMANENT NAVIGATION LOCK ---
# Ye list hamesha fix rahegi, code change hone par bhi nahi badlegi
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

# --- 3. ATTRACTIVE CUSTOM CSS ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #FFF5EE;
        border-right: 2px solid #FF4500;
    }
    .main-title {
        color: #D35400;
        font-size: 38px;
        font-weight: bold;
        text-align: center;
        text-decoration: underline;
        margin-top: -60px;
    }
    .report-header {
        background: linear-gradient(90deg, #FF4500, #FFA500);
        color: white;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .stTable {
        border: 1px solid #FF4500;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. UTILS & TIME PARSING ---
def parse_time_safe(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '00:00']: return None
    try:
        if isinstance(val, time): return val
        if isinstance(val, datetime): return val.time()
        t_str = str(val).strip()[:5]
        return datetime.strptime(t_str, '%H:%M').time()
    except: return None

# --- 5. DATA ENGINE (4-ROW PATTERN) ---
def process_hr_data(df, hols):
    # Column cleaning
    df.columns = [str(c).strip() for c in df.columns]
    eid_col, name_col = df.columns[0], df.columns[1]
    
    # Fill ID and Name for the 4-row blocks
    df[eid_col] = df[eid_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    date_cols = [c for c in df.columns if c.isdigit()]
    processed_data = []

    # Get unique employees
    ids = df[eid_col].unique()
    for eid in ids:
        if pd.isna(eid) or "id" in str(eid).lower(): continue
        
        # Get the 4 rows for this employee
        block = df[df[eid_col] == eid].reset_index(drop=True)
        if len(block) < 4: continue
        
        emp_name = block.iloc[0][name_col]
        
        for d in date_cols:
            day_idx = int(d)
            # Pattern: 0=Status, 1=In, 2=Out, 3=Total/Duration
            st_val = str(block.iloc[0][d]).strip().upper()
            in_t = parse_time_safe(block.iloc[1][d])
            out_t = parse_time_safe(block.iloc[2][d])
            
            # Duration Calculation
            try:
                raw_d = str(block.iloc[3][d])
                if ':' in raw_d:
                    h, m = map(int, raw_d.split(':'))
                    dur = h + (m/60)
                else:
                    dur = float(raw_d) * 24
            except: dur = 0
            
            is_holiday = (day_idx in hols) or any(x in st_val for x in ['WO', 'W'])
            
            entry = {
                "ID": str(eid), "Name": emp_name, "Date": day_idx, 
                "In": in_t, "Out": out_t, "Dur": dur, "Is_H": is_holiday
            }
            
            # Logic for Status & Penalties
            if in_t and out_t:
                entry["Late"] = 1 if in_t > time(9, 35) else 0 # Late Rule
                entry["Early"] = 1 if dur < 8.5 and not is_holiday else 0
                
                if 3.5 <= dur <= 5.5: entry["Status"] = "HD"
                elif is_holiday: entry["Status"] = st_val if st_val != "NAN" else "WO"
                elif in_t >= time(10, 16): entry["Status"] = "AB/"
                else: entry["Status"] = "P"
                entry["Miss"] = 0
            elif in_t or out_t:
                entry["Status"], entry["Miss"], entry["Late"], entry["Early"] = "A", 1, 0, 0
            else:
                entry["Status"] = st_val if is_holiday else "A"
                entry["Miss"], entry["Late"], entry["Early"] = 0, 0, 0
            
            processed_data.append(entry)
            
    return pd.DataFrame(processed_data)

# --- 6. SIDEBAR & NAVIGATION ---
if 'final_db' not in st.session_state:
    st.session_state.final_db = None

with st.sidebar:
    st.markdown("## 🍊 Orange House HR")
    st.markdown("---")
    uploaded_file = st.file_uploader("📤 Upload Attendance Excel", type=['xlsx'])
    sel_hols = st.multiselect("🗓️ Select Holidays:", range(1, 32))
    
    st.markdown("---")
    st.markdown("### 🧭 Navigation")
    # LOCKED SELECTBOX
    report_choice = st.selectbox("Switch Report View:", NAV_MENU)
    st.markdown("---")
    st.caption("🔒 Navigation Menu is Locked")

# --- 7. MAIN DASHBOARD DISPLAY ---
st.markdown('<p class="main-title">Orange House Pvt Ltd.</p>', unsafe_allow_html=True)

if uploaded_file:
    if st.session_state.final_db is None:
        # Load from row 0 based on image
        raw_df = pd.read_excel(uploaded_file)
        st.session_state.final_db = process_hr_data(raw_df, sel_hols)
    
    db = st.session_state.final_db
    st.markdown(f'<div class="report-header"><h3>{report_choice}</h3></div>', unsafe_allow_html=True)

    if report_choice == "Attendance Muster (Monthly)":
        muster = db.pivot(index=["ID", "Name"], columns="Date", values="Status")
        st.dataframe(muster, use_container_width=True)

    elif report_choice == "Attendance Summary":
        # Rule: Present, Absent, Leave, Late
        summary = db.groupby(["ID", "Name"]).agg(
            Total_Days=('Date', 'nunique'),
            Present=('Status', lambda x: (x == 'P').sum()),
            Half_Day=('Status', lambda x: (x == 'HD').sum()),
            Absent=('Status', lambda x: (x == 'A').sum()),
            Late_Count=('Late', 'sum')
        ).reset_index()
        st.table(summary)

    elif report_choice == "Exception Report":
        # Rule: Late, Early Out, Miss Punch
        excep = db.groupby(["ID", "Name"]).agg(
            Late_In=('Late', 'sum'),
            Early_Out=('Early', 'sum'),
            Miss_Punch=('Miss', 'sum'),
            Absents=('Status', lambda x: (x == 'A').sum())
        ).reset_index()
        st.table(excep)

    elif report_choice == "Half Day Report":
        st.table(db[db["Status"] == "HD"][["ID", "Name", "Date", "In", "Out", "Dur"]])

    elif report_choice == "Late Penalty Report":
        st.table(db.groupby(["ID", "Name"]).agg(Late_Days=('Late', 'sum')).reset_index())

    elif report_choice == "Continuous Absenteeism":
        # Filter for employees with more than 3 absents
        cont_abs = db[db["Status"] == "A"].groupby(["ID", "Name"]).size().reset_index(name='Total_Absents')
        st.table(cont_abs[cont_abs['Total_Absents'] >= 3])

else:
    st.info("👋 Hello! Please upload the Monthly Attendance Excel file in the sidebar.")
