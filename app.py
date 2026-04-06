import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- Page Config ---
st.set_page_config(page_title="Master HR System", layout="wide")

# --- Helper Functions ---
def parse_time(val):
    if not val or str(val).lower() in ['nan', '', '0', '00:00']: return None
    try:
        if ':' in str(val):
            return datetime.strptime(str(val)[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(val))).time()
    except: return None

def format_hhmm(hours_decimal):
    if hours_decimal <= 0: return "00:00"
    total_min = int(hours_decimal * 60)
    hh = total_min // 60
    mm = total_min % 60
    return f"{hh:02d}:{mm:02d}"

# --- Main Logic ---
def process_data(df, holiday_dates):
    df.columns = [str(c).strip() for c in df.columns]
    cols = df.columns.tolist()
    emp_id_col = next((c for c in cols if 'id' in c.lower()), None)
    header_col = next((c for c in cols if any(x in c.lower() for x in ['date', 'status', 'type'])), None)
    
    df[emp_id_col] = df[emp_id_col].ffill()
    date_cols = [c for c in cols if str(c).replace('.0','').isdigit()]
    
    master_records = []
    sl_tracker = {} # {emp_id: count}

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
            in_t = parse_time(in_row[day].values[0]) if not in_row.empty else None
            out_t = parse_time(out_row[day].values[0]) if not out_row.empty else None
            
            # Holiday Check
            is_holiday = (day_int in holiday_dates) or ('WO' in status_orig) or ('WOP' in status_orig)

            res = {
                "Emp ID": eid, "Name": name, "Date": day_int,
                "In": in_t, "Out": out_t, "Status": "A", "OT": 0, 
                "Early_Min": 0, "Delay_Min": 0, "Duration": 0, "Color": ""
            }

            if (in_t and not out_t) or (not in_t and out_t):
                res["Status"] = "MIS-P"
                res["Color"] = "Orange"
            elif not in_t or not out_t:
                res["Status"] = status_orig if is_holiday else "A"
                if is_holiday: res["Color"] = "Green"
            else:
                # Calculations
                eff_in = max(datetime.combine(datetime.today(), in_t), datetime.combine(datetime.today(), time(9, 30)))
                duration = (datetime.combine(datetime.today(), out_t) - eff_in).total_seconds() / 3600
                if out_t < in_t: duration += 24
                res["Duration"] = duration

                # Late Logic
                if in_t > time(9, 35):
                    delay = (datetime.combine(datetime.today(), in_t) - datetime.combine(datetime.today(), time(9, 30))).total_seconds() / 60
                    res["Delay_Min"] = int(delay)

                # Category Assignment
                if is_holiday:
                    res["Status"] = status_orig if status_orig else "W"
                    res["Color"] = "Green"
                    res["OT"] = duration
                elif in_t >= time(10, 16):
                    res["Status"] = "AB/"
                    res["Color"] = "Blue"
                    res["OT"] = max(0, duration - 4.0)
                elif 5.8 <= duration <= 6.2: # Short Leave
                    if sl_tracker[eid] < 1:
                        res["Status"] = "P"
                        res["Color"] = "Yellow"
                        sl_tracker[eid] += 1
                        res["OT"] = 0
                    else:
                        res["Status"] = "AB/"
                        res["Color"] = "Blue"
                        res["OT"] = max(0, duration - 4.0)
                else:
                    res["Status"] = "P"
                    res["OT"] = max(0, duration - 8.5)
                
                # Early Out Check (8:30 hours = 8.5)
                if not is_holiday and duration < 8.5:
                    early_min = (8.5 - duration) * 60
                    res["Early_Min"] = int(early_min)

            master_records.append(res)
    return pd.DataFrame(master_records)

# --- UI Layout ---
st.sidebar.header("⚙️ Settings")
holiday_input = st.sidebar.multiselect("Select National Holidays (Dates):", range(1, 32))

uploaded_file = st.file_uploader("Upload Attendance Excel", type=['xlsx'])

if uploaded_file:
    raw_df = pd.read_excel(uploaded_file, header=1)
    full_data = process_data(raw_df, holiday_input)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Master", "❓ Miss Punch", "🕒 Late Coming", "🚪 Early Out", "💰 Daily OT"])

    with tab1:
        st.subheader("Attendance Master (P, AB/, W)")
        pivot_master = full_data.pivot(index=["Emp ID", "Name"], columns="Date", values="Status")
        st.dataframe(pivot_master.style.applymap(lambda x: 'background-color: #00b050' if x in ['W','WO','WOP'] else ('background-color: #0070c0' if x == 'AB/' else '')))

    with tab2:
        st.subheader("Orange Alert: Miss Punch")
        miss = full_data[full_data["Status"] == "MIS-P"]
        st.table(miss[["Emp ID", "Name", "Date", "In", "Out"]])

    with tab3:
        st.subheader("Late Coming (> 09:35)")
        late = full_data[full_data["Delay_Min"] > 5]
        late["Delay"] = late["Delay_Min"].apply(lambda x: f"{x} Min")
        st.table(late[["Emp ID", "Name", "Date", "In", "Delay", "Status"]])

    with tab4:
        st.subheader("Early Out (< 08:30 Hours)")
        early = full_data[full_data["Early_Min"] > 0]
        early["Work Duration"] = early["Duration"].apply(format_hhmm)
        early["Early By"] = early["Early_Min"].apply(lambda x: f"{x} Min")
        st.table(early[["Emp ID", "Name", "Date", "In", "Out", "Work Duration", "Early By"]])

    with tab5:
        st.subheader("Daily OT Report (HH:MM)")
        full_data["OT_HHMM"] = full_data["OT"].apply(format_hhmm)
        ot_pivot = full_data.pivot(index=["Emp ID", "Name"], columns="Date", values="OT_HHMM")
        st.dataframe(ot_pivot)

    # Download
    csv = full_data.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Full Report", csv, "Final_Report.csv", "text/csv")
