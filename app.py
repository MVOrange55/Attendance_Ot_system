import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

st.set_page_config(page_title="Final OT System", layout="wide")
st.title("📊 Smart Attendance & OT System")

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
    df.columns = [str(c).strip() for c in df.columns]
    cols = df.columns.tolist()
    
    emp_id_col = next((c for c in cols if 'id' in c.lower()), None)
    name_col = next((c for c in cols if 'name' in c.lower()), None)
    header_col = next((c for c in cols if any(x in c.lower() for x in ['date', 'status', 'type'])), None)

    if not emp_id_col or not header_col:
        st.error(f"कॉलम नहीं मिले! चेक करें कि फाइल में 'Emp ID' और 'Date' कॉलम हैं।")
        return None

    # ID और Name को नीचे तक भरना
    df[emp_id_col] = df[emp_id_col].ffill()
    if name_col:
        df[name_col] = df[name_col].ffill()
    
    date_cols = [c for c in cols if str(c).strip().isdigit()]
    ot_records = []

    for eid in df[emp_id_col].unique():
        emp_block = df[df[emp_id_col] == eid]
        name = emp_block[name_col].iloc[0] if name_col else "Unknown"
        row_summary = {"Emp ID": eid, "Name": name}
        
        # --- यहाँ सुधार किया गया है ---
        # 1. Status Row: वो रो जिसमें P, A या WO लिखा हो
        st_row = emp_block[emp_block[header_col].astype(str).str.contains('Status|P|A|WO', case=False, na=False)].head(1)
        
        # 2. Out Row: वो रो जिसमें 'Out' लिखा हो
        out_row = emp_block[emp_block[header_col].astype(str).str.contains('Out', case=False, na=False)].head(1)

        for day in date_cols:
            try:
                # स्टेटस निकालना
                status_val = str(st_row[day].values[0]).strip().upper() if not st_row.empty else ''
                # आउट टाइम निकालना
                out_val = str(out_row[day].values[0]).strip() if not out_row.empty else ''

                # अगर स्टेटस 'P' या 'WO' नहीं है, तो OT 0
                if not any(x in status_val for x in ['P', 'WO']):
                    row_summary[day] = 0
                    continue
                
                # अगर टाइम खाली है
                if out_val.lower() in ['nan', '', 'null']:
                    row_summary[day] = 0
                    continue

                # टाइम पार्सिंग
                try:
                    t_out = datetime.strptime(out_val, '%H:%M').time()
                except:
                    try:
                        t_out = datetime.strptime(out_val, '%I:%M %p').time()
                    except:
                        # अगर एक्सेल में टाइम डेसीमल में है (जैसे 0.8125)
                        t_out = (datetime(1900, 1, 1) + timedelta(days=float(out_val))).time()

                t_in = time(9, 30)
                dt_in = datetime.combine(datetime.today(), t_in)
                dt_out = datetime.combine(datetime.today(), t_out)
                
                if dt_out <= dt_in: dt_out += timedelta(days=1)
                
                total_work_hrs = (dt_out - dt_in).total_seconds() / 3600

                if 'WO' in status_val:
                    ot_hrs = total_work_hrs
                else:
                    ot_hrs = max(0, total_work_hrs - 8.5)

                row_summary[day] = round_ot(ot_hrs)
            except:
                row_summary[day] = 0
        
        row_summary["Total Month OT"] = sum([v for k,v in row_summary.items() if str(k).isdigit()])
        ot_records.append(row_summary)

    return pd.DataFrame(ot_records)

uploaded_file = st.file_uploader("Upload Attendance Excel", type=['xlsx'])

if uploaded_file:
    # फाइल को बिना किसी हेडर के पढ़ना ताकि हम खुद ढूंढ सकें
    df_raw = pd.read_excel(uploaded_file)
    
    # अगर पहली रो में Emp ID नहीं है तो डेटा क्लीन करें
    if not any('id' in str(c).lower() for c in df_raw.columns):
        df_raw = pd.read_excel(uploaded_file, header=1)

    st.success("File Uploaded!")
    
    if st.button("🚀 Calculate OT Now"):
        final_df = process_data(df_raw)
        if final_df is not None:
            st.dataframe(final_df)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False)
            st.download_button("📥 Download Report", output.getvalue(), "OT_Report.xlsx")
