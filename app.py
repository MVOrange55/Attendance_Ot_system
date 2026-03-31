import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

st.set_page_config(page_title="Final OT System", layout="wide")
st.title("📊 Attendance OT System (Holidays & Week-Offs Fixed)")

def calculate_final_ot(total_hrs, is_full_ot_day):
    # RULE: Agar WO ya Holiday (4, 21) hai toh Pura OT, warna 8.5 minus
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
    # Column cleaning
    df.columns = [str(c).strip() for c in df.columns]
    cols = df.columns.tolist()
    
    emp_id_col = next((c for c in cols if 'id' in c.lower()), None)
    name_col = next((c for c in cols if 'name' in c.lower()), None)
    header_col = next((c for c in cols if any(x in c.lower() for x in ['date', 'status', 'type'])), None)

    if not emp_id_col or not header_col:
        st.error("Zaroori columns (ID/Date) nahi mile!")
        return None

    # ID aur Name ko fill karna
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
        
        # Status aur Out Time ki lines nikalna
        st_row = emp_block[emp_block[header_col].astype(str).str.contains('Status|P|A|WO', case=False, na=False)].head(1)
        out_row = emp_block[emp_block[header_col].astype(str).str.contains('Out', case=False, na=False)].head(1)

        for day in date_cols:
            try:
                day_num = int(str(day).replace('.0',''))
                status_val = str(st_row[day].values[0]).strip().upper() if not st_row.empty else ''
                out_val = str(out_row[day].values[0]).strip() if not out_row.empty else ''

                # Agar Absent hai toh 0
                if not any(x in status_val for x in ['P', 'WO']):
                    row_summary[day] = 0
                    continue
                
                # Time parsing
                if ':' in out_val:
                    t_out = datetime.strptime(out_val[:5], '%H:%M').time()
                else:
                    t_out = (datetime(1900, 1, 1) + timedelta(days=float(out_val))).time()

                # Shift Start: 09:30 AM
                t_in = time(9, 30)
                dt_in = datetime.combine(datetime.today(), t_in)
                dt_out = datetime.combine(datetime.today(), t_out)
                
                if dt_out <= dt_in: dt_out += timedelta(days=1)
                total_hrs = (dt_out - dt_in).total_seconds() / 3600

                # FULL OT CONDITION: Week Off (WO) ho YA tareekh 4 ya 21 ho
                is_full_ot_day = ('WO' in status_val) or (day_num in [4, 21])
                
                row_summary[day] = calculate_final_ot(total_hrs, is_full_ot_day)
            except:
                row_summary[day] = 0
        
        # Monthly Total
        row_summary["Total Month OT"] = sum([v for k,v in row_summary.items() if k in date_cols])
        ot_records.append(row_summary)

    return pd.DataFrame(ot_records)

# --- App Layout ---
uploaded_file = st.file_uploader("Upload Attendance File", type=['xlsx'])

if uploaded_file:
    df_raw = pd.read_excel(uploaded_file)
    if not any('id' in str(c).lower() for c in df_raw.columns):
        df_raw = pd.read_excel(uploaded_file, header=1)

    if st.button("🚀 Generate Final Report"):
        final_df = process_data(df_raw)
        if final_df is not None:
            st.success("Report Taiyar Hai! (4, 21 aur WO par pura OT calculate kiya gaya hai)")
            st.dataframe(final_df)
            
            # Excel Download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False)
            st.download_button("📥 Download Excel", output.getvalue(), "Final_OT_Report.xlsx")
