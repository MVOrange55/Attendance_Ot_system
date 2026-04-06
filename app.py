import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #fdf2e9; }
    .stButton>button { background-color: #d35400; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '0', '00:00']: return None
    try:
        v = str(val).strip()
        if ':' in v: return datetime.strptime(v[:5], '%H:%M').time()
        else: return (datetime(1900, 1, 1) + timedelta(days=float(v))).time()
    except: return None

def calculate_ot_final(work_hrs, status, is_wo):
    """
    Rules:
    - Sunday/WO: Full OT
    - AB/ Status: (Work Hours - 4) if Work Hours > 4
    - P or P(SL): (Work Hours - 8.5)
    """
    if is_wo:
        ot_exact = work_hrs
    elif status == "AB/":
        ot_exact = max(0, work_hrs - 4.0)
    else:
        ot_exact = max(0, work_hrs - 8.5)
    
    if ot_exact <= 0: return 0
    
    # 15-min Rounding
    h = int(ot_exact)
    m = (ot_exact - h) * 60
    if m < 15: rm = 0
    elif m < 30: rm = 0.25
    elif m < 45: rm = 0.50
    elif m < 60: rm = 0.75
    else: h += 1; rm = 0
    return h + rm

# --- 3. CORE PROCESSING ---
def process_hr_master(df, nh_list):
    df.columns = [str(c).strip() for c in df.columns]
    id_col, name_col = df.columns[0], df.columns[1]
    df[id_col] = df[id_col].ffill()
    df[name_col] = df[name_col].ffill()
    
    dates = [c for c in df.columns if str(c).replace('.0','').isdigit()]
    muster, ot_rep, ex_sum, ex_det, miss_p, final_sum = [], [], [], [], [], []

    for eid in df[id_col].unique():
        if pd.isna(eid): continue
        block = df[df[id_col] == eid].reset_index(drop=True)
        ename, emp_id = str(block.iloc[0][name_col]), str(eid).replace('.0','')
        
        # Row identification
        st_row = block[block.iloc[:, 2].astype(str).str.contains('Status|P|A|WO', case=False, na=False)].head(1)
        in_row = block[block.iloc[:, 2].astype(str).str.contains('In', case=False, na=False)].head(1)
        out_row = block[block.iloc[:, 2].astype(str).str.contains('Out', case=False, na=False)].head(1)

        row_m, row_ot = {"Emp ID": emp_id, "Name": ename}, {"Emp ID": emp_id, "Name": ename}
        p_c, a_c, ab_c, wo_c, tot_ot = 0, 0, 0, 0, 0
        sl_used = False # Mahine ki ek SL track karne ke liye

        for d in dates:
            t_in = parse_t(in_row[d].values[0]) if not in_row.empty else None
            t_out = parse_t(out_row[d].values[0]) if not out_row.empty else None
            status_val = str(st_row[d].values[0]).upper() if not st_row.empty else ""
            
            is_wo = (int(float(d)) in nh_list) or ('WO' in status_val)

            if not t_in and not t_out:
                row_m[d] = "A"; a_c += 1; row_ot[d] = 0; continue
            if not t_in or not t_out:
                miss_p.append({"Emp ID": emp_id, "Name": ename, "Date": d, "Type": "Miss Punch"})
                row_m[d] = "Miss"; row_ot[d] = 0; continue

            # Work Duration
            d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
            if d2 <= d1: d2 += timedelta(days=1)
            work_hrs = (d2 - d1).total_seconds() / 3600

            # --- ATTENDANCE STATUS LOGIC (YOUR SPECIFIC RULES) ---
            day_status = "P"
            if is_wo:
                day_status = "WO"; wo_c += 1
            else:
                # Rule 1 & 2: 9:30-10:16 entry with 8.5 hrs completion
                if t_in <= time(10, 16) and work_hrs >= 8.5:
                    day_status = "P"; p_c += 1
                
                # Rule 3, 4, 5: Late after 10:16 OR Early Exit (Short Leave vs AB/)
                elif t_in > time(10, 16) or work_hrs < 8.5:
                    if not sl_used:
                        day_status = "P (SL)"
                        sl_used = True
                        p_c += 1
                    else:
                        # Agar SL khatam hai toh AB/, bhale 8.5 hrs poore hon
                        day_status = "AB/"
                        ab_c += 1
                else:
                    day_status = "P"; p_c += 1

            # --- OT CALCULATION (9:30 Fix & AB/ 4hr Rule) ---
            t_in_calc = t_in if (is_wo or (time(9, 30) < t_in <= time(10, 15))) else time(9, 30)
            d1_ot = datetime.combine(datetime.today(), t_in_calc)
            if d2 <= d1_ot: d2 += timedelta(days=1)
            ot_work_hrs = (d2 - d1_ot).total_seconds() / 3600
            
            day_ot = calculate_ot_final(ot_work_hrs, day_status, is_wo)
            
            row_m[d], row_ot[d] = day_status, day_ot
            tot_ot += day_ot

        # Summary packing
        row_m.update({"Total P": p_c, "Total A": a_c, "Total AB/": ab_c, "Total WO": wo_c})
        row_ot["Total Month OT"] = tot_ot
        muster.append(row_m); ot_rep.append(row_ot)
        final_sum.append({"Emp ID": emp_id, "Name": ename, "P": p_c, "A": a_c, "AB/": ab_c, "WO": wo_c, "OT": tot_ot})

    return pd.DataFrame(muster), pd.DataFrame(ot_rep), pd.DataFrame(miss_p), pd.DataFrame(final_sum)

# --- 4. APP UI ---
st.title("🍊 Orange House HR Master System")
nav = st.sidebar.selectbox("Report", ["1. Muster", "2. OT Report", "3. Miss Punch", "4. Final Summary"])
f = st.sidebar.file_uploader("Upload Excel", type=['xlsx'])
h = st.sidebar.multiselect("Select Sundays/Holidays", range(1, 32))

if f:
    m, o, mp, fs = process_hr_master(pd.read_excel(f), h)
    reports = {"1. Muster": m, "2. OT Report": o, "3. Miss Punch": mp, "4. Final Summary": fs}
    st.dataframe(reports[nav], use_container_width=True)
