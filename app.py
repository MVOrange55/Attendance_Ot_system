import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Orange House HR Portal", layout="wide", page_icon="🍊")

# --- 2. ENGINE FUNCTIONS (ORIGINAL - NO CHANGES) ---
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
    sundays = [3, 10, 17, 24 ] 
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
                        d_start = datetime.combine(datetime.today(), t_start)
                        work_hrs = (d2 - d_start).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 4.0) if work_hrs > 4.0 else 0.0
                        status = "AB/"
                        if work_hrs < 4.0:
                            early_log.append(f"{t_out.strftime('%H:%M')} (Dt:{d_i})")
                    else:
                        t_start_calc = max(t_in, time(9, 30))
                        d_start_calc = datetime.combine(datetime.today(), t_start_calc)
                        work_hrs = (d2 - d_start_calc).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 8.5) if work_hrs > 8.5 else 0.0
                        
                        if actual_dur < 4.0: status = "AB/"
                        elif t_in > time(10, 16) or t_out < time(16, 0):
                            if not sl_used and actual_dur >= 6.0: status, sl_used = "P*", True
                            else: status = "AB/"
                        else: status = "P"

                        if t_in > time(9, 35): 
                            late_log.append(f"{t_in.strftime('%H:%M')} (Dt:{d_i})")
                        
                        if work_hrs < 8.5:
                            early_log.append(f"{t_out.strftime('%H:%M')} (Dt:{d_i})")

                    if status in ["P", "P*"]: p_c += 1
                    elif status == "AB/": ab_c += 0.5

            row_m[str(d_i)], row_o[str(d_i)] = status, day_ot
            tot_ot += day_ot

        res_m.append(row_m)
        res_s.append({
            "Emp ID": clean_id, "Name": ename, 
            "Present (P)": p_c, "Absent (A)": a_c, "Half Day (AB/)": ab_c, 
            "Holiday (H)": h_c, "Weekly Off (WO)": wo_c, 
            "Total OT Hours": tot_ot, "Payable Days": (p_c + ab_c + wo_c + h_c)
        })
        row_o["Total OT Hours"] = tot_ot
        res_o.append(row_o)
        res_ex.append({
            "Emp ID": clean_id, "Name": ename, 
            "Late Days": len(late_log), "Late In Detail": " | ".join(late_log),
            "Early Out Days": len(early_log), "Early Out Detail ( < 8.5h )": " | ".join(early_log)
        })
    
    return pd.DataFrame(res_m), pd.DataFrame(res_s), pd.DataFrame(res_o), pd.DataFrame(res_ex), pd.DataFrame(res_mi)

# --- PROFILE EXPORT HELPERS ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Employee Directory')
    return output.getvalue()

def to_html_for_pdf(df):
    time_str = datetime.today().strftime('%Y-%m-%d %H:%M')
    html_table = df.to_html(index=False)
    html = """
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 10px; }
            th, td { border: 1px solid #dddddd; text-align: left; padding: 6px; white-space: nowrap; }
            th { background-color: #f97316; color: white; font-weight: bold; }
            h2 { color: #f97316; font-family: Arial, sans-serif; }
        </style>
    </head>
    <body>
        <h2>Orange House - Employee Profile Directory</h2>
        <p>Generated on: """ + time_str + """</p>
        <div style="overflow-x: auto;">
            """ + html_table + """
        </div>
    </body>
    </html>
    """
    return html

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
        if u == "admin" and p == "orange_hr": 
            st.session_state.auth = True
            st.rerun()
        else: 
            st.error("Wrong Password!")
