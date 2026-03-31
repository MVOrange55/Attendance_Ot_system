import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

st.set_page_config(page_title="Final OT System", layout="wide")
st.title("📊 Official OT Calculator (All Rules Fixed)")

def calculate_final_ot(total_hrs, is_full_ot_day):
    # RULE: Agar WO, WOP, 4 ya 21 tarikh hai toh Pura OT, warna 8.5 minus
    if is_full_ot_day:
        ot_exact = total_hrs
    else:
        ot_exact = max(0, total_hrs - 8.5)
    
    if ot_exact <= 0: return 0
    
    # ROUNDING RULE: <15=0, 15=0.25, 30=0.50, 45=0.75
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
    
    # Flexible column detection to avoid KeyError
    emp_id_col = next((c for c in cols if 'id' in c.lower()), None)
    name_col = next((c for c in cols if 'name' in c.lower()), None)
    header_col = next((c for c in cols if any(x in c.lower() for x in ['date', 'status', 'type', 'unnamed'])), None)

    if not emp_id_col:
        st.error("Excel mein 'Emp ID' column nahi mila!")
        return None

    # Blank cells ko ID aur Name se bharna
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
        
        # Status aur Out Time rows ko dhundhna
        st_row = emp_block[emp_block[header_col].astype(str).str.contains('Status|P|A|WO|WOP', case=False, na=False)].head(1)
        out_row = emp_block[emp_block[header_col].astype(str).str.contains('Out', case=False, na=False)].head(1)

        for day in date_cols:
            try:
                day_num = int(str(day).replace('.0',''))
                status_val = str(st_row[day].values[0]).strip().upper() if not st_row.empty else ''
                out_val = str(out_row[day].values[0]).strip() if not out_row.empty else ''

                if out_val.lower() in ['nan', '', '0', '00:00']:
                    row_summary[day] = 0
                    continue
                
                # 09:30 AM Shift Logic
                if ':' in out_val:
                    t_out = datetime.strptime(out_val[:5], '%H:%M').time()
                else:
                    t_out = (datetime(1900, 1, 1) + timedelta(days=float(out_val))).time()

                t_in = time(9, 30)
                dt_in = datetime.combine(datetime.today(), t_in)
                dt_out = datetime.combine(datetime.today(), t_out)
                
                if dt_out <= dt_in: dt_out += timedelta(days=1)
                total_hrs = (dt_out - dt_in).total_seconds() / 3600

                # RULE CHECK: WO, WOP, Tareekh 4 ya 21 par Pura OT
                is_full_ot_day = (day_num in [4, 21]) or ('WO' in status_val) or ('WOP' in status_val)
                
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
            st.success("Syntax Error theek ho gayi hai! Sabhi rules ab lagu hain.")
            st.dataframe(final_df)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False)
            st.download_button("📥 Download Excel", output.getvalue(), "Official_OT_Report.xlsx")
