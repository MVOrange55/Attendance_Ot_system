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
    # कॉलम क्लीनिंग
    df.columns = [str(c).strip() for c in df.columns]
    cols = df.columns.tolist()
    
    # कॉलम ढूंढना
    emp_id_col = next((c for c in cols if 'id' in c.lower()), None)
    name_col = next((c for c in cols if 'name' in c.lower()), None)
    header_col = next((c for c in cols if any(x in c.lower() for x in ['date', 'status', 'type', 'unnamed'])), None)

    if not emp_id_col or not header_col:
        st.error(f"कॉलम नहीं मिले! एक्सेल में ये कॉलम हैं: {cols}")
        return None

    # ID और Name भरना
    df[emp_id_col] = df[emp_id_col].ffill()
    if name_col: df[name_col] = df[name_col].ffill()
    
    date_cols = [c for c in cols if str(c).strip().isdigit()]
    ot_records = []

    for eid in df[emp_id_col].unique():
        emp_block = df[df[emp_id_col] == eid]
        name = emp_block[name_col].iloc[0] if name_col else "Unknown"
        row_summary = {"Emp ID": eid, "Name": name}
        
        # --- यहाँ सबसे ज्यादा सुधार है ---
        # हम पूरी रो को चेक करेंगे कि क्या उसमें 'Status' या 'Out' शब्द कहीं भी है
        st_row = emp_block[emp_block[header_col].astype(str).str.contains('Status|P|A|WO|Present', case=False, na=False)].head(1)
        out_row = emp_block[emp_block[header_col].astype(str).str.contains('Out|Punch|Exit|Time', case=False, na=False)].head(1)
        
        # अगर Out row नहीं मिली, तो Total वाली रो को चेक करेंगे
        if out_row.empty:
            out_row = emp_block[emp_block[header_col].astype(str).str.contains('Total', case=False, na=False)].head(1)

        for day in date_cols:
            try:
                status_val = str(st_row[day].values[0]).strip().upper() if not st_row.empty else ''
                out_val = str(out_row[day].values[0]).strip() if not out_row.empty else ''

                if not any(x in status_val for x in ['P', 'WO', 'PRES', 'WEEK']):
                    row_summary[day] = 0
                    continue
                
                if out_val.lower() in ['nan', '', 'null', '0']:
                    row_summary[day] = 0
                    continue

                # टाइम कन्वर्जन
                try:
                    if ':' in out_val:
                        t_out = datetime.strptime(out_val.split()[0], '%H:%M').time()
                    else:
                        # एक्सेल का डेसीमल टाइम
                        t_out = (datetime(1900, 1, 1) + timedelta(days=float(out_val))).time()
                except:
                    row_summary[day] = 0
                    continue

                t_in = time(9, 30)
                dt_in = datetime.combine(datetime.today(), t_in)
                dt_out = datetime.combine(datetime.today(), t_out)
                
                if dt_out <= dt_in: dt_out += timedelta(days=1)
                
                total_work_hrs = (dt_out - dt_in).total_seconds() / 3600

                if 'WO' in status_val or 'WEEK' in status_val:
                    ot_hrs = total_work_hrs
                else:
                    ot_hrs = max(0, total_work_hrs - 8.5)

                row_summary[day] = round_ot(ot_hrs)
            except:
                row_summary[day] = 0
        
        row_summary["Total Month OT"] = sum([v for k,v in row_summary.items() if str(k).isdigit()])
        ot_records.append(row_summary)

    return pd.DataFrame(ot_records)

uploaded_file = st.file_uploader("Upload Your Excel File", type=['xlsx'])

if uploaded_file:
    df_raw = pd.read_excel(uploaded_file)
    
    # ऑटो-हेडर डिटेक्शन
    if not any('id' in str(c).lower() for c in df_raw.columns):
        for i in range(5): # पहली 5 लाइनों में हेडर ढूँढना
            test_df = pd.read_excel(uploaded_file, header=i)
            if any('id' in str(c).lower() for c in test_df.columns):
                df_raw = test_df
                break

    st.success("File Loaded!")
    
    # डेटा का छोटा सा हिस्सा दिखाएँ ताकि यूजर देख सके कि क्या रीड हुआ है
    with st.expander("एक्सेल में जो डेटा मिला है उसे यहाँ देखें (Debug)"):
        st.write(df_raw.head(10))

    if st.button("🚀 Calculate Final OT"):
        final_df = process_data(df_raw)
        if final_df is not None:
            st.dataframe(final_df)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False)
            st.download_button("📥 Download Report", output.getvalue(), "OT_Report.xlsx")
