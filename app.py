import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- Page Config ---
st.set_page_config(page_title="Master HR System", layout="wide")
st.title("🛡️ Master Attendance & OT System (Locked - Merged Format)")

def parse_t(val):
    if pd.isna(val) or str(val).strip() == '' or str(val).lower() == 'nan': return None
    try:
        if isinstance(val, time): return val
        if isinstance(val, datetime): return val.time()
        val_str = str(val).strip()
        if ':' in val_str: return datetime.strptime(val_str[:5], '%H:%M').time()
        # Excel decimal time handling
        return (datetime(1900, 1, 1) + timedelta(days=float(val))).time()
    except: return None

def format_hhmm(hours_decimal):
    if hours_decimal <= 0: return "00:00"
    total_min = int(round(hours_decimal * 60))
    return f"{total_min // 60:02d}:{total_min % 60:02d}"

def process_data(df, holiday_dates):
    # Cleaning data - First 2 columns are ID and Name
    cols = df.columns.tolist()
    emp_id_col = cols[0]
    name_col = cols[1]
    
    # ID aur Name ko niche tak fill karo (kyunki wo ek hi baar likhe hain)
    df[emp_id_col] = df[emp_id_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    # Date columns (1 to 31) dhoondo
    date_cols = [c for c in cols if str(c).split('.')[0].isdigit()]
    
    master_records = []
    
    # Har employee ke 4 rows ke set par kaam karo
    unique_ids = df[emp_id_col].unique()
    
    for eid in unique_ids:
        if pd.isna(eid): continue
        emp_block = df[df[emp_id_col] == eid].reset_index(drop=True)
        # Agar block mein 4 rows nahi hain toh skip karein
        if len(emp_block) < 4: continue
        
        emp_name = emp_block.iloc[0][name_col]
        sl_done = False # Short leave tracker for this employee

        for day in date_cols:
            day_int = int(str(day).split('.')[0])
            
            # Row 0: Status, Row 1: In, Row 2: Out, Row 3: Total Hours
            status_val = str(emp_block.iloc[0][day]).strip().upper()
            in_t = parse_t(emp_block.iloc[1][day])
            out_t = parse_t(emp_block.iloc[2][day])
            total_val = emp_block.iloc[3][day]
            
            # Duration calculation from Total Hours row
            try:
                if pd.isna(total_val) or isinstance(total_val, str): duration = 0
                else: duration = float(total_val) * 24
            except: duration = 0
            
            is_off = (day_int in holiday_dates) or any(x in status_val for x in ['WO', 'WOP', 'W', 'HOLIDAY'])

            res = {"Emp ID": eid, "Name": emp_name, "Date": day_int, "In": in_t, "Out": out_t, 
                   "Display": "A", "OT": 0, "Early_Min": 0, "Delay_Min": 0, "Duration": duration}

            # Rule Logic
            if (in_t and not out_t) or (not in_t and out_t):
                res["Display"] = "MIS-P"
            elif not in_t or not out_t:
                res["Display"] = status_val if is_off else "A"
            else:
                # Late Check (9:35)
                if in_t > time(9, 35):
                    res["Delay_Min"] = int((datetime.combine(datetime.today(), in_t) - datetime.combine(datetime.today(), time(9, 30))).total_seconds() / 60)

                # Status & Short Leave Logic
                if is_off:
                    res["Display"] = status_val if status_val else "W"
                    res["OT"] = duration
                elif in_t >= time(10, 16):
                    res["Display"] = "AB/"
                    res["OT"] = max(0, duration - 4.0)
                elif 5.8 <= duration <= 6.2:
                    if not sl_done:
                        res["Display"] = "P"
                        sl_done = True
                    else:
                        res["Display"] = "AB/"
                        res["OT"] = max(0, duration - 4.0)
                else:
                    res["Display"] = "P"
                    res["OT"] = max(0, duration - 8.5)
                
                # Early Out Check (8:30 Rule)
                if not is_off and duration < 8.5:
                    res["Early_Min"] = int((8.5 - duration) * 60)

            master_records.append(res)
            
    return pd.DataFrame(master_records)

# --- Streamlit UI ---
st.sidebar.markdown("### 📅 Settings")
h_days = st.sidebar.multiselect("Select National Holidays:", range(1, 32))

u_file = st.file_uploader("Upload Excel (ID & Name once, 4 Rows: Status/In/Out/Total)", type=['xlsx'])

if u_file:
    df_in = pd.read_excel(u_file, header=1)
    final_df = process_data(df_in, h_days)
    
    if not final_df.empty:
        t = st.tabs(["📋 Master", "❓ Miss Punch", "🕒 Late Coming", "🚪 Early Out", "💰 Daily OT"])
        with t[0]: st.dataframe(final_df.pivot(index=["Emp ID", "Name"], columns="Date", values="Display"))
        with t[1]: st.dataframe(final_df[final_df["Display"] == "MIS-P"][["Emp ID", "Name", "Date", "In", "Out"]])
        with t[2]:
            late = final_df[final_df["Delay_Min"] > 5].copy()
            late["Delay"] = late["Delay_Min"].apply(lambda x: f"{int(x)} Min")
            st.dataframe(late[["Emp ID", "Name", "Date", "In", "Delay", "Display"]])
        with t[3]:
            early = final_df[final_df["Early_Min"] > 0].copy()
            early["Work Duration"] = early["Duration"].apply(format_hhmm)
            early["Early By"] = early["Early_Min"].apply(lambda x: f"{int(x)} Min")
            st.dataframe(early[["Emp ID", "Name", "Date", "In", "Out", "Work Duration", "Early By"]])
        with t[4]:
            final_df["OT_F"] = final_df["OT"].apply(format_hhmm)
            st.dataframe(final_df.pivot(index=["Emp ID", "Name"], columns="Date", values="OT_F"))
