import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Orange House HR Portal", layout="wide", page_icon="🍊")

# --- 2. ENGINE FUNCTIONS ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00']: return None
    try:
        s = str(v).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(s))).time()
    except: return None

def get_slab_ot(extra_hrs):
    if extra_hrs < 0.25: return 0.0
    h = int(extra_hrs)
    m = round((extra_hrs - h) * 60)
    if 15 <= m < 27: slab = 0.00
    elif 29 <= m < 43: slab = 0.50
    elif 44 <= m < 57: slab = 0.75
    elif 59 <= m < 60: slab = 1.0
    elif m >= 60: h += 1; slab = 0.0
    else: slab = 0.0
    return float(h + slab)

def run_hr_engine(df, holidays, corrections):
    empty_out = {"muster": pd.DataFrame(), "summary": pd.DataFrame(), "ot": pd.DataFrame(), "log": pd.DataFrame(), "missing": pd.DataFrame()}
    if df is None or df.empty: return empty_out
    df_w = df.copy()
    id_c, name_c = df_w.columns[0], df_w.columns[1]
    df_w[id_c], df_w[name_c] = df_w[id_c].ffill(), df_w[name_c].ffill()
    for c in corrections:
        mask = df_w[id_c].astype(str).str.contains(str(c['id']))
        if any(mask):
            idx = df_w[mask].index[0]
            df_w.at[idx+1, str(c['date'])] = c['in']
            df_w.at[idx+2, str(c['date'])] = c['out']
    dates = [c for c in df_w.columns if str(c).replace('.0','').strip().isdigit()]
    sundays = [3, 10, 17, 24]
    res_m, res_s, res_o, res_ex, res_mi = [], [], [], [], []
    for eid in df_w[id_c].unique():
        if pd.isna(eid): continue
        clean_id = str(int(float(eid))) if '.' in str(eid) else str(eid).replace(':', '')
        block = df_w[df_w[id_c] == eid].reset_index(drop=True)
        ename = str(block.iloc[0][name_c])
        row_m, row_o = {"ID": clean_id, "Name": ename}, {"ID": clean_id, "Name": ename}
        sl_used, p_c, a_c, ab_c, wo_c, h_c, tot_ot = False, 0, 0, 0, 0, 0.0
        late_log, early_log = [], []
        for d in dates:
            d_i = int(float(d))
            t_in, t_out = parse_t(block.iloc[1][d]), parse_t(block.iloc[2][d])
            status, day_ot = "A", 0.0
            is_off_day = d_i in holidays or d_i in sundays
            if not t_in and not t_out:
                if d_i in sundays: status, wo_c = "WO", wo_c + 1
                elif d_i in holidays: status, h_c = "H", h_c + 1
                else: status, a_c = "A", a_c + 1
            elif (t_in and not t_out) or (not t_in and t_out):
                status, a_c = "A", a_c + 1
                m_type = "Out Missing" if t_in else "In Missing"
                res_mi.append({"ID": clean_id, "Name": ename, "Date": d_i, "In": t_in.strftime('%H:%M') if t_in else "", "Out": t_out.strftime('%H:%M') if t_out else "", "Status": m_type})
            else:
                d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
                if d2 <= d1: d2 += timedelta(days=1)
                actual_dur = (d2 - d1).total_seconds() / 3600
                if is_off_day:
                    status = "WO" if d_i in sundays else "H"
                    day_ot = get_slab_ot(actual_dur)
                    if d_i in sundays: wo_c += 1
                    else: h_c += 1
                else:
                    if t_in >= time(13, 30):
                        t_start = time(14, 0)
                        work_hrs = (d2 - datetime.combine(datetime.today(), t_start)).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 4.0) if work_hrs > 4.0 else 0.0
                        status = "AB/"
                    else:
                        t_start_calc = max(t_in, time(9, 30))
                        work_hrs = (d2 - datetime.combine(datetime.today(), t_start_calc)).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 8.5) if work_hrs > 8.5 else 0.0
                        status = "P" if actual_dur >= 4.0 else "AB/"
                    if status in ["P", "P*"]: p_c += 1
                    elif status == "AB/": ab_c += 0.5
            row_m[str(d_i)], row_o[str(d_i)] = status, day_ot
            tot_ot += day_ot
        res_m.append(row_m)
        res_s.append({"Emp ID": clean_id, "Name": ename, "Present (P)": p_c, "Absent (A)": a_c, "Half Day (AB/)": ab_c, "Holiday (H)": h_c, "Weekly Off (WO)": wo_c, "Total OT Hours": tot_ot, "Payable Days": (p_c + ab_c + wo_c + h_c)})
        res_o.append({**row_o, "Total OT Hours": tot_ot})
        res_ex.append({"Emp ID": clean_id, "Name": ename, "Late Days": len(late_log), "Early Out": len(early_log)})
    return {"muster": pd.DataFrame(res_m), "summary": pd.DataFrame(res_s), "ot": pd.DataFrame(res_o), "log": pd.DataFrame(res_ex), "missing": pd.DataFrame(res_mi)}

# --- 3. SESSION STATES ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'corrs' not in st.session_state: st.session_state.corrs = []
if 'profiles' not in st.session_state: st.session_state.profiles = []

# --- 4. UI ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color: #f97316;'>Orange House HR Portal</h1>", unsafe_allow_html=True)
    u = st.text_input("User ID")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "admin" and p == "orange_hr": st.session_state.auth = True; st.rerun()
        else: st.error("Wrong Password!")
else:
    app_mode = st.sidebar.radio("Navigation:", ["📊 Attendance Dashboard", "👤 Employee Directory"])
    
    if app_mode == "📊 Attendance Dashboard":
        st.title("Attendance Management")
        file = st.sidebar.file_uploader("Upload Excel", type=['xlsx'])
        hols = st.sidebar.multiselect("Select Holidays:", range(1, 32))
        if file:
            out = run_hr_engine(pd.read_excel(file), hols, st.session_state.corrs)
            st.dataframe(out["muster"], use_container_width=True)
            
    else:
        st.title("👤 Employee Profile Directory")
        tab1, tab2, tab3 = st.tabs(["➕ Add Profile", "📤 Import / Upload CSV", "📋 View Directory"])
        
        with tab1:
            with st.form("manual_add", clear_on_submit=True):
                p_id = st.text_input("Employee ID")
                p_name = st.text_input("Full Name")
                if st.form_submit_button("Save"):
                    st.session_state.profiles.append({'Employee ID': p_id, 'Full Name': p_name})
                    st.success("Saved!")
        
        with tab2:
            up = st.file_uploader("Upload CSV", type=['csv'])
            if up:
                df = pd.read_csv(up)
                if st.button("Confirm Import"):
                    for _, row in df.iterrows():
                        st.session_state.profiles.append({'Employee ID': str(row.get('Employee ID', '')), 'Full Name': str(row.get('Full Name', ''))})
                    st.success("Imported Successfully!"); st.rerun()
                    
        with tab3:
            if st.session_state.profiles:
                st.dataframe(pd.DataFrame(st.session_state.profiles), use_container_width=True)
