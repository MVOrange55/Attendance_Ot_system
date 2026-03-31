import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

st.set_page_config(page_title="Final OT System", layout="wide")
st.title("📊 Smart OT System (WO/WOP & Holiday Fixed)")

def calculate_final_ot(total_hrs, is_full_ot_day):
    # Rule: Agar WO, WOP, 4 ya 21 tarikh hai toh Pura OT milega
    if is_full_ot_day:
        ot_exact = total_hrs
    else:
        # Normal din (P) par 8.5 hours duty ke baad OT shuru
        ot_exact = max(0, total_hrs - 8.5)
    
    if ot_exact <= 0: return 0
    
    # Rounding Rule: <15=0, 15=0.25, 30=0.50, 45=0.75
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
    header_col = next((c for c in cols if any(x in c.lower() for x in ['date', 'status', 'type', 'unnamed'])), None)

    if not emp_id_col:
        st.error("Emp ID column nahi mila!")
        return None

    df[emp_id_col] = df[emp_id_col].ffill()
    if name_col:
        df[name
