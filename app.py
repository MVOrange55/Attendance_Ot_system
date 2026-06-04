import streamlit as st
import pandas as pd

st.set_page_config(page_title="Employee Directory", layout="wide")

if 'profiles' not in st.session_state: st.session_state.profiles = []

st.title("👤 Employee Profile Directory")

t1, t2, t3 = st.tabs(["➕ Add Profile", "📋 Directory / Delete", "📤 Export"])

with t1:
    with st.form("emp_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            eid = st.text_input("Employee ID *")
            name = st.text_input("Full Name *")
            gen = st.selectbox("Gender *", ["Male", "Female", "Other"])
            dob = st.date_input("Date of Birth *")
            doj = st.date_input("Date of Joining *")
            dept = st.text_input("Department")
            desig = st.text_input("Designation")
            mgr = st.text_input("Reporting Manager")
            father = st.text_input("Father's Name")
            cont = st.text_input("Contact Number *")
            email = st.text_input("Email ID")
            addr = st.text_area("Address")
            photo = st.file_uploader("Photo Upload", type=['jpg', 'png'])
        with c2:
            emg_name = st.text_input("Emergency Contact Person Name")
            emg = st.text_input("Emergency Contact")
            esic = st.text_input("ESIC")
            pf = st.text_input("PF")
            qual = st.text_input("Qualifications")
            exp = st.text_input("Experience")
            aad = st.text_input("Aadhaar")
            pan = st.text_input("PAN")
            stat = st.selectbox("Status", ["Active", "Inactive"])
            mstat = st.selectbox("Marital Status", ["Single", "Married"])
            nat = st.text_input("Nationality")
            bg = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
            res = st.file_uploader("Resume Upload", type=['pdf'])
        
        if st.form_submit_button("Save Profile"):
            if eid and name and cont:
                st.session_state.profiles.append({"ID": eid, "Name": name, "Dept": dept, "Contact": cont, "Status": stat})
                st.success("Saved!")
            else: st.error("Fill mandatory fields (*)")

with t2:
    if st.session_state.profiles:
        df = pd.DataFrame(st.session_state.profiles)
        st.dataframe(df)
        del_id = st.selectbox("Select ID to Delete:", df["ID"].unique())
        if st.button("Delete Selected"):
            st.session_state.profiles = [p for p in st.session_state.profiles if p["ID"] != del_id]
            st.rerun()
    else: st.info("No data")

with t3:
    if st.session_state.profiles:
        df = pd.DataFrame(st.session_state.profiles)
        st.download_button("Download CSV", df.to_csv(index=False), "Directory.csv")
        st.download_button("Download PDF (HTML)", df.to_html(), "Directory.html")
