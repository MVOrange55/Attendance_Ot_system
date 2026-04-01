import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

st.set_page_config(page_title="Final OT System", layout="wide")
st.title("📊 Final OT System (Actual In-Time + Total Hrs Row)")

def calculate_final_ot(total_hrs, is_full_ot_day):
    # Rule: Off/Holiday par pura time, normal din par -8.5
    if is_full_ot_day:
        ot_exact = total_hrs
    else:
        ot_exact = max(0, total_hrs - 8.5)
    
    if ot_exact <= 0: return 0
    
    # Rounding Rule
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
    header_col = next((c for c in cols if 'date' in c.lower()), None)

    if not emp_id_col or not header_col:
        st.error("Check karein: Excel mein 'Emp ID' aur 'Date' column header hone chahiye.")
        return None

    df[emp_id_col] = df[emp_id_col].ffill()
    if name_col: df[name_col] = df[name_col].ffill()
    
    date_cols = [c for c in cols if str(c).replace('.0','').isdigit()]
    final_output_rows = []

    for eid in df[emp_id_col].unique():
        if pd.isna(eid): continue
        emp_block = df[df[emp_id_col] == eid]
        name = emp_block[name_col].iloc[0] if name_col else "Unknown"
        
        # Rows identifying: Status, In, Out, aur aapka 'Total' row
        st_row = emp_block[emp_block[header_col].astype(str).str.contains('Status|P|A|WO', case=False, na=False)].head(1)
        in_row = emp_block[emp_block[header_col].astype(str).str.contains('In', case=False, na=False)].head(1)
        out_row = emp_block[emp_block[header_col].astype(str).str.contains('Out', case=False, na=False)].head(1)
        total_hrs_row = emp_block[emp_block[header_col].astype(str).str.contains('Total', case=False, na=False)].head(1)

        # Pehle original rows add karo (Status, In, Out, Total)
        if not st_row.empty: final_output_rows.append(st_row.iloc[0].to_dict())
        if not in_row.empty: final_output_rows.append(in_row.iloc[0].to_dict())
        if not out_row.empty: final_output_rows.append(out_row.iloc[0].to_dict())
        if not total_hrs_row.empty: final_output_rows.append(total_hrs_row.iloc[0].to_dict())

        # Ab "TOTAL OT" row calculate karo
        ot_row = {emp_id_col: eid, name_col: name, header_col: "TOTAL OT"}
        monthly_total_ot = 0

        for day in date_cols:
            try:
                status_val = str(st_row[day].values[0]).strip().upper() if not st_row.empty else ''
                in_val = str(in_row[day].values[0]).strip() if not in_row.empty else ''
                out_val = str(out_row[day].values[0]).strip() if not out_row.empty else ''
                
                if out_val.lower() in ['nan', '', '0', '00:00']:
                    ot_row[day] = 0
                    continue

                day_num = int(str(day).replace('.0',''))
                is_full_ot_day = (day_num in [4, 21]) or ('WO' in status_val) or ('WOP' in status_val)

                def parse_t(val):
                    if ':' in val: return datetime.strptime(val[:5], '%H:%M').time()
                    return (datetime(1900, 1, 1) + timedelta(days=float(val))).time()

                t_out = parse_t(out_val)
                # Rule: Off/Holiday par actual In, normal din par 9:30 AM
                t_in = parse_t(in_val) if (is_full_ot_day and in_val not in ['', 'nan', '0']) else time(9, 30)

                dt_in = datetime.combine(datetime.today(), t_in)
                dt_out = datetime.combine(datetime.today(), t_out)
                if dt_out <= dt_in: dt_out += timedelta(days=1)
                
                calc_hrs = (dt_out - dt_in).total_seconds() / 3600
                daily_ot = calculate_final_ot(calc_hrs, is_full_ot_day)
                
                ot_row[day] = daily_ot
                monthly_total_ot += daily_ot
            except:
                ot_row[day] = 0
        
        ot_row["Total Month OT"] = monthly_total_ot
        final_output_rows.append(ot_row) # Sabse niche OT row

    return pd.DataFrame(final_output_rows)

uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx'])
if uploaded_file:
    df_raw = pd.read_excel(uploaded_file)
    if not any('id' in str(c).lower() for c in df_raw.columns):
        df_raw = pd.read_excel(uploaded_file, header=1)

    if st.button("🚀 Generate Final Report"):
        final_df = process_data(df_raw)
        if final_df is not None:
            st.dataframe(final_df)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False)
            st.download_button("📥 Download Excel", output.getvalue(), "Final_OT_Report.xlsx")
