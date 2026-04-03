import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- Page Config ---
st.set_page_config(page_title="Master HR System", layout="wide")
st.title("🛡️ Master Attendance & OT System (Locked)")

# --- Helper Functions ---
def parse_t(val):
    if not val or str(val).lower() in ['nan', '', '0', '00:00']: return None
    try:
        if ':' in str(val): return datetime.strptime(str(val)[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(val))).time()
    except: return None

def format_hhmm(hours_decimal):
    if hours_decimal <= 0: return "00:00"
    total_min = int(round(hours_decimal * 60))
    hh = total_min // 60
    mm = total_min % 60
    return f"{hh:02d}:{mm:02d}"

# --- Processing Logic ---
def process_data(df, holiday_dates):
    df.columns = [str(c).strip() for c in df.columns]
    cols = df.columns.tolist()
    emp_id_col = next((c for c in cols if 'id' in c.lower()), None)
    header_col = next((c for c in cols if any(x in c.lower() for x in ['date', 'status', 'type'])), None)
    
    df[emp_id_col] = df[emp_id_col].ffill()
    date_cols = [c for c in cols if str(c).replace('.0','').isdigit()]
    
    master_records = []
    sl_tracker = {} 

    for eid in df[emp_id_col].unique():
        if pd.isna(eid): continue
        emp_block = df[df[emp_id_col] == eid]
        name = emp_block.iloc[0].get('Name', 'Unknown')
        sl_tracker[eid] = 0

        st_row = emp_block[emp_block[header_col].astype(str).str.contains('Status', case=False, na=False)].head(1)
        in_row = emp_block[emp_block[header_col].astype(str).str.contains('In', case=False, na=False)].head(1)
        out_row = emp_block[emp_block[header_col].astype(str).str.contains('Out', case=False, na=False)].head(1)

        for day in date_cols:
            day_int = int(str(day).replace('.0',''))
            status_orig = str(st_row[day].values[0]).strip().upper() if not st_row.empty else ""
            in_t = parse_t(in_row[day].values[0]) if not in_row.empty else None
            out_t = parse_t(out_row[day].values[0]) if not out_row.empty else None
            
            is_off = (day_int in holiday_dates) or any(x in status_orig for x in ['WO', 'WOP', 'W'])

            res = {
                "Emp ID": eid, "Name": name, "Date": day_int,
                "In": in_t, "Out": out_t, "Display": "A", "OT": 0, 
                "Early_Min": 0, "Delay_Min": 0, "Duration": 0
            }

            if (in_t and not out_t) or (not in_t and out_t):
                res["Display"] = "MIS-P"
            elif not in_t or not out_t:
                res["Display"] = status_orig if is_off else "A"
            else:
                eff_in = max(datetime.combine(datetime.today(), in_t), datetime.combine(datetime.today(), time(9, 30)))
                duration = (datetime.combine(datetime.today(), out_t) - eff_in).total_seconds() / 3600
                if out_t < in_t: duration += 24
                res["Duration"] = duration

                if in_t > time(9, 35):
                    delay = (datetime.combine(datetime.today(), in_t) - datetime.combine(datetime.today(), time(9, 30))).total_seconds() / 60
                    res["Delay_Min"] = int(delay)

                if is_off:
                    res["Display"] = status_orig if status_orig else "W"
                    res["OT"] = duration
                elif in_t >= time(10, 16):
                    res["Display"] = "AB/"
                    res["OT"] = max(0, duration - 4.0)
                elif 5.8 <= duration <= 6.2:
                    if sl_tracker[eid] < 1:
                        res["Display"] = "P"
                        sl_tracker[eid] += 1
                        res["OT"] = 0
                    else:
                        res["Display"] = "AB/"
                        res["OT"] = max(0, duration - 4.0)
                else:
                    res["Display"] = "P"
                    res["OT"] = max(0, duration - 8.5)
                
                if not is_off and duration < 8.5:
                    res["Early_Min"] = int((8.5 - duration) * 60)

            master_records.append(res)
    return pd.DataFrame(master_records)

# --- UI Layout ---
st.sidebar.header("⚙️ Settings")
holiday_input = st.sidebar.multiselect("Select National Holidays (Dates):", range(1, 32))

uploaded_file = st.file_uploader("Upload Attendance Excel", type=['xlsx'])

if uploaded_file:
    raw_df = pd.read_excel(uploaded_file, header=1)
    full_df = process_data(raw_df, holiday_input)
    
    t1, t2, t3, t4, t5 = st.tabs(["📋 Master", "❓ Miss Punch", "🕒 Late Coming", "🚪 Early Out", "💰 Daily OT"])

    with t1:
        st.subheader("Monthly Status (P, AB/, W)")
        pivot_m = full_df.pivot(index=["Emp ID", "Name"], columns="Date", values="Display")
        st.dataframe(pivot_m)

    with t2:
        st.subheader("Miss Punch Report")
        miss = full_df[full_df["Display"] == "MIS-P"]
        st.dataframe(miss[["Emp ID", "Name", "Date", "In", "Out"]])

    with t3:
        st.subheader("Late Coming (> 09:35)")
        late = full_df[full_df["Delay_Min"] > 5]
        late["Delay"] = late["Delay_Min"].apply(lambda x: f"{int(x)} Min")
        st.dataframe(late[["Emp ID", "Name", "Date", "In", "Delay", "Display"]])

    with t4:
        st.subheader("Early Out (< 08:30 Hours)")
        early = full_df[full_df["Early_Min"] > 0]
        early["Work Duration"] = early["Duration"].apply(format_hhmm)
        early["Early By"] = early["Early_Min"].apply(lambda x: f"{int(x)} Min")
        st.dataframe(early[["Emp ID", "Name", "Date", "In", "Out", "Work Duration", "Early By"]])

    with t5:
        st.subheader("Daily OT Report (HH:MM)")
        full_df["OT_Final"] = full_df["OT"].apply(format_hhmm)
        ot_p = full_df.pivot(index=["Emp ID", "Name"], columns="Date", values="OT_Final")
        st.dataframe(ot_p)

    csv = full_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Download Combined Report", csv, "Final_Report.csv", "text/csv")
