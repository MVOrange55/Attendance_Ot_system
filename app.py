import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- Page Configuration ---
st.set_page_config(page_title="Master HR Dashboard", layout="wide")
st.title("🛡️ Master Attendance & OT Management System (Locked)")

# --- Utility Functions ---
def parse_time(val):
    if not val or str(val).lower() in ['nan', '', '0', '00:00']: return None
    try:
        if ':' in str(val):
            return datetime.strptime(str(val)[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(val))).time()
    except: return None

def format_hhmm(hours_decimal):
    if hours_decimal <= 0: return "00:00"
    total_min = int(round(hours_decimal * 60))
    hh = total_min // 60
    mm = total_min % 60
    return f"{hh:02d}:{mm:02d}"

# --- Core Processing Logic ---
def process_hr_data(df, holiday_list):
    df.columns = [str(c).strip() for c in df.columns]
    cols = df.columns.tolist()
    emp_id_col = next((c for c in cols if 'id' in c.lower()), None)
    header_col = next((c for c in cols if any(x in c.lower() for x in ['date', 'status', 'type'])), None)
    
    df[emp_id_col] = df[emp_id_col].ffill()
    date_cols = [c for c in cols if str(c).replace('.0','').isdigit()]
    
    final_data = []
    sl_count = {} # Employee Short Leave Tracker

    for eid in df[emp_id_col].unique():
        if pd.isna(eid): continue
        emp_block = df[df[emp_id_col] == eid]
        name = emp_block.iloc[0].get('Name', 'Unknown')
        sl_count[eid] = 0

        # Identifying Data Rows
        st_row = emp_block[emp_block[header_col].astype(str).str.contains('Status', case=False, na=False)].head(1)
        in_row = emp_block[emp_block[header_col].astype(str).str.contains('In', case=False, na=False)].head(1)
        out_row = emp_block[emp_block[header_col].astype(str).str.contains('Out', case=False, na=False)].head(1)

        for day in date_cols:
            d_num = int(str(day).replace('.0',''))
            orig_status = str(st_row[day].values[0]).strip().upper() if not st_row.empty else ""
            t_in = parse_time(in_row[day].values[0]) if not in_row.empty else None
            t_out = parse_time(out_row[day].values[0]) if not out_row.empty else None
            
            is_holiday = (d_num in holiday_list) or any(x in orig_status for x in ['WO', 'WOP', 'W'])

            row = {
                "Emp ID": eid, "Name": name, "Date": d_num,
                "In": t_in, "Out": t_out, "Status": "A", "OT": 0, 
                "Early_Min": 0, "Delay_Min": 0, "Duration": 0, "Display": ""
            }

            # 1. Miss Punch Rule
            if (t_in and not t_out) or (not t_in and t_out):
                row["Display"] = "MIS-P"
                row["Status"] = "MIS-P"
                final_data.append(row)
                continue

            if not t_in or not t_out:
                row["Display"] = orig_status if is_holiday else "A"
                final_data.append(row)
                continue

            # 2. Working Duration Calculation
            eff_in = max(datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), time(9, 30)))
            work_hrs = (datetime.combine(datetime.today(), t_out) - eff_in).total_seconds() / 3600
            if t_out < t_in: work_hrs += 24
            row["
