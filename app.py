import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

st.set_page_config(page_title="Orange House HR Automation", layout="wide")

# --- Styling ---
st.markdown("""
    <style>
    .header { font-size: 24px; font-weight: bold; text-align: center; color: #d35400; }
    .title { font-size: 18px; font-weight: bold; text-align: center; text-decoration: underline; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
def parse_time_safe(val):
    if pd.isna(val) or str(val).strip() == '' or str(val).lower() == 'nan': return None
    try:
        if isinstance(val, time): return val
        if isinstance(val, datetime): return val.time()
        v_str = str(val).strip()[:5]
        return datetime.strptime(v_str, '%H:%M').time()
    except: return None

# --- Session State ---
if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None

# --- Processor ---
def run_processor(df, holidays):
    df.columns = [str(c).strip().split('.')[0] for c in df.columns]
    cols = df.columns.tolist()
    eid_col, name_col = cols[0], cols[1]
    df[eid_col] = df[eid_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    date_cols = [c for c in cols if c.isdigit() and 1 <= int(c) <= 31]
    final_rows = []

    for eid in df[eid_col].unique():
        if pd.isna(eid) or "id" in str(eid).lower(): continue
        emp_block = df[df[eid_col] == eid].reset_index(drop=True)
        if len(emp_block) < 4: continue
        
        emp_name = emp_block.iloc[0][name_col]
        for d in date_cols:
            status_val = str(emp_block.iloc[0][d]).strip().upper()
            in_t = parse_time_safe(emp_block.iloc[1][d])
            out_t = parse_time_safe(emp_block.iloc[2][d])
            try: duration = float(emp_block.iloc[3][d]) * 24 if pd.notna(emp_block.iloc[3][d]) else 0
            except: duration = 0
            
            is_hol = (int(d) in holidays) or any(x in status_val for x in ['WO', 'WOP', 'W'])
            
            # Logic Rules
            res = {"Emp ID": str(eid), "Name": emp_name, "Date": int(d), "In": in_t, "Out": out_t, "Dur": duration, "Is_H": is_hol}
            
            if (in_t and not out_t) or (not in_t and out_t): 
                res["F_Status"], res["Miss"] = "A", True
            elif in_t and out_t:
                res["Miss"] = False
                res["Late"] = 1 if in_t > time(9, 35) else 0
                res["Early"] = 1 if duration < 8.5 and not is_hol else 0
                if 3.5 <= duration <= 5.5: res["F_Status"] = "HD"
                elif is_hol: res["F_Status"] = status_val if status_val != "NAN" else "WO"
                elif in_t >= time(10, 16): res["F_Status"] = "AB/"
                else: res["F_Status"] = "P"
            else:
                res["F_Status"] = status_val if is_hol else "A"
                res["Miss"], res["Late"], res["Early"] = False, 0, 0
                
            final_rows.append(res)
    return pd.DataFrame(final_rows)

# --- Sidebar ---
with st.sidebar:
    st.header("Orange House Admin")
    uploaded = st.file_uploader("Upload Monthly Excel", type=['xlsx'])
    hols = st.multiselect("Select Holidays:", range(1, 32))
    st.markdown("---")
    nav = st.selectbox("Select Report:", [
        "Attendance Muster", "Attendance Summary", "Exception Report", 
        "Half Day Report", "Late Penalty", "Edit Miss Punch"
    ])

# --- Main App ---
if uploaded and st.session_state.processed_df is None:
    raw = pd.read_excel(uploaded, header=1)
    st.session_state.processed_df = run_processor(raw, hols)

if st.session_state.processed_df is not None:
    f_df = st.session_state.processed_df
    
    st.markdown('<p class="header">Orange House Pvt Ltd.</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="title">{nav}</p>', unsafe_allow_html=True)

    if nav == "Attendance Muster":
        st.dataframe(f_df.pivot(index=["Emp ID", "Name"], columns="Date", values="F_Status"))

    elif nav == "Attendance Summary":
        summary = f_df.groupby(["Emp ID", "Name"]).agg(
            Working_Days=('F_Status', lambda x: (x == 'P').sum() + (x == 'HD').sum()*0.5),
            Present=('F_Status', lambda x: (x == 'P').sum()),
            Absent=('F_Status', lambda x: (x == 'A').sum()),
            Late=('Late', 'sum'), Early_Out=('Early', 'sum')
        ).reset_index()
        st.table(summary)

    elif nav == "Exception Report":
        excep = f_df.groupby(["Emp ID", "Name"]).agg(
            Late=('Late', 'sum'), Early=('Early', 'sum'), 
            Miss_Punch=('Miss', 'sum'), Absents=('F_Status', lambda x: (x == 'A').sum())
        ).reset_index()
        st.table(excep)

    elif nav == "Half Day Report":
        st.table(f_df[f_df["F_Status"] == "HD"][["Emp ID", "Name", "Date", "In", "Out"]])

    elif nav == "Late Penalty":
        st.table(f_df.groupby(["Emp ID", "Name"]).agg(Late_Count=('Late', 'sum')).reset_index())

    elif nav == "Edit Miss Punch":
        miss_df = f_df[f_df["Miss"] == True]
        if miss_df.empty: st.success("All clear!")
        for idx, r in miss_df.iterrows():
            with st.expander(f"Fix {r['Name']} - Day {r['Date']}"):
                ni = st.text_input("In", "09:30", key=f"i{idx}")
                no = st.text_input("Out", "18:30", key=f"o{idx}")
                if st.button("Save", key=f"s{idx}"):
                    st.session_state.processed_df.at[idx, 'In'] = datetime.strptime(ni, '%H:%M').time()
                    st.session_state.processed_df.at[idx, 'Out'] = datetime.strptime(no, '%H:%M').time()
                    st.rerun()
else:
    st.info("Please upload the file and select holidays in the sidebar.")
