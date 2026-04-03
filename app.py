import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

st.set_page_config(page_title="HR Report System", layout="wide")
st.title("🛡️ HR Automation: 4-Row System")

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

def process_data(df, holidays):
    df.columns = [str(c).strip().split('.')[0] for c in df.columns]
    cols = df.columns.tolist()
    eid_col, name_col = cols[0], cols[1]
    df[eid_col] = df[eid_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    date_cols = [c for c in cols if c.isdigit() and 1 <= int(c) <= 31]
    results = []

    for eid in df[eid_col].unique():
        if pd.isna(eid) or str(eid).lower() == 'emp id': continue
        block = df[df[eid_col] == eid].reset_index(drop=True)
        if len(block) < 4: continue
        name = block.iloc[0][name_col]
        sl_done = False

        for d in date_cols:
            day_num = int(d)
            st_val = str(block.iloc[0][d]).strip().upper()
            in_t, out_t = parse_t(block.iloc[1][d]), parse_t(block.iloc[2][d])
            try: dur = float(block.iloc[3][d]) * 24 if pd.notna(block.iloc[3][d]) else 0
            except: dur = 0
            
            is_h = (day_num in holidays) or any(x in st_val for x in ['WO', 'WOP', 'W', 'HOLIDAY'])
            row = {"Emp ID": eid, "Name": name, "Date": day_num, "In": in_t, "Out": out_t, "Status": "A", "OT": 0.0, "Late": 0, "Early": 0, "Is_Miss": False, "Dur": dur}

            if (in_t and not out_t) or (not in_t and out_t):
                row["Is_Miss"] = True; row["Status"] = "A"
            elif in_t and out_t:
                if in_t > time(9, 35):
                    row["Late"] = int((datetime.combine(datetime.today(), in_t) - datetime.combine(datetime.today(), time(9, 30))).total_seconds() / 60)
                if dur < 8.5 and not is_h:
                    row["Early"] = int((8.5 - dur) * 60)
                
                raw_ot = dur if is_h else (max(0, dur - 4.0) if in_t >= time(10, 16) else max(0, dur - 8.5))
                row["OT"] = get_ot_decimal(raw_ot)

                if is_h: row["Status"] = st_val if st_val not in ['NAN', ''] else "WO"
                elif in_t >= time(10, 16): row["Status"] = "AB/"
                elif 5.8 <= dur <= 6.2 and not sl_done:
                    row["Status"] = "P"; sl_done = True
                elif 5.8 <= dur <= 6.2 and sl_done:
                    row["Status"] = "AB/"
                else: row["Status"] = "P"
            else:
                row["Status"] = st_val if is_h else "A"
            results.append(row)
    return pd.DataFrame(results)

# --- UI ---
st.sidebar.header("Settings")
h_days = st.sidebar.multiselect("Holidays:", range(1, 32))
u_file = st.file_uploader("Upload Excel", type=['xlsx'])

if u_file:
    raw_df = pd.read_excel(u_file, header=1)
    res_df = process_data(raw_df, h_days)
    if not res_df.empty:
        t1, t2, t3, t4, t5 = st.tabs(["📋 Attendance", "🕒 Late In", "🏃 Early Out", "💰 OT Report", "⚠️ Miss Punch"])
        with t1: st.dataframe(res_df.pivot(index=["Emp ID", "Name"], columns="Date", values="Status"))
        with t2: st.dataframe(res_df[res_df["Late"] > 0][["Emp ID", "Name", "Date", "In", "Late"]])
        with t3: st.dataframe(res_df[res_df["Early"] > 0][["Emp ID", "Name", "Date", "Out", "Dur", "Early"]])
        with t4:
            ot_p = res_df.pivot(index=["Emp ID", "Name"], columns="Date", values="OT")
            ot_p["Total"] = ot_p.sum(axis=1)
            st.dataframe(ot_p.style.format("{:.2f}"))
        with t5: st.dataframe(res_df[res_df["Is_Miss"] == True][["Emp ID", "Name", "Date", "In", "Out"]])
    
    st.sidebar.download_button("📥 Download", res_df.to_csv(index=False).encode('utf-8'), "Report.csv")
