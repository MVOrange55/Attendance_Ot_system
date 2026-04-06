import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Orange House HR MS", layout="wide")

def parse_t(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '00:00']: return None
    try: return datetime.strptime(str(val).strip(), '%H:%M').time()
    except: return None

def apply_muster_style(val):
    if 'P (SL)' in str(val): return 'background-color: #FFFF00; color: black;' # Yellow
    elif 'AB/' in str(val): return 'background-color: #0000FF; color: white;' # Blue
    elif val in ['WO', 'WOP', 'NH']: return 'background-color: #008000; color: white;' # Green
    elif val == 'A': return 'background-color: #FF0000; color: white;' # Red
    return ''

# --- 2. CORE PROCESSING ENGINE ---
def process_hr_system(df, nh_list):
    df.columns = [str(c).strip() for c in df.columns]
    id_col, name_col = df.columns[0], df.columns[1]
    df[id_col] = df[id_col].ffill()
    df[name_col] = df[name_col].ffill()
    dates = [c for c in df.columns if c.isdigit()]
    
    muster, ot_rep, ex_sum, ex_det, miss_p = [], [], [], [], []

    for eid in df[id_col].unique():
        if pd.isna(eid): continue
        block = df[df[id_col] == eid].reset_index(drop=True)
        ename, emp_id = block.iloc[0][name_col], str(int(float(eid)))
        
        row_m, row_ot = {"Emp ID": emp_id, "Name": ename}, {"Emp ID": emp_id, "Name": ename}
        l_cnt, e_cnt, ab_cnt, a_cnt, p_cnt = 0, 0, 0, 0, 0
        l_dt, l_tm, e_dt, e_tm, ab_dates = [], [], [], [], []
        sl_used_date = "--"

        for d in dates:
            day_status, day_ot = "A", 0
            t_in_raw = parse_t(block.iloc[1][d])
            t_out = parse_t(block.iloc[2][d])
            
            # --- Miss Punch Logic ---
            if (t_in_raw and not t_out):
                miss_p.append({"Emp ID": emp_id, "Name": ename, "Date": d, "In Time": t_in_raw.strftime('%H:%M'), "Out Time": "--:--", "Current Status": "Out Punch Miss"})
                continue
            if (not t_in_raw and t_out):
                miss_p.append({"Emp ID": emp_id, "Name": ename, "Date": d, "In Time": "--:--", "Out Time": t_out.strftime('%H:%M'), "Current Status": "In Punch Miss"})
                continue
            if not t_in_raw and not t_out:
                a_cnt += 1; row_m[d] = "A"; continue

            # --- Calculation Logic (Locked Rules) ---
            t_in = max(t_in_raw, time(9, 30))
            d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
            work_hrs = (d2 - d1).total_seconds() / 3600
            req_out = d1 + timedelta(hours=8.5)
            early_min = (req_out - d2).total_seconds() / 60

            # Violation Checks
            is_late = t_in_raw > time(9, 35)
            is_early = early_min > 2 # 2-min grace logic
            
            if is_late: l_cnt += 1; l_dt.append(d); l_tm.append(t_in_raw.strftime('%H:%M'))
            if is_early: e_cnt += 1; e_dt.append(d); e_tm.append(t_out.strftime('%H:%M'))

            # Status Decision
            if is_late or is_early:
                if sl_used_date == "--" and time(9, 35) < t_in_raw <= time(10, 15) and not is_early:
                    day_status = "P (SL)"; sl_used_date = d; p_cnt += 1
                else:
                    day_status = "AB/"; ab_cnt += 1; ab_dates.append(d)
            else:
                day_status = "P"; p_cnt += 1
                if work_hrs > 8.5:
                    extra = work_hrs - 8.5
                    day_ot = 0.25 if extra < 2 else 0.5 if extra < 4 else 0.75 if extra < 6 else 1

            row_m[d], row_ot[d] = day_status, day_ot

        # Data Packing
        muster.append(row_m); ot_rep.append(row_ot)
        ex_sum.append({"Emp ID": emp_id, "Name": ename, "Total Late In": l_cnt, "Total Early Out": e_cnt, "SL Status": sl_used_date, "Total AB/": ab_cnt, "Total Absent": a_cnt})
        ex_det.append({"Emp ID": emp_id, "Name": ename, "Late In (Date:Time)": ", ".join([f"{dt}({tm})" for dt, tm in zip(l_dt, l_tm)]), "Early Out (Date:Time)": ", ".join([f"{dt}({tm})" for dt, tm in zip(e_dt, e_tm)]), "Final Status & AB/ Dates": f"{sl_used_date if sl_used_date != '--' else ''} AB/ Dates: {', '.join(ab_dates)}"})

    return muster, ot_rep, ex_sum, ex_det, miss_p

# --- 3. UI DASHBOARD ---
st.sidebar.header("ORANGE HOUSE HR")
nav = st.sidebar.selectbox("Select Report", ["1. Attendance Muster", "2. Overtime (OT) Report", "3. Exception Summary Report", "4. Exception Detailed Report", "5. Miss Punch Report", "6. Miss Punch Correction", "7. Attendance Summary"])
f = st.sidebar.file_uploader("Upload Excel", type=['xlsx'])
h = st.sidebar.multiselect("NH Holidays", range(1, 32))

if f:
    m, o, s, d, mp = process_hr_system(pd.read_excel(f), h)
    
    if "1." in nav: st.dataframe(pd.DataFrame(m).style.applymap(apply_muster_style))
    elif "2." in nav: st.dataframe(pd.DataFrame(o))
    elif "3." in nav: st.dataframe(pd.DataFrame(s))
    elif "4." in nav: st.dataframe(pd.DataFrame(d))
    elif "5." in nav: st.table(pd.DataFrame(mp))
    elif "6." in nav: st.info("Use this section to manually override punches.")
    elif "7." in nav: st.write("### Monthly Totals Section")
