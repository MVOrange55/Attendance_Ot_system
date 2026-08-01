import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Orange House HR Portal", layout="wide", page_icon="🍊")

# --- 2. SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'corrs' not in st.session_state: st.session_state.corrs = []
if 'profiles' not in st.session_state: st.session_state.profiles = []

# --- 3. HELPER FUNCTION ---
def get_pdf_download_link(df):
    html = df.to_html(index=False)
    return html

# --- 4. ENGINE FUNCTIONS ---
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
    sundays = [5, 12, 19, 26] 
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
                miss_type = "OUT Punch Missing" if t_in else "IN Punch Missing"
                res_mi.append({"ID": clean_id, "Name": ename, "Date": d_i, "Status": "Miss Punch", "Detail": miss_type})
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
                        work_hrs = (d2 - datetime.combine(datetime.today(), time(14, 0))).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 4.0) if work_hrs > 4.0 else 0.0
                        status = "AB/"
                    else:
                        work_hrs = (d2 - datetime.combine(datetime.today(), max(t_in, time(9, 30)))).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 8.5) if work_hrs > 8.5 else 0.0
                        if actual_dur < 4.0: status = "AB/"
                        elif t_in > time(10, 16) or t_out < time(16, 0):
                            if not sl_used and actual_dur >= 6.0: status, sl_used = "P*", True
                            else: status = "AB/"
                        else: status = "P"
                        if t_in is not None and t_in > time(9, 35):
                            late_log.append(f"{d_i}({t_in.strftime('%H:%M')})")
                        if work_hrs < 8.5:
                            out_str = t_out.strftime('%H:%M') if t_out is not None else "N/A"
                            early_log.append(f"{d_i}({out_str})")
                    if status in ["P", "P*"]: p_c += 1
                    elif status == "AB/": ab_c += 0.5
            row_m[str(d_i)], row_o[str(d_i)] = status, day_ot
            tot_ot += day_ot
        res_m.append(row_m)
        res_s.append({"Emp ID": clean_id, "Name": ename, "P": p_c, "A": a_c, "AB/": ab_c, "H": h_c, "WO": wo_c, "OT": tot_ot})
        row_o["Total OT"] = tot_ot
        res_o.append(row_o)
        res_ex.append({
            "Emp ID": clean_id, "Name": ename, "Late Days": len(late_log), "Late In Detail": " | ".join(late_log),
            "Early Out Days": len(early_log), "Early Out Detail ( < 8.5h )": " | ".join(early_log)
        })
    return pd.DataFrame(res_m), pd.DataFrame(res_s), pd.DataFrame(res_o), pd.DataFrame(res_ex), pd.DataFrame(res_mi)

# --- 5. UI ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color: #f97316;'>Orange House HR Portal</h1>", unsafe_allow_html=True)
    u = st.text_input("User ID"); p = st.text_input("Password", type="password")
    if st.button("Login") and u == "admin" and p == "Hr": st.session_state.auth = True; st.rerun()
