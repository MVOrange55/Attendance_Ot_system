import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="Orange House HR Portal", layout="wide", page_icon="🍊")

if 'auth' not in st.session_state: st.session_state.auth = False
if 'profiles' not in st.session_state: st.session_state.profiles = []

# --- AUTH ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color: #f97316;'>Orange House HR Portal</h1>", unsafe_allow_html=True)
    u = st.text_input("User ID"); p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "admin" and p == "orange_hr": st.session_state.auth = True; st.rerun()
else:
    nav = st.sidebar.radio("Navigation:", ["👤 Employee Directory"])
    
    if nav == "👤 Employee Directory":
        st.subheader("👤 Employee Directory")
        t1, t2, t3 = st.tabs(["➕ Add / Update Profile", "📋 Directory / Filter / Delete", "📊 Custom Reports"])
        
        with t1:
            with st.form("emp_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    eid = st.text_input("Employee ID *")
                    name = st.text_input("Full Name *")
                    gen = st.selectbox("Gender *", ["Male", "Female", "Other"], index=0)
                    dob = st.date_input("Date of Birth *")
                    doj = st.date_input("Date of Joining *")
                    dept = st.text_input("Department")
                    desig = st.text_input("Designation")
                    mgr = st.text_input("Reporting Manager")
                    fat = st.text_input("Father's Name")
                    cont = st.text_input("Contact Number *")
                with c2:
                    email = st.text_input("Email ID")
                    addr = st.text_area("Address")
                    esic = st.text_input("ESIC"); pf = st.text_input("PF")
                    qual = st.text_input("Qualifications"); exp = st.text_input("Experience")
                    aad = st.text_input("Aadhaar"); pan = st.text_input("PAN")
                    stat = st.selectbox("Status", ["Active", "Inactive"])
                    mst = st.selectbox("Marital Status", ["Single", "Married"])
                    nat = st.text_input("Nationality"); bg = st.text_input("Blood Group")
                
                if st.form_submit_button("Save/Update Profile"):
                    if eid and name and cont:
                        st.session_state.profiles = [p for p in st.session_state.profiles if str(p.get("ID")) != str(eid)]
                        st.session_state.profiles.append({
                            "ID": eid, "Name": name, "Gender": gen, "DOB": str(dob), "DOJ": str(doj), 
                            "Dept": dept, "Designation": desig, "Manager": mgr, "Contact": cont, 
                            "Email": email, "Address": addr, "ESIC": esic, "PF": pf, 
                            "Qual": qual, "Exp": exp, "Aadhaar": aad, "PAN": pan, 
                            "Status": stat, "Marital": mst, "Nationality": nat, "BloodGroup": bg
                        })
                        st.success("Record Saved/Updated!"); st.rerun()
                    else: st.error("Fill mandatory fields (*)")

        with t2:
            if st.session_state.profiles:
                df = pd.DataFrame(st.session_state.profiles)
                c_f1, c_f2 = st.columns(2)
                f_dept = c_f1.multiselect("Filter by Dept:", df["Dept"].unique())
                f_mgr = c_f2.multiselect("Filter by Manager:", df["Manager"].unique())
                if f_dept: df = df[df["Dept"].isin(f_dept)]
                if f_mgr: df = df[df["Manager"].isin(f_mgr)]
                
                st.dataframe(df, use_container_width=True)
                
                del_id = st.selectbox("Select ID to Delete:", df["ID"].unique())
                if st.button("Delete Selected"):
                    st.session_state.profiles = [p for p in st.session_state.profiles if str(p.get("ID")) != str(del_id)]
                    st.rerun()
            else: st.info("No records found.")

        with t3:
            st.subheader("📥 Download Reports")
            if st.session_state.profiles:
                df = pd.DataFrame(st.session_state.profiles)
                
                report_choice = st.selectbox("Select Report:", ["Report 1: Dept & Manager", "Report 2: Work Profile", "Report 3: Statutory & Personal"])
                
                if report_choice == "Report 1: Dept & Manager": view_df = df[['ID', 'Name', 'Dept', 'Manager']]
                elif report_choice == "Report 2: Work Profile": view_df = df[['ID', 'Name', 'Designation', 'DOJ', 'Dept', 'Contact']]
                else: view_df = df[['ID', 'Name', 'ESIC', 'PF', 'PAN', 'Status', 'BloodGroup']]
                
                st.dataframe(view_df, use_container_width=True)
                
                c1, c2 = st.columns(2)
                c1.download_button("📥 Export CSV", view_df.to_csv(index=False), f"{report_choice}.csv")
                
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(200, 10, txt=report_choice, ln=True, align='C')
                pdf.set_font("Arial", size=8)
                for _, row in view_df.iterrows():
                    pdf.cell(200, 7, txt=str(row.tolist()), ln=True)
                c2.download_button("📄 Export PDF", pdf.output(dest='S').encode('latin-1'), f"{report_choice}.pdf")
            else: st.info("Add employees to generate reports.")
                
