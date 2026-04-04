import streamlit as st
import pandas as pd
import re

# 1. Page Config
st.set_page_config(layout="wide", page_title="Orange HR Premium")

# 2. CSS: Navigation clean (No dots, No numbers)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50; min-width: 300px; }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 12px 20px; border-radius: 8px; margin-bottom: 8px;
        transition: 0.3s; background: rgba(255,255,255,0.05); cursor: pointer;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: #e67e22; }
    .stButton > button { background-color: #e67e22; color: white; border-radius: 12px; width: 100%; font-weight: bold; height: 45px; }
    .stTextInput input { border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Session State for Login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- LOGIN SECTION ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center; color: #e67e22;'>🔐 Orange HR System Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        # Blank Fields (No Placeholders)
        u_name = st.text_input("Username", value="", placeholder="")
        p_name = st.text_input("Password", type="password", value="", placeholder="")
        if st.button("LOGIN TO SYSTEM"):
            if u_name == "Orange_Hr" and p_name == "Orange_Admin":
                st.session_state['logged_in'] = True
                st.session_state['u_name'] = u_name
                st.session_state['p_name'] = p_name
                st.rerun()
            else:
                st.error("Galt Password ya User! Check karein.")

# --- DASHBOARD SECTION (After Login) ---
else:
    # Sidebar Navigation (Wahi 9 Reports)
    st.sidebar.title("HR Navigation")
    menu = [
        "Attendance Muster", "Overtime Report", "Exception Summary",
        "Exception Detailed", "Miss Punch Tracker", "Half Day Report",
        "Absenteeism Report", "Attendance Summary", "Correction Module",
        "Holiday Settings", "Upload Excel Data"
    ]
    choice = st.sidebar.radio("", menu)

    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title(f"📊 {choice}")
    st.divider()

    # --- 9 VALIDATION RULES (Jo Lock Karwaye The) ---
    st.subheader("🛡️ Security & Validation Report")
    
    u = st.session_state['u_name']
    p = st.session_state['p_name']

    rules = [
        {"ID": 1, "Validation Rule": "Empty User Check", "Status": "✅ PASS" if u else "❌ FAIL"},
        {"ID": 2, "Validation Rule": "Empty Pass Check", "Status": "✅ PASS" if p else "❌ FAIL"},
        {"ID": 3, "Validation Rule": "Min Password Length (8)", "Status": "✅ PASS" if len(p)>=8 else "❌ FAIL"},
        {"ID": 4, "Validation Rule": "Max Password Length (20)", "Status": "✅ PASS" if len(p)<=20 else "❌ FAIL"},
        {"ID": 5, "Validation Rule": "No Spaces in Username", "Status": "✅ PASS" if " " not in u else "❌ FAIL"},
        {"ID": 6, "Validation Rule": "Special Character Check", "Status": "✅ PASS" if re.search(r"[!@#$%^&*]", p) else "❌ FAIL"},
        {"ID": 7, "Validation Rule": "Numeric Check (0-9)", "Status": "✅ PASS" if re.search(r"\d", p) else "❌ FAIL"},
        {"ID": 8, "Validation Rule": "Admin Role Restriction", "Status": "✅ PASS" if u.lower() != "admin" else "❌ FAIL"},
        {"ID": 9, "Validation Rule": "User ID Format (Min 4)", "Status": "✅ PASS" if len(u)>=4 else "❌ FAIL"}
    ]
    st.table(pd.DataFrame(rules))

    st.divider()

    # --- ASALI HR REPORT DATA ---
    if choice == "Attendance Muster":
        st.write("### 📅 Employee Attendance Muster")
        df_muster = pd.DataFrame({
            "Emp ID": ["1001", "1002", "1003", "1004"],
            "Employee Name": ["Rahul Sharma", "Sonia Verma", "Amit Kumar", "Priya Das"],
            "In-Time": ["09:00", "09:15", "08:55", "09:30"],
            "Out-Time": ["18:00", "18:05", "18:10", "17:30"],
            "Status": ["Present", "Present", "Present", "Late In"]
        })
        st.dataframe(df_muster, use_container_width=True)

    elif choice == "Overtime Report":
        st.write("### 🕒 OT Calculation Report")
        df_ot = pd.DataFrame({
            "Emp ID": ["1001", "1003"],
            "Name": ["Rahul Sharma", "Amit Kumar"],
            "Work Hrs": ["10:00", "09:30"],
            "Standard": ["08:30", "08:30"],
            "OT Hrs": ["01:30", "01:00"],
            "OT Pay": ["₹350", "₹250"]
        })
        st.table(df_ot)

    elif choice == "Miss Punch Tracker":
        st.write("### ⚠️ Missing Punch List")
        df_miss = pd.DataFrame({
            "Date": ["03-04-2026", "04-04-2026"],
            "Emp Name": ["Sonia Verma", "Vikram Singh"],
            "Issue": ["Out-Punch Missing", "In-Punch Missing"]
        })
        st.error("Missing Punches Found!")
        st.table(df_miss)

    elif choice == "Upload Excel Data":
        st.subheader("📁 Upload New Attendance File")
        up = st.file_uploader("Upload .xlsx file", type=['xlsx'])
        if up: st.success("File Processed!")

    elif choice == "Holiday Settings":
        st.subheader("📅 Set Company Holidays")
        h_date = st.date_input("Date")
        h_name = st.text_input("Holiday Name")
        if st.button("Save"): st.success("Holiday Locked!")

    else:
        st.info(f"Generating Detailed Data for {choice}...")
        st.write("Running backend processing for records...")
