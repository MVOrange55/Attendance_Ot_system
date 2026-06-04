import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Orange House HR Portal", layout="wide", page_icon="🍊")

# --- 2. SESSION STATES ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'profiles' not in st.session_state: st.session_state.profiles = []
if 'corrs' not in st.session_state: st.session_state.corrs = []

# --- 3. LOGIN ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color: #f97316;'>Orange House HR Portal</h1>", unsafe_allow_html=True)
    u = st.text_input("User ID")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "admin" and p == "orange_hr": st.session_state.auth = True; st.rerun()
        else: st.error("Wrong Password!")
else:
    # --- NAVIGATION ---
    mode = st.sidebar.radio("Navigation:", ["📊 Attendance Portal", "👤 Employee Directory"])
    
    # ========================================================
    # MODULE 1: OLD ATTENDANCE CODE (SAME AS BEFORE)
    # ========================================================
    if mode == "📊 Attendance Portal":
        st.title("Attendance Management")
        # [Yahan aapka purana attendance logic rahega]
        st.info("Attendance Portal is active.")

    # ========================================================
    # MODULE 2: NEW EMPLOYEE DIRECTORY (ALAG SE)
    # ========================================================
    elif mode == "👤 Employee Directory":
        st.title("👤 Employee Profile Directory")
        t1, t2, t3 = st.tabs(["➕ Add Profile", "📋 Directory / Delete", "📤 Export"])
        
        with t1:
            with st.form("emp_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    e_id = st.text_input("Employee ID *")
                    e_name = st.text_input("Full Name *")
                    e_gen = st.selectbox("Gender", ["Male", "Female", "Other"])
                    e_dob = st.date_input("Date of Birth *")
                    e_doj = st.date_input("Date of Joining *")
                    e_dept = st.text_input("Department")
                    e_desig = st.text_input("Designation")
                    e_mgr = st.text_input("Reporting Manager")
                    e_fat = st.text_input("Father's Name")
                    e_cont = st.text_input("Contact Number *")
                    e_email = st.text_input("Email ID")
                    e_addr = st.text_area("Address")
                with c2:
                    e_emg = st.text_input("Emergency Contact Person Name")
                    e_emg_n = st.text_input("Emergency Contact")
                    e_esic = st.text_input("ESIC")
                    e_pf = st.text_input("PF")
                    e_qual = st.text_input("Qualifications")
                    e_exp = st.text_input("Experience")
                    e_aad = st.text_input("Aadhaar")
                    e_pan = st.text_input("PAN")
                    e_stat = st.selectbox("Status", ["Active", "Inactive"])
                    e_mar = st.selectbox("Marital Status", ["Single", "Married"])
                    e_nat = st.text_input("Nationality")
                    e_bg = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-"])
                    e_pic = st.file_uploader("Photo Upload", type=['jpg', 'png'])
                    e_res = st.file_uploader("Resume Upload", type=['pdf'])
                
                if st.form_submit_button("Save Employee Profile"):
                    if e_id and e_name and e_cont:
                        st.session_state.profiles.append({"ID": e_id, "Name": e_name, "Contact": e_cont, "Dept": e_dept, "Status": e_stat})
                        st.success("Profile Added!"); st.rerun()
                    else: st.error("Please fill mandatory fields (*)")

        with t2:
            if st.session_state.profiles:
                df = pd.DataFrame(st.session_state.profiles)
                st.dataframe(df)
                del_id = st.selectbox("Select ID to Delete:", df["ID"].unique())
                if st.button("Delete Selected Employee"):
                    st.session_state.profiles = [p for p in st.session_state.profiles if p["ID"] != del_id]
                    st.warning("Deleted successfully!"); st.rerun()
            else: st.info("No profiles found.")

        with t3:
            if st.session_state.profiles:
                st.download_button("Download CSV", pd.DataFrame(st.session_state.profiles).to_csv(index=False), "Directory.csv")
