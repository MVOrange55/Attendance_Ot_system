import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- 1. PAGE CONFIG & SESSION ---
st.set_page_config(page_title="Orange House HR Portal", layout="wide", page_icon="🍊")

if 'auth' not in st.session_state: st.session_state.auth = False
if 'corrs' not in st.session_state: st.session_state.corrs = []
if 'profiles' not in st.session_state: st.session_state.profiles = []

# --- 2. ENGINE FUNCTIONS (ORIGINAL) ---
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
        sl_used, p_c, a_c, ab_c, wo_c, h_c, tot_ot = False, 0, 0, 0, 0, 0, 0.0
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
                        t_start = time(14, 0); d_start = datetime.combine(datetime.today(), t_start)
                        work_hrs = (d2 - d_start).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 4.0) if work_hrs > 4.0 else 0.0
                        status = "AB/"
                    else:
                        t_start_calc = max(t_in, time(9, 30)); d_start_calc = datetime.combine(datetime.today(), t_start_calc)
                        work_hrs = (d2 - d_start_calc).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 8.5) if work_hrs > 8.5 else 0.0
                        if actual_dur < 4.0: status = "AB/"
                        elif t_in > time(10, 16) or t_out < time(16, 0):
                            if not sl_used and actual_dur >= 6.0: status, sl_used = "P*", True
                            else: status = "AB/"
                        else: status = "P"
                    if status in ["P", "P*"]: p_c += 1
                    elif status == "AB/": ab_c += 0.5
            row_m[str(d_i)], row_o[str(d_i)] = status, day_ot
            tot_ot += day_ot
        res_m.append(row_m)
        res_s.append({"Emp ID": clean_id, "Name": ename, "Present (P)": p_c, "Absent (A)": a_c, "Half Day (AB/)": ab_c, "Holiday (H)": h_c, "Weekly Off (WO)": wo_c, "Total OT Hours": tot_ot, "Payable Days": (p_c + ab_c + wo_c + h_c)})
        row_o["Total OT Hours"] = tot_ot
        res_o.append(row_o)
        res_ex.append({"Emp ID": clean_id, "Name": ename, "Late Days": len(late_log), "Early Out Days": len(early_log)})
    return pd.DataFrame(res_m), pd.DataFrame(res_s), pd.DataFrame(res_o), pd.DataFrame(res_ex), pd.DataFrame(res_mi)

# --- 3. UI ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color: #f97316;'>Orange House HR Portal</h1>", unsafe_allow_html=True)
    u = st.text_input("User ID"); p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "admin" and p == "orange_hr": st.session_state.auth = True; st.rerun()
else:
    nav = st.sidebar.radio("Navigation:", ["📊 Attendance Portal", "👤 Employee Directory"])
    
    if nav == "📊 Attendance Portal":
        # ... [Attendance UI remains same] ...
        file = st.sidebar.file_uploader("Upload Excel", type=['xlsx'])
        hols = st.sidebar.multiselect("Select Holidays:", range(1, 32))
        menu = st.sidebar.selectbox("Reports Menu:", ["📊 Attendance Muster", "📈 Summary Report", "💰 OT Slab Report", "⚠️ Late/Early Log", "❌ Miss Punch", "🛠️ Correction"])
        if file:
            df_raw = pd.read_excel(file)
            m, s, o, ex, mi = run_hr_engine(df_raw, hols, st.session_state.corrs)
            if menu == "📊 Attendance Muster": st.dataframe(m, use_container_width=True)
            elif menu == "📈 Summary Report": st.dataframe(s, use_container_width=True)
            elif menu == "💰 OT Slab Report": st.dataframe(o, use_container_width=True)
            elif menu == "⚠️ Late/Early Log": st.dataframe(ex, use_container_width=True)
            elif menu == "❌ Miss Punch": st.dataframe(mi, use_container_width=True)
            elif menu == "🛠️ Correction":
                with st.form("corr"):
                    eid = st.text_input("Emp ID"); dt = st.number_input("Date", 1, 31)
                    cin = st.text_input("IN"); cout = st.text_input("OUT")
                    if st.form_submit_button("Update"):
                        st.session_state.corrs.append({'id': eid, 'date': int(dt), 'in': cin, 'out': cout}); st.rerun()

    else: # --- EMPLOYEE DIRECTORY ---
        st.subheader("👤 Employee Directory")
        t1, t2 = st.tabs(["➕ Add/Update Profile", "📋 Directory / Filter / Delete"])
        with t1:
            with st.form("emp_form", clear_on_submit=True):
                eid = st.text_input("Employee ID *")
                name = st.text_input("Full Name *")
                dob = st.date_input("Date of Birth *")
               doj = st.date_input("Date of Joining *")
              gen = st.text_input("Gender *")
                dept = st.text_input("Department")
                desig = st.text_input("Designation")
                  rep manager = st.text_input("Reporting Manager")
                father name = st.text_input("Father's Name")
                cont = st.text_input("Contact Number")
                stat = st.selectbox("Status", ["Active", "Inactive"])
                if st.form_submit_button("Save/Update Profile"):
                    if eid and name:
                        # Puraane record ko filter karke naya save karna = UPDATE
                        st.session_state.profiles = [p for p in st.session_state.profiles if str(p.get("ID")) != str(eid)]
                        st.session_state.profiles.append({"ID": str(eid), "Name": name, "Dept": dept, "Contact": cont, "Status": stat})
                        st.success("Profile saved/updated successfully!"); st.rerun()
                    else: st.error("ID and Name are mandatory!")
        with t2:
            if st.session_state.profiles:
                df = pd.DataFrame(st.session_state.profiles)
                # FILTERING
                if "Dept" in df.columns:
                    f_dept = st.multiselect("Filter by Department:", df["Dept"].unique())
                    if f_dept: df = df[df["Dept"].isin(f_dept)]
                st.dataframe(df, use_container_width=True)
                # DELETION
                del_id = st.selectbox("Select ID to Delete:", [str(x) for x in df["ID"].unique()])
                if st.button("Delete Selected Employee"):
                    st.session_state.profiles = [p for p in st.session_state.profiles if str(p.get("ID")) != str(del_id)]
                    st.rerun()
                st.download_button("📥 Export CSV", df.to_csv(index=False), "Directory.csv")
            else: st.info("No records found.")
