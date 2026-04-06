import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- Page Config ---
st.set_page_config(page_title="Orange House HR", layout="wide")

st.title("🍊 Orange House HR Master")

# --- Helper functions ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '0', '00:00']: return None
    try:
        v = str(val).strip()
        if ':' in v: return datetime.strptime(v[:5], '%H:%M').time()
        else: return (datetime(1900, 1, 1) + timedelta(days=float(v))).time()
    except: return None

def calculate_ot_final(work_hrs, status, is_wo):
    if is_wo: ot_exact = work_hrs 
    elif status == "AB/": ot_exact = max(0, work_hrs - 4.0)
    else: ot_exact = max(0, work_hrs - 8.5)
    
    if ot_exact <= 0: return 0
    h = int(ot_exact)
    m = (ot_exact - h) * 60
    if m < 15: rm = 0
    elif m < 30: rm = 0.25
    elif m < 45: rm = 0.50
    elif m < 60: rm = 0.75
    else: h += 1; rm = 0
    return h + rm

# --- Main Logic ---
f = st.sidebar.file_uploader("Upload Excel File", type=['xlsx'])

if f:
    try:
        df = pd.read_excel(f)
        st.success("File Upload Ho Gayi! Processing shuru...")
        
        fixed_wo = [1, 4, 8, 15, 21, 22, 29]
        df.columns = [str(c).strip() for c in df.columns]
        
        id_col, name_col = df.columns[0], df.columns[1]
        df[id_col] = df[id_col].ffill()
        df[name_col] = df[name_col].ffill()
        
        dates = [c for c in df.columns if c.replace('.0','').isdigit()]
        
        if not dates:
            st.error("Error: Excel mein Date columns (1, 2, 3...) nahi mile!")
        else:
            muster = []
            # Sirf sample ke liye Muster report dikhate hain
            for eid in df[id_col].unique():
                if pd.isna(eid): continue
                block = df[df[id_col] == eid].reset_index(drop=True)
                ename = str(block.iloc[0][name_col])
                
                # Rows dhundhna
                in_row = block[block.iloc[:, 2].astype(str).str.contains('In', case=False, na=False)].head(1)
                out_row = block[block.iloc[:, 2].astype(str).str.contains('Out', case=False, na=False)].head(1)
                
                row_m = {"ID": eid, "Name": ename}
                sl_used = False
                
                for d in dates:
                    t_in = parse_t(in_row[d].values[0]) if not in_row.empty else None
                    t_out = parse_t(out_row[d].values[0]) if not out_row.empty else None
                    is_wo = int(float(d)) in fixed_wo
                    
                    if is_wo: 
                        row_m[d] = "WO"
                    elif not t_in or not t_out:
                        row_m[d] = "A"
                    else:
                        # Work hours calculation logic yahan aayega
                        row_m[d] = "P"
                
                muster.append(row_m)
            
            st.write("### Attendance Preview")
            st.dataframe(pd.DataFrame(muster))
            
    except Exception as e:
        st.error(f"Kuch galat hua: {e}")
else:
    st.warning("Kripya Excel file sidebar se upload karein.")
