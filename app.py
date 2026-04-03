import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

st.set_page_config(page_title="Orange House HR Pro", layout="wide")

# --- CSS for Professional Reports ---
st.markdown("<style>.header {font-size:24px; font-weight:bold; text-align:center; color:#d35400;} .title {text-align:center; text-decoration:underline;}</style>", unsafe_allow_html=True)

# --- Helper: Safe Time Parsing ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() == '' or str(val).lower() == 'nan': return None
    try:
        if isinstance(val, time): return val
        if isinstance(val, datetime): return val.time()
        v_str = str(val).strip()[:5]
        return datetime.strptime(v_str, '%H:%M').time()
    except: return None

# --- Session State to Prevent Data Loss ---
if 'hr_master' not in st.session_state:
    st.session_state.hr_master = None

# --- Smart Processor ---
def smart_process(df, holidays):
    # Column cleaning
    df.columns = [str(c).strip().split('.')[0] for c in df.columns]
    all_cols = df.columns.tolist()
    
    # Picking first two columns as ID and Name regardless of their spelling
    eid_col, name_col = all_cols[0], all_cols[1]
    df[eid_col] = df[eid_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    # Finding date columns (1-31)
    dates = [c for c in all_cols if c.isdigit() and 1 <= int(c) <= 31]
    
    rows = []
    for eid in df[eid_col].unique():
        if pd.isna(eid) or "id" in str(eid).lower(): continue
        block = df[df[eid_col] == eid].reset_index(drop=True)
        if len(block) < 4: continue
        
        name = block.iloc[0][name_col]
        for d in dates:
            day = int(d)
            st_val = str(block.iloc[0][d]).strip().upper()
            in_t, out_t = parse_t(block.iloc[1][d]), parse_t(block.iloc[2][d])
            try: dur = float(block.iloc[3][d]) * 24 if pd.notna(block.iloc[3][d]) else 0
            except: dur = 0
            
            is_h = (day in holidays) or any(x in st_val for x in ['WO', 'WOP', 'W'])
            
            # Logic: P, A, HD, Miss Punch
            res = {"Emp ID": str(eid), "Name": name, "Date": day, "In": in_t, "Out": out_t, "Dur": dur, "Is_H": is_h}
            if (in_t and not out_t) or (not in_t and out_t):
                res["Status"], res["Miss"] = "A", 1
            elif in_t and out_t:
                res["Miss"] = 0
                res["Late"] = 1 if in_t > time(9, 35) else 0
                res["Early"] = 1 if dur < 8.5 and not is_h else 0
                if 3.5 <= dur <= 5.5: res["Status"] = "HD"
                elif is_h: res["Status"] = st_val if st_val != "NAN" else "WO"
                elif in_t >= time(10, 16): res["Status"] = "AB/"
                else: res["Status"] = "P"
            else:
                res["Status"] = st_val if is_h else "A"
                res["Miss"], res["Late"], res["Early"] = 0, 0, 0
            rows.append(res)
    return pd.DataFrame(rows)

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    u_file = st.file_uploader("Upload Excel", type=['xlsx'])
    h_days = st.multiselect("Select Holidays:", range(1, 32))
    st.markdown("---")
    report = st.selectbox("Switch View:", ["Muster", "Summary", "Exceptions", "Half-Day", "Penalty", "Correction"])

# --- Main App ---
if u_file and st.session_state.hr_master is None:
    # Row 2 contains headers (1,2,3...)
    raw = pd.read_excel(u_file, header=1)
    st.session_state.hr_master = smart_process(raw, h_days)

if st.session_state.hr_master is not None:
    data = st.session_state.hr_master
    st.markdown('<p class="header">Orange House Pvt Ltd.</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="title">{report} Report</p>', unsafe_allow_html=True)

    if report == "Muster":
        st.dataframe(data.pivot(index=["Emp ID", "Name"], columns="Date", values="Status"))
    elif report == "Summary":
        summ = data.groupby(["Emp ID", "Name"]).agg(
            Present=('Status', lambda x: (x == 'P').sum()),
            Absent=('Status', lambda x: (x == 'A').sum()),
            Late=('Late', 'sum'), Early=('Early', 'sum')
        ).reset_index()
        st.table(summ)
    elif report == "Exceptions":
        st.table(data.groupby(["Emp ID", "Name"]).agg(Miss_Punch=('Miss', 'sum'), Late=('Late', 'sum'), Early=('Early', 'sum')).reset_index())
    elif report == "Half-Day":
        st.table(data[data["Status"] == "HD"][["Emp ID", "Name", "Date", "In", "Out"]])
    elif report == "Correction":
        miss = data[data["Miss"] == 1]
        for i, r in miss.iterrows():
            with st.expander(f"Fix {r['Name']} - Date {r['Date']}"):
                ni, no = st.text_input("In", "09:30", key=f"i{i}"), st.text_input("Out", "18:30", key=f"o{i}")
                if st.button("Save", key=f"s{i}"):
                    st.session_state.hr_master.at[i, 'In'] = datetime.strptime(ni, '%H:%M').time()
                    st.session_state.hr_master.at[i, 'Out'] = datetime.strptime(no, '%H:%M').time()
                    st.rerun()
else:
    st.info("Sidebar se Excel file upload karein.")
