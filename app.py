import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

st.set_page_config(page_title="Final OT Calculator", layout="wide")
st.title("📊 Attendance & OT System")

def round_ot(hours):
    if hours <= 0: return 0
    full_hours = int(hours)
    rem = (hours - full_hours) * 60
    if rem < 15: rounded = 0
    elif rem < 30: rounded = 0.25
    elif rem < 45: rounded = 0.50
    elif rem < 60: rounded = 0.75
    else: 
        full_hours += 1
        rounded = 0
    return full_hours + rounded

def process_data(df):
    # 1. ऑटोमैटिक कॉलम ढूंढना (ताकि स्पेलिंग की गलती न हो)
    cols = df.columns.tolist()
    
    # Emp ID कॉलम ढूंढना
    emp_id_col = next((c for c in cols if 'id' in str(c).lower()), None)
    # Name कॉलम ढूंढना
    name_col = next((c for c in cols if 'name' in str(c).lower()), None)
    # Status/Type कॉलम ढूंढना
    status_col = next((c for c in cols if 'status' in str(c).lower() or 'type' in str(c).lower() or 'date' in str(c).lower()), None)

    if not emp_id_col or not status_col:
        st.error(f"Excel में सही कॉलम नहीं मिले! आपकी फाइल में ये कॉलम हैं: {cols}")
        return None

    # सफाई
    df[emp_id_col] = df[emp_id_col].ffill()
    if name_col: df[name_col] = df[name_col].ffill()
    
    date_cols = [c for c in cols if str(c).strip().isdigit()]
    std_hrs = 8.5
    ot_records = []

    for eid in df[emp_id_col].unique():
        emp_block = df[df[emp_id_col] == eid]
        name = emp_block[name_col].iloc[0] if name_col else str(eid)
        row_summary = {"Emp ID": eid, "Name": name}
        
        # ब्लॉक पहचानना
        status_rows = emp_block[emp_block[status_col].astype(str).str.contains('P|A|WO|Status', case=False, na=False)]
        in_rows = emp_block[emp_block[status_col].astype(str).str.contains('In', case=False, na=False)]
        out_rows = emp_block[emp_block[status_col].astype(str).str.contains('Out', case=False, na=False)]

        for day in date_cols:
            try:
                current_status = str(status_rows[day].values[0]).strip().upper() if not status_rows.empty else 'A'
                out_val = str(out_rows[day].values[0]).strip() if not out_rows.empty else ''

                if 'A' in current_status or not out_val or out_val.lower() == 'nan' or out_val == "":
                    row_summary[day] = 0
                    continue

                fmt = '%H:%M'
                t_in = time(9, 30) # Default
                try:
                    t_out = datetime.strptime(out_val, fmt).time()
                except:
                    # अगर समय 07:30 PM फॉर्मेट में हो
                    t_out = datetime.strptime(out_val, '%I:%M %p').time()

                dt_in = datetime.combine(datetime.today(), t_in)
                dt_out = datetime.combine(datetime.today(), t_out)
                if dt_out <= dt_in: dt_out += timedelta(days=1)
                
                total_hrs = (dt_out - dt_in).total_seconds() / 3600

                if 'WO' in current_status:
                    ot_hrs = total_hrs
                else:
                    ot_hrs = max(0, total_hrs - std_hrs)

                row_summary[day] = round_ot(ot_hrs)
            except:
                row_summary[day] = 0
        
        row_summary["Total Month OT"] = sum([v for k,v in row_summary.items() if str(k).isdigit()])
        ot_records.append(row_summary)

    return pd.DataFrame(ot_records)

uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx'])

if uploaded_file:
    # फाइल को ऊपर की फालतू Rows हटाकर पढ़ना
    df = pd.read_excel(uploaded_file)
    
    # अगर पहली रो खाली है तो उसे ठीक करना
    if 'Emp ID' not in df.columns:
        df = pd.read_excel(uploaded_file, header=1) # 1 row नीचे से शुरू करेगा

    if st.button("🚀 Generate Report"):
        final_df = process_data(df)
        if final_df is not None:
            st.dataframe(final_df)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False)
            st.download_button("📥 Download Report", output.getvalue(), "OT_Report.xlsx")
