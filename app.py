import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

st.set_page_config(page_title="HR Admin Pro", layout="wide")

# --- Helper Functions ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() == '' or str(val).lower() == 'nan': return None
    try:
        if isinstance(val, time): return val
        if isinstance(val, datetime): return val.time()
        val_str = str(val).strip()
        if ':' in val_str: return datetime.strptime(val_str[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(val))).time()
    except: return None

def get_ot_decimal(total_hrs):
    h = int(total_hrs)
    m = round((total_hrs - h) * 60)
    if m < 15: dec = 0.0
    elif m < 30: dec = 0.25
    elif m < 45: dec = 0.50
    elif m < 60: dec = 0.75
    else: h += 1; dec = 0.0
    return float(h + dec)

# --- Session State ---
if 'master_data' not in st.session_state:
    st.session_state.master_data = None

def process_data(df, holidays):
    # Header cleaning (Sirf ek baar top se)
    df.columns = [str(c).strip().split('.')[0] for c in df.columns]
    cols = df.columns.tolist()
    eid_col, name_col = cols[0], cols[1]
    
    # Fill names/IDs for the 4-row blocks
    df[eid_col] = df[eid_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    date_cols = [c for c in cols if c.isdigit() and 1 <= int(c) <= 31]
    results = []

    # Har unique Employee ID ke liye 4 rows uthana
    for eid in df[eid_col].unique():
        if pd.isna(eid) or str(eid).lower() == 'emp id': continue
        block = df[df[eid_col] == eid].reset_index(drop=True)
        
        # Check if block has at least 4 rows
        if len(block) < 4: continue
        emp_name = block.iloc[0][name_col]

        for d in date_cols:
            day_num = int(d)
            st_val = str(block.iloc[0][d]).strip().upper()
            in_t, out_t = parse_t(block.iloc[1][d]), parse_t(block.iloc[2][d])
            try: dur = float(block.iloc[3][d]) * 24 if pd.notna(block.iloc[3][d]) else 0
            except: dur = 0
            
            is_h = (day_num in holidays) or any(x in st_val for x in ['WO', 'WOP', 'W'])
            results.append({
                "Emp ID": eid, "Name": emp_name, "Date": day_num, "In": in_t, "Out": out_t, 
                "Status": st_val if st_val != "NAN" else "", "Duration": dur, "Is_Holiday": is_h
            })
    return pd.DataFrame(results)

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Admin Settings")
    u_file = st.file_uploader("Upload Excel", type=['xlsx'])
    h_days = st.multiselect("Select Holidays:", range(1, 32))
    st.markdown("---")
    page = st.radio("Go To:", ["📋 Attendance Master", "🕒 Late In", "🏃 Early Out", "💰 OT Report", "🛠️ Edit Miss Punch"])

if u_file and st.session_state.master_data is None:
    # Header=1 means Row 2 contains (1, 2, 3...)
    df_raw = pd.read_excel(u_file, header=1)
    st.session_state.master_data = process_data(df_raw, h_days)

if st.session_state.master_data is not None:
    df = st.session_state.master_data.copy()
    
    def apply_rules(row):
        in_t, out_t, dur = row['In'], row['Out'], row['Duration']
        res = {"Final_Status": "A", "Late": 0, "Early": 0, "OT": 0.0, "Is_Miss": False}
        
        if (in_t and not out_t) or (not in_t and out_t):
            res["Is_Miss"] = True
        elif in_t and out_t:
            if in_t > time(9, 35): res["Late"] = int((datetime.combine(datetime.today(), in_t) - datetime.combine(datetime.today(), time(9, 30))).total_seconds() / 60)
            if dur < 8.5 and not row['Is_Holiday']: res["Early"] = int((8.5 - dur) * 60)
            raw_ot = dur if row['Is_Holiday'] else (max(0, dur - 4.0) if in_t >= time(10, 16) else max(0, dur - 8.5))
            res["OT"] = get_ot_decimal(raw_ot)
            if row['Is_Holiday']: res["Final_Status"] = row['Status'] if row['Status'] else "WO"
            elif in_t >= time(10, 16): res["Final_Status"] = "AB/"
            else: res["Final_Status"] = "P"
        else:
            res["Final_Status"] = row['Status'] if row['Is_Holiday'] else "A"
        return pd.Series(res)

    f_df = pd.concat([df, df.apply(apply_rules, axis=1)], axis=1)

    if page == "📋 Attendance Master":
        st.dataframe(f_df.pivot(index=["Emp ID", "Name"], columns="Date", values="Final_Status"))
    elif page == "🕒 Late In":
        st.dataframe(f_df[f_df["Late"] > 0][["Emp ID", "Name", "Date", "In", "Late"]])
    elif page == "🏃 Early Out":
        st.dataframe(f_df[f_df["Early"] > 0][["Emp ID", "Name", "Date", "Out", "Duration", "Early"]])
    elif page == "💰 OT Report":
        ot_p = f_df.pivot(index=["Emp ID", "Name"], columns="Date", values="OT")
        ot_p["Total"] = ot_p.sum(axis=1)
        st.dataframe(ot_p.style.format("{:.2f}"))
    elif page == "🛠️ Edit Miss Punch":
        m_df = f_df[f_df["Is_Miss"] == True]
        for idx, r in m_df.iterrows():
            with st.expander(f"Edit {r['Name']} - Day {r['Date']}"):
                c1, c2 = st.columns(2)
                ni = c1.text_input("In (HH:MM)", value="09:30", key=f"i{idx}")
                no = c2.text_input("Out (HH:MM)", value="18:30", key=f"o{idx}")
                if st.button("Save", key=f"b{idx}"):
                    t_i, t_o = datetime.strptime(ni, '%H:%M').time(), datetime.strptime(no, '%H:%M').time()
                    st.session_state.master_data.at[idx, 'In'], st.session_state.master_data.at[idx, 'Out'] = t_i, t_o
                    st.session_state.master_data.at[idx, 'Duration'] = (datetime.combine(datetime.today(), t_o) - datetime.combine(datetime.today(), t_i)).total_seconds() / 3600
                    st.rerun()
                    
