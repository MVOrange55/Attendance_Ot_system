import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

st.set_page_config(page_title="Correct OT System", layout="wide")
st.title("📊 Attendance OT Calculator (Fixed Rules)")

# --- RULE: Rounding (<15=0, 15=0.25, 30=0.50, 45=0.75) ---
def calculate_rounded_ot(total_hrs, is_week_off):
    # 1. 8.5 Hours standard cut (Agar Present hai)
    if is_week_off:
        ot_exact = total_hrs
    else:
        ot_exact = max(0, total_hrs - 8.5)
    
    if ot_exact <= 0: return 0
    
    # 2. Rounding Logic
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
    # Status/Date column jisme In/Out/Status likha hai
    header_col = next((c for c in cols if any(x in c.lower() for x in ['date', 'status', 'type', 'unnamed'])), None)

    df[emp_id_col] = df[emp_id_col].ffill()
    if name_col: df[name_col] = df[name_col].ffill()
    
    date_cols = [c for c in cols if str(c).replace('.0','').isdigit()]
    ot_records = []

    for eid in df[emp_id_col].unique():
        if pd.isna(eid): continue
        emp_block = df[df[emp_id_col] == eid]
        name = emp_block[name_col].iloc[0] if name_col else str(eid)
        row_summary = {"Emp ID": eid, "Name": name}
        
        # Status aur Out Time ki rows pehchanna
        # Hum row ke text ko check kar rahe hain
        st_row = emp_block[emp_block[header_col].astype(str).str.contains('Status|P|A|WO', case=False, na=False)].head(1)
        out_row = emp_block[emp_block[header_col].astype(str).str.contains('Out', case=False, na=False)].head(1)

        for day in date_cols:
            try:
                status_val = str(st_row[day].values[0]).strip().upper() if not st_row.empty else 'A'
                out_val = str(out_row[day].values[0]).strip() if not out_row.empty else ''

                if not any(x in status_val for x in ['P', 'WO']):
                    row_summary[day] = 0
                    continue
                
                # Time conversion
                if ':' in out_val:
                    t_out = datetime.strptime(out_val[:5], '%H:%M').time()
                else:
                    t_out = (datetime(1900, 1, 1) + timedelta(days=float(out_val))).time()

                t_in = time(9, 30) # Default Standard In
                dt_in = datetime.combine(datetime.today(), t_in)
                dt_out = datetime.combine(datetime.today(), t_out)
                
                if dt_out <= dt_in: dt_out += timedelta(days=1)
                total_hrs = (dt_out - dt_in).total_seconds() / 3600

                # Week Off hai ya Present?
                is_wo = 'WO' in status_val
                
                # Apply Rounding and 8.5 Cut Rule
                row_summary[day] = calculate_rounded_ot(total_hrs, is_wo)
            except:
                row_summary[day] = 0
        
        row_summary["Total Month OT"] = sum([v for k,v in row_summary.items() if k in date_cols])
        ot_records.append(row_summary)

    return pd.DataFrame(ot_records)

# --- Streamlit UI ---
uploaded_file = st.file_uploader("Upload Your Excel File", type=['xlsx'])

if uploaded_file:
    df_raw = pd.read_excel(uploaded_file)
    if 'Emp ID' not in df_raw.columns:
        df_raw = pd.read_excel(uploaded_file, header=1)

    if st.button("🚀 Calculate Rounded OT"):
        final_df = process_data(df_raw)
        st.write("### ✅ Final Monthly OT List (8.5h Deducted)")
        st.dataframe(final_df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False)
        st.download_button("📥 Download Correct OT Report", output.getvalue(), "Final_OT_Report.xlsx")