else:
    st.sidebar.title("🍊 Orange HR")
    app_mode = st.sidebar.radio("Navigation:", ["📊 Attendance Dashboard", "👤 Employee Profile Directory"])
    
    # --- SECTION A: ATTENDANCE DASHBOARD ---
    if app_mode == "📊 Attendance Dashboard":
        st.title("🍊 Attendance Management Dashboard")
        menu = st.sidebar.selectbox("Reports Menu:", ["📊 Attendance Muster", "📈 Summary Report", "💰 OT Slab Report", "⚠️ Late/Early Log", "❌ Miss Punch", "🛠️ Correction"])
        
        file = st.sidebar.file_uploader("Upload Excel", type=['xlsx'], key="att_up")
        hols = st.sidebar.multiselect("Select Holidays:", range(1, 32))

        if file:
            df_raw = pd.read_excel(file)
            m, s, o, ex, mi = run_hr_engine(df_raw, hols, st.session_state.corrs)
            st.subheader(f"{menu}")
            
            if menu == "📊 Attendance Muster": st.dataframe(m, use_container_width=True)
            elif menu == "📈 Summary Report": st.dataframe(s, use_container_width=True)
            elif menu == "💰 OT Slab Report": st.dataframe(o, use_container_width=True)
            elif menu == "⚠️ Late/Early Log": st.dataframe(ex, use_container_width=True)
            elif menu == "❌ Miss Punch": st.dataframe(mi, use_container_width=True)
            elif menu == "🛠️ Correction":
                c1, c2 = st.columns(2)
                with c1:
                    with st.form("corr"):
                        eid = st.text_input("Emp ID")
                        dt = st.number_input("Date", 1, 31)
                        cin = st.text_input("IN")
                        cout = st.text_input("OUT")
                        if st.form_submit_button("Update"):
                            st.session_state.corrs.append({'id': eid, 'date': int(dt), 'in': cin, 'out': cout})
                            st.rerun()
                with c2: 
                    st.write("History:", st.session_state.corrs)
        else:
            st.info("Sidebar se attendance Excel file upload karein.")

    # --- SECTION B: EMPLOYEE PROFILE DIRECTORY ---
    else:
        st.title("👤 Advanced Employee Profile Directory")
        
        tab1, tab2, tab3 = st.tabs(["➕ Add Profile (Manual)", "📤 Import / Upload CSV File", "📋 View & Manage Directory"])
        
        # --- TAB 1: MANUAL ENTRY ---
        with tab1:
            st.subheader("Manual Employee Data Entry Form")
            with st.form("extended_profile_form", clear_on_submit=True):
                st.markdown("### 📝 Personal Details")
                col1, col2, col3 = st.columns(3)
                with col1:
                    p_id = st.text_input("Employee ID *")
                    p_name = st.text_input("Full Name *")
                    p_dob = st.date_input("Date of Birth", datetime(1995, 1, 1))
                with col2:
                    p_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                    p_contact = st.text_input("Contact Number")
                    p_email = st.text_input("Email ID")
                with col3:
                    p_photo = st.file_uploader("Upload Photo", type=['jpg', 'jpeg', 'png'], key="man_pic")
                    p_emergency = st.text_input("Emergency Contact")
                    p_address = st.text_area("Address", height=68)

                st.markdown("---")
                st.markdown("### 🏢 Employment & Work Details")
                col4, col5, col6 = st.columns(3)
                with col4:
                    p_dept = st.text_input("Department")
                    p_desig = st.text_input("Designation")
                    p_manager = st.text_input("Reporting Manager")
                with col5:
                    p_doj = st.date_input("Date of Joining", datetime.today())
                    p_type = st.selectbox("Employment Type", ["Full-Time", "Part-Time", "Contract", "Intern"])
                    p_status = st.selectbox("Status", ["Active", "Inactive"])
                with col6:
                    p_location = st.text_input("Work Location")
                    p_shift = st.text_input("Shift Details")
                    p_exp = st.text_input("Total Experience (Years)")

                st.markdown("---")
                st.markdown("### 💰 Financial & Statutory Details")
                col7, col8 = st.columns(2)
                with col7:
                    p_salary = st.text_input("Salary Details (CTC/Gross)")
                    p_bank = st.text_area("Bank Account Details (Acc No, IFSC, Bank Name)", height=68)
                with col8:
                    p_pf = st.text_area("PF/ESI Information", height=68)
                    p_aadhaar = st.text_input("Aadhaar Card Number", placeholder="XXXX-XXXX-XXXX")
                    p_pan = st.text_input("PAN Card Number")

                st.markdown("---")
                st.markdown("### 📊 HR Metrics & Documents")
                col9, col10 = st.columns(2)
                with col9:
                    p_skills = st.text_area("Skills & Qualifications")
                    p_perf = st.text_area("Performance Details / Remarks")
                with col10:
                    p_leave = st.text_input("Initial Leave Balance")
                    p_docs = st.file_uploader("Upload Documents", type=['pdf', 'docx', 'zip'], accept_multiple_files=True, key="man_doc")

                submit_profile = st.form_submit_button("Save Complete Profile")
                if submit_profile:
                    if p_id.strip() == "" or p_name.strip() == "":
                        st.error("Employee ID aur Name mandatory hain!")
                    else:
                        exists = any(str(p['Employee ID']) == p_id.strip() for p in st.session_state.profiles)
                        if exists:
                            st.error(f"Employee ID {p_id} pehle se registered hai!")
                        else:
                            st.session_state.profiles.append({
                                'Employee ID': p_id.strip(), 'Full Name': p_name.strip(), 'Photo': p_photo.name if p_photo else 'No Photo',
                                'Gender': p_gender, 'Date of Birth': p_dob.strftime('%Y-%m-%d'), 'Contact Number': p_contact.strip(),
                                'Email ID': p_email.strip(), 'Address': p_address.strip().replace('\n', ' '), 'Emergency Contact': p_emergency.strip(),
                                'Department': p_dept.strip(), 'Designation': p_desig.strip(), 'Reporting Manager': p_manager.strip(),
                                'Date of Joining': p_doj.strftime('%Y-%m-%d'), 'Employment Type': p_type, 'Work Location': p_location.strip(),
                                'Shift Details': p_shift.strip(), 'Salary Details': p_salary.strip(), 'Bank Account Details': p_bank.strip().replace('\n', ' '),
                                'PF/ESI Information': p_pf.strip().replace('\n', ' '), 'Attendance Record': "Linked", 'Leave Balance': p_leave.strip(),
                                'Performance Details': p_perf.strip().replace('\n', ' '), 'Skills & Qualifications': p_skills.strip().replace('\n', ' '),
                                'Experience': p_exp.strip(), 'Documents Upload': 'Uploaded' if p_docs else 'No Documents', 'Status': p_status
                            })
                            st.success(f"{p_name} ka profile save ho gaya!")
                            st.rerun()

        # --- TAB 2: BULK CSV UPLOAD / IMPORT ---
        with tab2:
            st.subheader("Bulk Import Employee Master File")
            st.markdown("""
            **⚠️ Rule:** Aapki CSV/Excel file mein exact wahi headers hone chahiye jo system match karega. 
            Aap testing ke liye niche diye gaye button se **Sample Format Template** download kar sakte hain.
            """)
            
            template_cols = ['Employee ID', 'Full Name', 'Photo', 'Gender', 'Date of Birth', 'Contact Number', 'Email ID', 'Address', 'Emergency Contact', 'Department', 'Designation', 'Reporting Manager', 'Date of Joining', 'Employment Type', 'Work Location', 'Shift Details', 'Salary Details', 'Bank Account Details', 'PF/ESI Information', 'Attendance Record', 'Leave Balance', 'Performance Details', 'Skills & Qualifications', 'Experience', 'Documents Upload', 'Status']
            template_df = pd.DataFrame(columns=template_cols)
            st.download_button(label="📥 Download Sample CSV Template", data=template_df.to_csv(index=False), file_name="Employee_Import_Template.csv", mime="text/csv")
            
            st.write("---")
            uploaded_master = st.file_uploader("Apni HR CSV ya Excel File Select Karein:", type=['csv', 'xlsx'], key="bulk_profile_uploader")
            
            if uploaded_master:
                try:
                    if uploaded_master.name.endswith('.csv'):
                        uploaded_df = pd.read_csv(uploaded_master)
                    else:
                        uploaded_df = pd.read_excel(uploaded_master)
                    
                    st.write("File Preview (Top 5 rows):", uploaded_df.head())
                    
                    if st.button("Confirm & Import All Data", type="primary"):
                        success_count = 0
                        duplicate_count = 0
                        
                        for _, row in uploaded_df.iterrows():
                            raw_id = row.get('Employee ID', '')
                            if pd.isna(raw_id) or str(raw_id).strip() == "":
                                continue
                            
                            emp_id = str(raw_id).strip().split('.')[0]
                            
                            exists = any(str(p['Employee ID']) == emp_id for p in st.session_state.profiles)
                            if exists:
                                duplicate_count += 1
                                continue
                            
                            def clean_val(val, default=""):
                                if pd.isna(val): return default
                                return str(val).strip()

                            st.session_state.profiles.append({
                                'Employee ID': emp_id,
                                'Full Name': clean_val(row.get('Full Name'), 'Unnamed'),
                                'Photo': clean_val(row.get('Photo'), 'No Photo'),
                                'Gender': clean_val(row.get('Gender'), 'Male'),
                                'Date of Birth': clean_val(row.get('Date of Birth')),
                                'Contact Number': clean_val(row.get('Contact Number')),
                                'Email ID': clean_val(row.get('Email ID')),
                                'Address': clean_val(row.get('Address')).replace('\n', ' '),
                                'Emergency Contact': clean_val(row.get('Emergency Contact')),
                                'Department': clean_val(row.get('Department'), 'General'),
                                'Designation': clean_val(row.get('Designation'), 'Staff'),
                                'Reporting Manager': clean_val(row.get('Reporting Manager')),
                                'Date of Joining': clean_val(row.get('Date of Joining')),
                                'Employment Type': clean_val(row.get('Employment Type'), 'Full-Time'),
                                'Work Location': clean_val(row.get('Work Location')),
                                'Shift Details': clean_val(row.get('Shift Details')),
                                'Salary Details': clean_val(row.get('Salary Details')),
                                'Bank Account Details': clean_val(row.get('Bank Account Details')).replace('\n', ' '),
                                'PF/ESI Information': clean_val(row.get('PF/ESI Information')).replace('\n', ' '),
                                'Attendance Record': clean_val(row.get('Attendance Record'), 'Linked'),
                                'Leave Balance': clean_val(row.get('Leave Balance')),
                                'Performance Details': clean_val(row.get('Performance Details')).replace('\n', ' '),
                                'Skills & Qualifications': clean_val(row.get('Skills & Qualifications')).replace('\n', ' '),
                                'Experience': clean_va
