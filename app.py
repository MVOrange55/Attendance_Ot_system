import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #fdf2e9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #d35400; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS (TIME & EXPORT) ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '00:00']: return None
    try: return datetime.strptime(str(val).strip(), '%H:%M').time()
    except: return None

def get_excel_download(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# --- 3. MASTER PROCESSING ENGINE (ALL RULES INCLUDED) ---
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
        l_dt_tm, e_dt_tm, ab_dates = [], [], []
        sl_used_date = "--"

        for d in dates:
            t_in_raw = parse_t(block.iloc[1][d])
            t_out = parse_t(block.iloc[2][d])
            
            # Rule: Miss Punch (Single Missing Only)
            if (t_in_raw and not t_out):
                miss_p.append({"Emp ID": emp_id, "Name": ename, "Date": d, "In Time": t_in_raw.strftime('%H:%M'), "Out Time": "--:--", "Current Status": "Out Punch Miss"})
                row_m[d] = "Miss"; continue
            if (not t_in_raw and t_out):
                miss_p.append({"Emp ID": emp_id, "Name": ename, "Date": d, "In Time": "--:--", "Out Time": t_out.strftime('%H:%M'), "Current Status": "In Punch Miss"})
                row_m[d] = "Miss"; continue
            if not t_in_raw and not t_out:
                a_cnt += 1; row_m[d] = "A"; row_ot[d] = 0; continue

            # Rule: 9:30 AM Hard Lock
            t_in = max(t_in_raw, time(9, 30))
            d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
            work_hrs = (d2 - d1).total_seconds() / 3600
            req_out = d1 + timedelta(hours=8.5)
            early_min = (req_out - d2).total_seconds() / 60

            # Violation Checks
            is_late = t_in_raw > time(9, 35)
            is_early = early_min > 2 # 2-min grace
            
            if is_late: l_cnt += 1; l_dt_tm.append(f"{d}({t_in_raw.strftime('%H:%M')})")
            if is_early: e_cnt += 1; e_dt_tm.append(f"{d}({t_out.strftime('%H:%M')})")

            # Status Decision (SL vs AB/ vs P)
            day_ot = 0
            if is_late or is_early:
                if sl_used_date == "--" and time(9, 35) < t_in_raw <= time(10, 15) and not is_early:
                    day_status = "P (SL)"; sl_used_date = d; p_cnt += 1
                else:
                    day_status = "AB/"; ab_cnt += 1; ab_dates.append(d)
            else:
                day_status = "P"; p_cnt += 1
                # OT Slab: .25, .50, .75, 1
                if work_hrs > 8.5:
                    ex = work_hrs - 8.5
                    day_ot = 0.25 if ex < 2 else 0.5 if ex < 4 else 0.75 if ex < 6 else 1

            row_m[d], row_ot[d] = day_status, day_ot

        # Packing Reports
        muster.append(row_m); ot_rep.append(row_ot)
        ex_sum.append({"Emp ID": emp_id, "Name": ename, "Total Late In": l_cnt, "Total Early Out": e_cnt, "SL Status": sl_used_date, "Total AB/": ab_cnt, "Total Absent": a_cnt})
        ex_det.append({"Emp ID": emp_id, "Name": ename, "Late In (Date:Time)": ", ".join(l_dt_tm), "Early Out (Date:Time)": ", ".join(e_dt_tm), "Final Status & AB/ Dates": f"SL: {sl_used_date} | AB/ Dates: {', '.join(ab_dates)}"})

    return pd.DataFrame(muster), pd.DataFrame(ot_rep), pd.DataFrame(ex_sum), pd.DataFrame(ex_det), pd.DataFrame(miss_p)

# --- 4. APP UI & NAVIGATION ---
st.title("🍊 Orange House HR Master System")

with st.sidebar:
    st.header("Control Panel")
    nav = st.selectbox("Select Report Type", [
        "1. Attendance Muster", "2. Overtime (OT) Report", "3. Exception Summary Report",
        "4. Exception Detailed Report", "5. Miss Punch Report", "6. Miss Punch Correction", "7. Attendance Summary"
    ])
    f = st.file_uploader("Upload Excel File", type=['xlsx'])
    h = st.multiselect("Select NH Holidays", range(1, 32))

if f:
    m_df, o_df, s_df, d_df, mp_df = process_hr_system(pd.read_excel(f), h)
    
    # Logic to show selected report
    active_df = pd.DataFrame()
    if "1." in nav: active_df = m_df
    elif "2." in nav: active_df = o_df
    elif "3." in nav: active_df = s_df
    elif "4." in nav: active_df = d_df
    elif "5." in nav: active_df = mp_df
    
    st.subheader(nav)
    st.dataframe(active_df, use_container_width=True)

    # --- DOWNLOAD SECTION ---
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        xl_data = get_excel_download(active_df)
        st.download_button(label="📥 Download as EXCEL", data=xl_data, file_name=f"{nav}.xlsx", mime="application/vnd.ms-excel")
    with c2:
        st.button("📄 Download as PDF (Coming Soon)") # PDF Logic needs additional library config