else:
                
    nav = st.sidebar.radio("Navigation:", ["📊 Attendance Engine", "👤 Employee Directory"])
    
    if nav == "📊 Attendance Engine":
        file = st.sidebar.file_uploader("Upload Attendance Excel", type=['xlsx'])
        hols = st.sidebar.multiselect("Select Holidays:", range(1, 32))
        menu = st.sidebar.selectbox("Reports:", [" 📊 Attendance Muster", "📈 Summary Report", "💰 OT Slab Report", "⚠️ Late/Early Log", "❌ Miss Punch", "🛠️ Correction"])
        if file:
            m, s, o, ex, mi = run_hr_engine(pd.read_excel(file), hols, st.session_state.corrs)
            if m is not None:
                if menu == " 📊 Attendance Muster": st.dataframe(m)
                elif menu == "📈 Summary Report": st.dataframe(s)
                elif menu == "💰 OT Slab Report": st.dataframe(o)
                elif menu == "⚠️ Late/Early Log": st.dataframe(ex)
                elif menu == "❌ Miss Punch": st.dataframe(mi)
        if menu == "🛠️ Correction":
            eid = st.text_input("ID"); dt = st.number_input("Date", 1, 31); cin = st.text_input("IN"); cout = st.text_input("OUT")
            if st.button("Add Correction"): st.session_state.corrs.append({'id': eid, 'date': int(dt), 'in': cin, 'out': cout}); st.rerun()
    
    else:
        st.subheader("Employee Profile Management")
        t1, t2, t3, t4, t5, t6 = st.tabs(["➕ Add Manual", "📄 Important Uploads", "🗑️ Delete Record", "🔍 Filter/Edit", "📥 Download", "ℹ️ Help"])
        with t1:
            with st.form("manual_emp", clear_on_submit=True):
                c1, c2 = st.columns(2)
                data = {"ID": c1.text_input("ID"), "Name": c1.text_input("Name"), "Gender": c1.selectbox("Gender", ["Male", "Female"]), "DOB": str(c1.date_input("DOB")), "DOJ": str(c1.date_input("DOJ")), "Dept": c2.text_input("Dept"), "Contact": c1.text_input("Contact (Max 10)", max_chars=10), "PF": c2.text_input("PF (Max 12)", max_chars=12), "Aadhaar": c1.text_input("Aadhaar (Max 12)", max_chars=12), "Status": c2.selectbox("Status", ["Active", "Inactive"]), "Designation": c2.text_input("Designation"), "Manager": c2.text_input("Manager"), "FatherName": c1.text_input("FatherName"), "Email": c2.text_input("Email"), "Address": c2.text_area("Address"), "EmergencyName": c1.text_input("EmergencyName"), "EmergencyContact": c1.text_input("EmergencyContact"), "ESIC": c2.text_input("ESIC"), "Qualification": c1.text_input("Qualification"), "Experience": c2.text_input("Experience"), "PAN": c2.text_input("PAN"), "MaritalStatus": c1.selectbox("MaritalStatus", ["Single", "Married"]), "Nationality": c2.text_input("Nationality"), "BloodGroup": c1.text_input("BloodGroup")}
                photo = st.file_uploader("Upload Employee Photo", type=['jpg', 'png'])
                if st.form_submit_button("Save Record"):
                    if photo: data["Photo"] = photo.name
                    st.session_state.profiles.append(data); st.success("Record Saved Successfully!")
        with t2:
            up = st.file_uploader("Upload CSV", type=['csv'])
            if up: 
                try:
                    df_up = pd.read_csv(up, encoding='latin1')
                    df_up = df_up.dropna(how='all')
                    df_up = df_up.fillna('')
                    st.write(f"Total Rows Found: {len(df_up)}")
                    st.dataframe(df_up) 
                    if st.button("Confirm & Upload"): 
                        st.session_state.profiles.extend(df_up.to_dict('records'))
                        st.success("Data Imported Successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error reading file: {e}")
        with t3:
            st.subheader("Batch Delete Employees")
            if st.session_state.profiles:
                options = {f"{p.get('ID')} - {p.get('Name')}": p.get('ID') for p in st.session_state.profiles}
                del_ids = st.multiselect("Select Employees to Delete:", options=list(options.keys()))
                if st.button("Confirm Delete Selected", type="primary"):
                    selected_ids = [options[k] for k in del_ids]
                    st.session_state.profiles = [p for p in st.session_state.profiles if p.get('ID') not in selected_ids]
                    st.success("Selected records deleted!")
                    st.rerun()
        with t4:
            st.subheader("Search & Filter Employees")
            if st.session_state.profiles:
                df = pd.DataFrame(st.session_state.profiles)
                c1, c2, c3 = st.columns(3)
                dept_list = df['Dept'].unique().tolist() if 'Dept' in df.columns else []
                desig_list = df['Designation'].unique().tolist() if 'Designation' in df.columns else []
                
                dept_filter = c1.multiselect("Filter by Dept:", dept_list)
                desig_filter = c2.multiselect("Filter by Designation:", desig_list)
                search_term = c3.text_input("🔍 Quick Find:", placeholder="Type name or ID...")

                filt = df.copy()
                if dept_filter: filt = filt[filt['Dept'].isin(dept_filter)]
                if desig_filter: filt = filt[filt['Designation'].isin(desig_filter)]
                if search_term:
                    filt = filt[filt['Name'].astype(str).str.contains(search_term, case=False) | 
                                filt['ID'].astype(str).str.contains(search_term)]

                # Dynamic Sr. No. logic
                filt.insert(0, 'Sr. No.', range(1, len(filt) + 1))
                edited_df = st.data_editor(filt, use_container_width=True, num_rows="dynamic")
                
                if st.button("💾 Save All Changes", use_container_width=True):
                    if 'Sr. No.' in edited_df.columns: edited_df = edited_df.drop(columns=['Sr. No.'])
                    st.session_state.profiles = edited_df.to_dict('records')
                    st.success("Changes saved!")
                    st.rerun()
            else:
                st.info("No employee profiles found.")
        with t5:
            if st.session_state.profiles:
                df = pd.DataFrame(st.session_state.profiles)
                st.download_button("📥 CSV Export", df.to_csv(index=False), "Report.csv")
                st.markdown(f'<a href="data:text/html;charset=utf-8,{get_pdf_download_link(df)}" download="Report.html">📥 Download HTML/PDF View</a>', unsafe_allow_html=True)
        with t6:
            st.warning("Ensure CSV headers match the template.")
