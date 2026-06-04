# --- 4. UI ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color: #f97316;'>Orange House HR Portal</h1>", unsafe_allow_html=True)
    u = st.text_input("User ID"); p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "admin" and p == "orange_hr": st.session_state.auth = True; st.rerun()
        else: st.error("Wrong Password!")
else:
    # --- NAVIGATION ---
    app_mode = st.sidebar.radio("Navigation:", ["📊 Attendance Dashboard", "👤 Employee Directory"])
    
    if app_mode == "📊 Attendance Dashboard":
        # ... (Yahan aapka purana Attendance wala code rahega) ...
        pass 

    elif app_mode == "👤 Employee Directory":
        if 'profiles' not in st.session_state: st.session_state.profiles = []
        
        tab1, tab2, tab3 = st.tabs(["➕ Add Profile", "📋 Directory View", "⚙️ Manage"])
        
        with tab1:
            st.subheader("Employee Enrollment")
            with st.form("emp_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    eid = st.text_input("Employee ID *")
                    name = st.text_input("Full Name *")
                    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                    dob = st.date_input("Date of Birth")
                    doj = st.date_input("Date of Joining")
                    dept = st.text_input("Department")
                    desig = st.text_input("Designation")
                    mgr = st.text_input("Reporting Manager")
                    father = st.text_input("Father's Name")
                with c2:
                    ph = st.text_input("Contact Number *")
                    email = st.text_input("Email ID")
                    addr = st.text_area("Address")
                    emerg_name = st.text_input("Emergency Contact Person")
                    emerg_no = st.text_input("Emergency Contact")
                    esic = st.text_input("ESIC")
                    pf = st.text_input("PF")
                    aadhaar = st.text_input("Aadhaar")
                    pan = st.text_input("PAN")
                
                c3, c4 = st.columns(2)
                with c3:
                    qual = st.text_input("Qualifications")
                    exp = st.text_input("Experience")
                    status = st.selectbox("Status", ["Active", "Inactive"])
                    marit = st.selectbox("Marital Status", ["Single", "Married"])
                with c4:
                    nat = st.text_input("Nationality")
                    bg = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
                    photo = st.file_uploader("Upload Photo", type=['jpg', 'png'])
                    resume = st.file_uploader("Upload Resume", type=['pdf'])

                if st.form_submit_button("Save Employee Profile"):
                    if eid and name and ph:
                        st.session_state.profiles.append({
                            "ID": eid, "Name": name, "Gender": gender, "Contact": ph, 
                            "Dept": dept, "Status": status, "DOJ": doj
                        })
                        st.success("Profile Saved!")
                    else: st.error("Mandatory fields (ID, Name, Contact) are required.")

        with tab3:
            st.subheader("Filters")
            df = pd.DataFrame(st.session_state.profiles) if st.session_state.profiles else pd.DataFrame()
            if not df.empty:
                f_dept = st.multiselect("Filter by Dept", df["Dept"].unique())
                filtered_df = df[df["Dept"].isin(f_dept)] if f_dept else df
                st.dataframe(filtered_df)
                
                # Download Buttons
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    csv = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Excel", csv, "directory.csv", "text/csv")
                with col_d2:
                    st.download_button("Download PDF", data=filtered_df.to_html(), file_name="directory.html")
            else: st.info("No profiles found.")
