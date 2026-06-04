import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- CONFIG ---
st.set_page_config(page_title="Orange House HR Portal", layout="wide", page_icon="🍊")

# --- SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'corrs' not in st.session_state: st.session_state.corrs = []
if 'profiles' not in st.session_state: st.session_state.profiles = []

# --- ENGINE FUNCTIONS ---
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
    if df is None or df.empty: return None, None, None, None, None
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
        p_c, a_c, ab_c, wo_c, h_c, tot_ot = 0, 0, 0, 0, 0, 0.0
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
                    if t_in >= time(13, 30): status = "AB/"
                    else:
                        work_hrs = (d2 - datetime.combine(datetime.today(), max(t_in, time(9, 30)))).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 8.5) if work_hrs > 8.5 else 0.0
                        status = "P" if actual_dur >= 4.0 else "AB/"
                    if status == "P": p_c += 1
                    elif status == "AB/": ab_c += 0.5
            row_m[str(d_i)], row_o[str(d_i)] = status, day_ot
            tot_ot += day_ot
        res_m.append(row_m)
        res_s.append({"ID": clean_id, "Name": ename, "P": p_c, "A": a_c, "AB/": ab_c, "H": h_c, "WO": wo_c, "OT": tot_ot})
        res_o.append({**row_o, "Total OT": tot_ot})
    return pd.DataFrame(res_m), pd.DataFrame(res_s), pd.DataFrame(res_o), pd.DataFrame(res_ex), pd.DataFrame(res_mi)

# --- UI ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color: #f97316;'>Orange House HR Portal</h1>", unsafe_allow_html=True)
    u = st.text_input("User ID"); p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "admin" and p == "orange_hr": st.session_state.auth = True; st.rerun()
else:
    nav = st.sidebar.radio("Navigation:", ["📊 Attendance", "👤 Employee Directory"])
    
    if nav == "📊 Attendance":
        st.subheader("📊 Attendance Portal")
        file = st.sidebar.file_uploader("Upload Excel", type=['xlsx'])
        hols = st.sidebar.multiselect("Holidays (Dates):", range(1, 32))
        if file:
            df_raw = pd.read_excel(file)
            m, s, o, ex, mi = run_hr_engine(df_raw, hols, st.session_state.corrs)
            st.dataframe(m, use_container_width=True)
    
    else: # --- DIRECTORY ---
        st.header("👤 Employee Directory")
        t1, t2, t3 = st.tabs(["➕ Add/Edit", "📋 Import/Delete", "📊 Reports"])
        with t1:
            with st.form("emp_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    eid = st.text_input("Employee ID *"); name = st.text_input("Full Name *")
                    gen = st.selectbox("Gender *", ["Male", "Female", "Other"]); dob = st.date_input("DOB *")
                    doj = st.date_input("DOJ *"); dept = st.text_input("Department"); desig = st.text_input("Designation")
                    mgr = st.text_input("Reporting Manager"); fat = st.text_input("Father's Name"); cont = st.text_input("Contact *")
                with c2:
                    email = st.text_input("Email ID"); addr = st.text_area("Address"); emg = st.text_input("Emergency Person")
                    emg_no = st.text_input("Emergency Contact"); esic = st.text_input("ESIC"); pf = st.text_input("PF")
                    qual = st.text_input("Qualifications"); exp = st.text_input("Experience"); aad = st.text_input("Aadhaar")
                    pan = st.text_input("PAN"); stat = st.selectbox("Status", ["Active", "Inactive"]); mst = st.selectbox("Marital", ["Single", "Married"])
                    nat = st.text_input("Nationality"); bg = st.text_input("Blood Group")
                if st.form_submit_button("Save/Update Profile"):
                    st.session_state.profiles = [p for p in st.session_state.profiles if str(p.get("ID")) != str(eid)]
                    st.session_state.profiles.append({"ID": eid, "Name": name, "Dept": dept, "Manager": mgr, "DOJ": str(doj), "Contact": cont, "ESIC": esic, "PAN": pan, "Status": stat, "Blood Group": bg})
                    st.success("Record Saved!"); st.rerun()
        with t2:
            up = st.file_uploader("Upload CSV", type=['csv'])
            if up: st.session_state.profiles.extend(pd.read_csv(up).to_dict('records')); st.rerun()
            if st.session_state.profiles:
                df = pd.DataFrame(st.session_state.profiles)
                st.dataframe(df, use_container_width=True)
                del_id = st.selectbox("Delete ID:", df["ID"].unique())
                if st.button("Delete"): st.session_state.profiles = [p for p in st.session_state.profiles if str(p.get("ID")) != str(del_id)]; st.rerun()
        with t3:
            if st.session_state.profiles:
                df = pd.DataFrame(st.session_state.profiles)
                r = st.selectbox("Report:", ["General", "Work", "Statutory"])
                st.dataframe(df)
                st.download_button("📥 Export CSV", df.to_csv(index=False), f"{r}.csv")
