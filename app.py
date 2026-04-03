import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# Page Setup
st.set_page_config(page_title="Orange House HR Automation", layout="wide")

# --- UI Header ---
st.markdown("<h2 style='text-align: center; color: #d35400;'>Orange House Pvt Ltd.</h2>", unsafe_allow_html=True)

# --- Robust Time Parser ---
def parse_time_safe(val):
    if pd.isna(val) or str(val).strip() == '' or str(val).lower() == 'nan':
        return None
    try:
        if isinstance(val, time): return val
        if isinstance(val, datetime): return val.time()
        v_str = str(val).strip()[:5]
        return datetime.strptime(v_str, '%H:%M').time()
    except:
        return None

# --- Main Processor with Column Safety ---
def process_data(df, holidays):
    # Clean column names
    df.columns = [str(c).strip().split('.')[0] for c in df.columns]
    cols = df.columns.tolist()
    
    # Dynamically find ID and Name columns
    eid_col = cols[0]
    name_col = cols[1]
    
    df[eid_col] = df[eid_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    # Identify Date columns (1-31)
    date_cols = [c for c in cols if c.isdigit() and 1 <= int(c) <= 31]
    
    results = []
    for eid in df[eid_col].unique():
        if pd.isna(eid) or "id" in str(eid).lower():
            continue
            
        block = df[df[eid_col] == eid].reset_index(drop=True)
        if len(block) < 4: continue
        
        name = block.iloc[0][name_col]
        
        for d in date_cols:
            day_num = int(d)
            st_val = str(block.iloc[0][d]).strip().upper()
            in_t = parse_time_safe(block.iloc[1][d])
            out_t = parse_time_safe(block.iloc[2][d])
            
            try:
                dur = float(block.iloc[3][d]) * 24 if pd.notna(block.iloc[3][d]) else 0
            except:
                dur = 0
                
            is_h = (day_num in holidays) or any(x in st_val for x in ['WO', 'WOP', 'W'])
            
            res = {"Emp ID": str(eid), "Name": name, "Date": day_num, "In": in_t, "Out": out_t, "Dur": dur, "Is_H": is_h}
            
            # Status Logic
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
            
            results.append(res)
            
    return pd.DataFrame(results)

# --- Sidebar & Navigation ---
if 'final_data' not in st.session_state:
    st.session_state.final_data = None

with st.sidebar:
    st.header("Admin Settings")
    u_file = st.file_uploader("Upload Excel", type=['xlsx'])
    h_days = st.multiselect("Holidays:", range(1, 32))
    st.markdown("---")
    page = st.selectbox("Navigation", [
        "Muster Report", "Summary Report", "Exception Report", 
        "Half Day Report", "Late Penalty", "Edit Punch"
    ])

# --- Logic Execution ---
if u_file and st.session_state.final_data is None:
    # Important: Row 2 contains the dates (1, 2, 3...)
    raw_df = pd.read_excel(u_file, header=1)
    st.session_state.final_data = process_data(raw_df, h_days)

if st.session_state.final_data is not None:
    data = st.session_state.final_data
    st.subheader(f"📊 {page}")

    if page == "Muster Report":
        # Safe Pivot to avoid KeyError
        muster = data.pivot(index=["Emp ID", "Name"], columns="Date", values="Status")
        st.dataframe(muster)

    elif page == "Summary Report":
        summary = data.groupby(["Emp ID", "Name"]).agg(
            Working_Days=('Status', lambda x: (x == 'P').sum() + (x == 'HD').sum()*0.5),
            Present=('Status', lambda x: (x == 'P').sum()),
            Absent=('Status', lambda x: (x == 'A').sum()),
            Late=('Late', 'sum'), Early_Out=('Early', 'sum')
        ).reset_index()
        st.table(summary)

    elif page == "Exception Report":
        excep = data.groupby(["Emp ID", "Name"]).agg(
            Late_In=('Late', 'sum'), Early_Out=('Early', 'sum'), 
            Miss_Punch=('Miss', 'sum'), Absents=('Status', lambda x: (x == 'A').sum())
        ).reset_index()
        st.table(excep)

    elif page == "Half Day Report":
        st.table(data[data["Status"] == "HD"][["Emp ID", "Name", "Date", "In", "Out"]])

    elif page == "Late Penalty":
        penalty = data.groupby(["Emp ID", "Name"]).agg(Late_Count=('Late', 'sum')).reset_index()
        st.table(penalty)

    elif page == "Edit Punch":
        miss = data[data["Miss"] == 1]
        for i, r in miss.iterrows():
            with st.expander(f"Fix {r['Name']} - Day {r['Date']}"):
                ni = st.text_input("New In", "09:30", key=f"in_{i}")
                no = st.text_input("New Out", "18:30", key=f"out_{i}")
                if st.button("Update", key=f"btn_{i}"):
                    st.session_state.final_data.at[i, 'In'] = datetime.strptime(ni, '%H:%M').time()
                    st.session_state.final_data.at[i, 'Out'] = datetime.strptime(no, '%H:%M').time()
                    st.rerun()
else:
    st.info("Sidebar se Excel file upload karein.")
