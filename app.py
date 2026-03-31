import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

st.set_page_config(page_title="Final OT System", layout="wide")
st.title("📊 Final Attendance OT System (With National Holidays)")

def calculate_final_ot(total_hrs, is_wo_or_holiday):
    # Rule: WO ya Holiday par pura OT, Present par 8.5 minus
    if is_wo_or_holiday:
        ot_exact = total_hrs
    else:
        ot_exact = max(0, total_hrs - 8.5)
    
    if ot_exact <= 0: return 0
    
    # Rule: Rounding (<15=0, 15=0.25, 30=0.50, 45=0.75)
    hours = int(ot_exact)
    minutes = (ot_exact - hours) * 60
    
    if minutes < 15: rounded_min = 0
    elif minutes < 30: rounded_min = 0.25
    elif minutes < 45: rounded_min = 0.50
    elif minutes < 60: rounded_min = 0.75
    else:
        hours += 1
        rounded_min = 0
    return hours + rounded_min

def process_data(df):
    df.columns = [str(c).strip() for c in df.columns]
    cols = df.columns.tolist()
    
    emp_id_col = next((c for c in cols if 'id' in c.lower()), None)
    name_col = next((c for c in cols if 'name' in c.lower()), None)
    header_col = next((c for c in cols if any(x in c.lower() for x in ['date', 'status', 'type'])), None)

    if not emp_id_col or not header_col:
        st.error("Zaroori columns nahi mile!")
        return None

    df[emp_id_col] = df[emp_id_col].ffill()
    if name_col:
        df[name_col] = df[name_col].ffill()
    
    date_cols = [c for c in cols if str(c).replace('.0','').isdigit()]
    ot_records = []

    for eid in df[emp_id_col].unique():
        if pd.isna(eid): continue
        emp_block = df[df[emp_id_col] == eid]
        name = emp_block[name_col].iloc[0] if name_col else "Unknown"
        row_summary = {"Emp ID": eid, "Name": name}
        
        st_row = emp_block[emp_block[header_col].astype(str).str.contains('Status|P|A|WO', case=False, na=False)].head(1)
        out_row = emp_block[emp_block[header_col].astype(str).str.contains('Out', case=False, na=False)].head(1)

        for day in date_cols:
            try:
                # Din ki pehchan (4 aur 21 National Holiday hain)
                day_num = int(str(day).replace('.0',''))
                is_holiday = day_num in [4, 21]
                
                status_val = str(st_row[day].values[0]).strip().upper() if not st_row.empty else ''
                out_val = str(out_row[day].values[0]).strip() if not out_row.empty else ''

                if not any(x in status_val for x in ['P', 'WO']):
                    row_summary[day] = 0
                    continue
                
                if ':' in out_val:
                    t_out = datetime.strptime(out_val[:5], '%H:%M').time()
                else:
                    t_out = (datetime(1900, 1, 1) + timedelta(days=float(out_val))).time()

                t_in = time(9, 30)
                dt_in = datetime.combine(datetime.today(), t_in)
                dt_out = datetime.combine(datetime.today(), t_out)
                
                if dt_out <= dt_in: dt_out += timedelta(days=1)
                total_hrs = (dt_out - dt_in).total_seconds() / 3600

                # Agar WO hai YA 4/21 tarikh hai, to pura OT milega
                is_full_ot_day = ('WO' in status_val) or is_holiday
                
                row_summary[day] = calculate_final_ot(total_hrs, is_full_ot_day)
            except:
                row_summary[day] = 0
        
        row_summary["Total Month OT"] = sum([v for k,v in row_summary.items() if k in date_cols])
        ot_records.append(row_summary)

    return pd.DataFrame(ot_records)

uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx'])
if uploaded_file:
    df_raw = pd.read_excel(uploaded_file)
    if not any('id' in str(c).lower() for c in df_raw.columns):
        df_raw = pd.read_excel(uploaded_file, header=1)

    if st.button("🚀 Calculate Final OT Report"):
        final_df = process_data(df_raw)
        if final_df is not None:
            st.success("4 aur 21 tarikh ko National Holiday maan kar pura OT calculate kiya gaya hai.")
            st.dataframe(final_df)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False)
            st.download_button("📥 Download Report", output.getvalue(), "Holiday_OT_Report.xlsx")
