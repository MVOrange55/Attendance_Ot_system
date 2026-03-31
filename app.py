import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

st.set_page_config(page_title="Final OT System", layout="wide")
st.title("📊 Smart Attendance & OT System")

def round_ot(hours):
    """Rounding: <15=0, 15-29=0.25, 30-44=0.50, 45-59=0.75, 60=1.0"""
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
    # 1. कॉलम के नाम क्लीन करना
    df.columns = [str(c).strip() for c in df.columns]
    cols = df.columns.tolist()
    
    # मुख्य कॉलम पहचानना
    emp_id_col = next((c for c in cols if 'id' in c.lower()), None)
    name_col = next((c for c in cols if 'name' in c.lower()), None)
    header_col = next((c for c in cols if any(x in c.lower() for x in ['date', 'status', 'type'])), None)

    if not emp_id_col or not header_col:
        st.error(f"कॉलम नहीं मिले! चेक करें कि 'Emp ID' और 'Date/Status' कॉलम मौजूद हैं।")
        return None

    # 2. Forward Fill: ID और Name को नीचे तक भरना (Kyuki ye ek hi baar hain)
    df[emp_id_col] = df[emp_id_col].ffill()
    if name_col:
        df[name_col] = df[name_col].ffill()
    
    # तारीख वाले कॉलम (1, 2, 3... 31)
    date_cols = [c for c in cols if str(c).isdigit()]
    std_hrs = 8.5
    ot_records = []

    # 3. एम्प्लोयी के हिसाब से डेटा ग्रुप करना
    for eid in df[emp_id_col].unique():
        emp_block = df[df[emp_id_col] == eid]
        name = emp_block[name_col].iloc[0] if name_col else "Unknown"
        
        row_summary = {"Emp ID": eid, "Name": name}
        
        # ब्लॉक के अंदर Status और Out Time वाली लाइनों को पहचानना
        st_row = emp_block[emp_block[header_col].astype(str).str.contains('P|A|WO|Status', case=False, na=False)]
        out_row = emp_block[emp_block[header_col].astype(str).str.contains('Out', case=False, na=False)]

        for day in date_cols:
            try:
                status = str(st_row[day].values[0]).strip().upper() if not st_row.empty else 'A'
                out_val = str(out_row[day].values[0]).strip() if not out_row.empty else ''

                if 'A' in status or out_val.lower() in ['nan', ''] or out_val == "":
                    row_summary[day] = 0
                    continue

                # टाइम पार्सिंग (24hr या AM/PM)
                try:
                    t_out = datetime.strptime(out_val, '%H:%M').time()
                except:
                    t_out = datetime.strptime(out_val, '%I:%M %p').time()

                t_in = time(9, 30) # Default Standard In-Time
                dt_in = datetime.combine(datetime.today(), t_in)
                dt_out = datetime.combine(datetime.today(), t_out)
                
                if dt_out <= dt_in: dt_out += timedelta(days=1)
                
                total_work_hrs = (dt_out - dt_in).total_seconds() / 3600

                # OT Calculation Rule
                if 'WO' in status:
                    ot_hrs = total_work_hrs # Week Off = Full OT
                else:
                    ot_hrs = max(0, total_work_hrs - std_hrs) # Present = After 8.5h

                row_summary[day] = round_ot(ot_hrs)
            except:
                row_summary[day] = 0
        
        # पूरे महीने का जोड़
        row_summary["Total Month OT"] = sum([v for k,v in row_summary.items() if str(k).isdigit()])
        ot_records.append(row_summary)

    return pd.DataFrame(ot_records)

# --- Streamlit UI ---
uploaded_file = st.file_uploader("Upload Attendance Excel", type=['xlsx'])

if uploaded_file:
    # फाइल को रीड करना
    df_raw = pd.read_excel(uploaded_file)
    
    # अगर हेडर पहली लाइन में नहीं है, तो उसे ठीक करना
    emp_id_check = next((c for c in df_raw.columns if 'id' in str(c).lower()), None)
    if not emp_id_check:
        df_raw = pd.read_excel(uploaded_file, header=1)

    st.success("File Uploaded Successfully!")
    
    if st.button("🚀 Generate Final One-Row OT"):
        final_df = process_data(df_raw)
        if final_df is not None:
            st.subheader("Monthly OT Summary")
            st.dataframe(final_df)
            
            # Excel Download Button
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False)
            st.download_button("📥 Download Final Excel Report", output.getvalue(), "Employee_OT_Report.xlsx")
