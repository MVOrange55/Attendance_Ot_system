import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- Page Config ---
st.set_page_config(page_title="HR Automation Pro", layout="wide")
st.title("🛡️ Final HR Automation System")

def parse_t(val):
    if pd.isna(val) or str(val).strip() == '' or str(val).lower() == 'nan': return None
    try:
        if isinstance(val, time): return val
        if isinstance(val, datetime): return val.time()
        val_str = str(val).strip()
        if ':' in val_str: return datetime.strptime(val_str[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(val))).time()
    except: return None

def get_ot_decimal_slab(total_hours):
    hours = int(total_hours)
    minutes = round((total_hours - hours) * 60)
    if minutes < 15: slab_dec = 0.0
    elif minutes < 30: slab_dec = 0.25
    elif minutes < 45: slab_dec = 0.50
    elif minutes < 60: slab_dec = 0.75
    else: 
        hours += 1
        slab_dec = 0.0
    return float(hours + slab_dec)

def process_data(df, holiday_dates):
    # Header cleaning: Sirf wahi columns le jo 1-31 ke beech hain
    cols = df.columns.tolist()
    emp_id_col, name_col = cols[0], cols[1]
    df[emp_id_col] = df[emp_id_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    # Strictly filter only date columns (1 to 31)
    date_cols = []
    for c in cols:
        try:
            val = int(float(str(c).split('.')[0]))
            if 1 <= val <= 31:
                date_cols.append(c)
        except: continue

    master_records = []
    for eid in df[emp_id_col].unique():
        if pd.isna(eid): continue
        emp_block = df[df[emp_id_col] == eid].reset_index(drop=True)
        if len(emp_block) < 4: continue
        emp_name = emp_block.iloc[0][name_col]
        sl_count = 0 

        for day in date_cols:
            day_label = int(float(str(day).split('.')[0]))
            status_val = str(emp_block.iloc[0][day]).strip().upper()
            in_t, out_t = parse_t(emp_block.iloc[1][day]), parse_t(emp_block.iloc[2][day])
            total_val = emp_block.iloc[3][day]

            try: duration = float(total_val) * 24 if pd.notna(total_val) and not isinstance(total_val, str) else 0
            except: duration = 0
            
            is_off = (day_label in holiday_dates) or any(x in status_val for x in ['WO', 'WOP', 'W'])
            
            res = {
                "Emp ID": eid, "Name": emp_name, "Date": day_label, "In": in_t, "Out": out_t, 
                "Display": "A", "OT_Dec": 0.0, "Late_Min": 0, "Early_Min": 0, "Is_Miss": False
            }

            if (in_t and not out_t) or (not in_t and out_t):
                res["Is_Miss"] = True
            elif in_t and out_t:
                # Late/Early Rules
                if in_t > time(9, 35):
                    res["Late_Min"] = int((datetime.combine(datetime.today(), in_t) - datetime.combine(datetime.today(), time(9, 30))).total_seconds() / 60)
                if duration < 8.5 and not is_off:
                    res["Early_Min"] = int((8.5 - duration) * 60)
                
                # OT Calculation
                if is_off: raw_ot = duration
                elif in_t >= time(10, 16): raw_ot = max(0, duration - 4.0)
                else: raw_ot = max(0, duration - 8.5)
                res["OT_Dec"] = get_ot_decimal_slab(raw_ot)

                # Status
                if is_off: res["Display"] = status_val if status_val else "W"
                elif in_t >= time(10, 16): res["Display"] = "AB/"
                elif 5.8 <= duration <= 6.2 and sl_count < 1:
                    res["Display"] = "P"; sl_count += 1
                elif 5.8 <= duration <= 6.2: res["Display"] = "AB/"
                else: res["Display"] = "P"
            else:
                res["Display"] = status_val if is_off else "A"

            master_records.append(res)
            
    return pd.DataFrame(master_records)

# --- UI ---
st.sidebar.header("Settings")
h_days = st.sidebar.multiselect("Holidays:", range(1, 32))
u_file = st.file_uploader("Upload Excel", type=['xlsx'])

if u_file:
    # Header=1 kyunki aapki file mein 2nd row se data shuru hota hai
    df_in = pd.read_excel(u_file, header=1)
    final_df = process_data(df_in, h_days)
    
    if not final_df.empty:
        t = st.tabs(["📋 Attendance", "💰 OT (Decimal)", "⚠️ Miss Punch", "🕒 Late/Early"])
        
        with t[0]:
            st.dataframe(final_df.pivot(index=["Emp ID", "Name"], columns="Date", values="Display"))
            
        with t[1]:
            ot_p = final_df.pivot(index=["Emp ID", "Name"], columns="Date", values="OT_Dec")
            # Calculate Total correctly row-wise
            ot_p["Monthly Total"] = ot_p.sum(axis=1)
            st.dataframe(ot_p.style.format("{:.2f}"))
            
        with t[2]:
            st.dataframe(final_df[final_df["Is_Miss"]==True][["Emp ID", "Name", "Date", "In", "Out"]])
            
        with t[3]:
            st.dataframe(final_df[(final_df["Late_Min"] > 5) | (final_df["Early_Min"] > 0)])

    st.sidebar.download_button("📥 Download", final_df.to_csv(index=False).encode('utf-8'), "HR_Report.csv")
