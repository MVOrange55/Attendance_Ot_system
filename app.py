import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- CONFIG ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

# --- HELPERS ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '00:00']: return None
    try:
        s = str(val).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(s))).time()
    except: return None

# --- CORE ENGINE ---
def process_hr_system(df, nh_list):
    df.columns = [str(c).strip() for c in df.columns]
    id_c, name_c = df.columns[0], df.columns[1]
    df[id_c] = df[id_c].ffill()
    df[name_c] = df[name_c].ffill()
    dates = [c for c in df.columns if c.replace('.0','').isdigit()]
    
    muster, ot_rep, summary = [], [], []

    for eid in df[id_c].unique():
        if pd.isna(eid): continue
        block = df[df[id_c] == eid].reset_index(drop=True)
        ename = str(block.iloc[0][name_c])
        
        row_m, row_ot = {"ID": eid, "Name": ename}, {"ID": eid, "Name": ename}
        sl_used = False
        p_cnt, ab_cnt, a_cnt, tot_ot = 0, 0, 0, 0

        for d in dates:
            t_in_raw = parse_t(block.iloc[1][d])
            t_out = parse_t(block.iloc[2][d])
            
            # Holiday Check
            if int(float(d)) in nh_list:
                row_m[d], row_ot[d] = "H", 0
                continue

            # Absent Check
            if not t_in_raw or not t_out:
                row_m[d], row_ot[d] = "A", 0
                a_cnt += 1
                continue

            # --- RULE: 1:30 PM Entry ---
            t_in_eff = t_in_raw
            if t_in_raw >= time(13, 30) and t_in_raw < time(14, 0):
                t_in_eff = time(14, 0) # Count from 2 PM

            d1 = datetime.combine(datetime.today(), t_in_eff)
            d2 = datetime.combine(datetime.today(), t_out)
            if d2 <= d1: d2 += timedelta(days=1)
            work_hrs = (d2 - d1).total_seconds() / 3600

            # --- STATUS LOGIC ---
            status = "P"
            
            # Late Entry Logic
            if t_in_raw > time(10, 16):
                if not sl_used:
                    status = "P (SL)"; sl_used = True
                else:
                    status = "AB/"
            
            # 1:30 PM onwards is Half Day
            if t_in_raw >= time(13, 30):
                status = "AB/"

            # Early Out Logic (2 hours before 6 PM is 4 PM)
            if t_out < time(16, 0):
                if not sl_used and status != "AB/":
                    status = "P (SL)"; sl_used = True
                else:
                    status = "AB/"

            # 4-Hour Work Rule
            if work_hrs <= 4.1: # Small buffer
                status = "AB/"

            # --- OT CALCULATION ---
            # For P/SL: OT after 8.5 hrs. For AB/: OT after 4 hrs.
            day_ot =
