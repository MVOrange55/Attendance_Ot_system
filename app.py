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

# --- CSV STRUCTURE HELPER FUNCTIONS ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Employee Directory')
    return output.getvalue()

def to_html_for_pdf(df):
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 10px; }}
            th, td {{ border: 1px solid #dddddd; text-align: left; padding: 6px; white-space: nowrap; }}
            th {{ background-color: #f97316; color: white; font-weight: bold; }}
            h2 {{ color: #f97316; font-family: Arial, sans-serif; }}
        </style>
    </head>
    <body>
        <h2>Orange House - Employee Profile Directory</h2>
        <p>Generated on: {datetime.today().strftime('%Y-%m-%d %H:%M')}</p>
        <div style="overflow-x: auto;">
            {df.to_html(index=False)}
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
    u = st.text_input("User ID"); p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "admin" and p == "orange_hr": st.session_state.auth = True; st.rerun()
        else: st.error("Wrong Password!")
else:
    st.sidebar.title("🍊 Orange HR")
    
    # Do alag main sections: 1) Attendance Reports, 2) Employee Profile Directory
    app_mode = st.sidebar.radio("Navigation:", ["📊 Attendance Dashboard", "👤 Employee Profile Directory"])
    
    # --- SECTION A: ATTENDANCE DASHBOARD ---
    if app_mode == "📊 Attendance Dashboard":
        st.title("🍊 Attendance Management Dashboard")
        menu = st.sidebar.selectbox("Reports Menu:", [
            "📊 Attendance Muster", 
            "📈 Summary Report", 
            "💰 OT Slab Report", 
            "⚠️ Late/Early Log", 
            "❌ Miss Punch", 
            "🛠️ Correction"
        ])
        
        file = st.sidebar.file_uploader("Upload Excel", type=['xlsx'])
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
                        eid = st.text_input("Emp ID"); dt = st.number_input("Date", 1, 31)
                        cin = st.text_input("IN"); cout = st.text_input("OUT")
                        if st.form_submit_button("Update"):
                            st.session_state.corrs.append({'id': eid, 'date': int(dt), 'in': cin, 'out': cout}); st.rerun()
                with c2: st.write("History:", st.session_state.corrs)
        else:
            st.info("Sidebar se attendance Excel file upload karein.")

    # --- SECTION B: EMPLOYEE PROFILE DIRECTORY (COMPLETELY ISOLATED) ---
    else:
        st.title("👤 Advanced Employee Profile Directory")
        
        tab1, tab2 = st.tabs(["➕ Add Detailed Profile", "📋 View & Manage Directory"])
        
        with tab1:
            st.subheader("Enter Standard Employee Database Details")
            with st.form("extended_profile_form", clear_on_submit=True):
                
                # IMPORTANT CSV COLUMN STRUCTURE FIELDS
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
                    p_photo = st.file_uploader("Upload Photo", type=['jpg', 'jpeg', 'png'])
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
                    p_docs = st.file_uploader("Upload Documents (Resume/Certificates)", type=['pdf', 'docx', 'zip'], accept_multiple_files=True)

                submit_profile = st.form_submit_button("Save Complete Profile")
                if submit_profile:
                    if p_id.strip() == "" or p_name.strip() == "":
                        st.error("Employee ID aur Name mandatory hain!")
                    else:
                        exists = any(p['Employee ID'] == p_id.strip() for p in st.session_state.profiles)
                        if exists:
                            st.error(f"Employee ID {p_id} pehle se registered hai!")
                        else:
                            # Strict CSV Structured Schema Alignment
                            st.session_state.profiles.append({
                                'Employee ID': p_id.strip(),
                                'Full Name': p_name.strip(),
                                'Photo': p_photo.name if p_photo else 'No Photo Uploaded',
                                'Gender': p_gender,
                                'Date of Birth': p_dob.strftime('%Y-%m-%d'),
                                'Contact Number': p_contact.strip(),
                                'Email ID': p_email.strip(),
                                'Address': p_address.strip().replace('\n', ' '),
                                'Emergency Contact': p_emergency.strip(),
                                'Department': p_dept.strip(),
                                'Designation': p_desig.strip(),
                                'Reporting Manager': p_manager.strip(),
                                'Date of Joining': p_doj.strftime('%Y-%m-%d'),
                                'Employment Type': p_type,
                                'Work Location': p_location.strip(),
                                'Shift Details': p_shift.strip(),
                                'Salary Details': p_salary.strip(),
                                'Bank Account Details': p_bank.strip().replace('\n', ' '),
                                'PF/ESI Information': p_pf.strip().replace('\n', ' '),
                                'Attendance Record': "Linked",
                                'Leave Balance': p_leave.strip(),
                                'Performance Details': p_perf.strip().replace('\n', ' '),
                                'Skills & Qualifications': p_skills.strip().replace('\n', ' '),
                                'Experience': p_exp.strip(),
                                'Documents Upload': 'Uploaded' if p_docs else 'No Documents',
                                'Status': p_status
                            })
                            st.success(f"{p_name} ka profile detailed database mein save ho gaya!")
                            st.rerun()

        with tab2:
            st.subheader("Registered Employee Directory")
            if len(st.session_state.profiles) == 0:
                st.info("Abhi koi profiles saved nahi hain.")
            else:
                # Direct conversion to clean structured DataFrame
                display_df = pd.DataFrame(st.session_state.profiles)
                
                # --- FILTERS SYSTEM ---
                st.markdown("#### 🔍 Filter Employees")
                f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                
                with f_col1:
                    search_id = st.text_input("Filter by ID:")
                with f_col2:
                    search_name = st.text_input("Filter by Name:")
                with f_col3:
                    all_depts = ["All"] + list(display_df['Department'].unique())
                    search_dept = st.selectbox("Filter by Department:", all_depts)
                with f_col4:
                    search_status = st.selectbox("Filter by Status:", ["All", "Active", "Inactive"])
                
                # Dynamic filtering
                filtered_df = display_df.copy()
                if search_id:
                    filtered_df = filtered_df[filtered_df['Employee ID'].astype(str).str.contains(search_id, case=False)]
                if search_name:
                    filtered_df = filtered_df[filtered_df['Full Name'].str.contains(search_name, case=False)]
                if search_dept != "All":
                    filtered_df = filtered_df[filtered_df['Department'] == search_dept]
                if search_status != "All":
                    filtered_df = filtered_df[filtered_df['Status'] == search_status]
                
                # Show CSV Structure DataFrame
                st.dataframe(filtered_df, use_container_width=True)
                
                # --- EXPORT DOWNLOAD SYSTEM ---
                st.write("")
                st.markdown("#### 📥 Export / Download Filtered Directory")
                down_col1, down_col2, down_col3, _ = st.columns([1, 1, 1, 3])
                
                with down_col1:
                    # Pure CSV Data Download
                    csv_buffer = io.StringIO()
                    filtered_df.to_csv(csv_buffer, index=False)
                    st.download_button(
                        label="Download CSV 📄",
                        data=csv_buffer.getvalue(),
                        file_name=f"Employee_Database_{datetime.today().strftime('%Y-%m-%d')}.csv",
                        mime="text/csv"
                    )
                
                with down_col2:
                    excel_data = to_excel(filtered_df)
                    st.download_button(
                        label="Download Excel 📈",
                        data=excel_data,
                        file_name=f"Employee_Directory_{datetime.today().strftime('%Y-%m-%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                with down_col3:
                    html_data = to_html_for_pdf(filtered_df)
                    st.download_button(
                        label="Download PDF Print 📄",
                        data=html_data,
                        file_name=f"Employee_Directory_{datetime.today().strftime('%Y-%m-%d')}.html",
                        mime="text/html"
                    )
                
                # --- DELETE COMPONENT ---
                st.write("---")
                st.subheader("❌ Delete Employee Profile")
                
                delete_options = [f"{p['Employee ID']} - {p['Full Name']}" for p in st.session_state.profiles]
                selected_to_delete = st.selectbox("Kisko directory se delete karna hai select karein:", delete_options)
                
                if st.button("Delete Selected Profile", type="primary"):
                    target_id = selected_to_delete.split(" - ")[0]
                    st.session_state.profiles = [p for p in st.session_state.profiles if p['Employee ID'] != target_id]
                    st.success(f"Profile {selected_to_delete} deleted successfully!")
                    st.rerun()
