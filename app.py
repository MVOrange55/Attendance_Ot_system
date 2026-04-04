import streamlit as st
import pandas as pd
import re

# 1. Page Config
st.set_page_config(layout="wide", page_title="Orange HR System")

# 2. Premium CSS (Navigation dots hataye, clean list banayi)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50; min-width: 300px; }
    [data-testid="stSidebar"] * { color: white !important; }
    /* Navigation cleanup: Hide radio dots */
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 12px 20px; border-radius: 8px; margin-bottom: 8px;
        transition: 0.3s; background: rgba(255,255,255,0.05); cursor: pointer;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: #e67e22; }
    .stButton > button { background-color: #e67e22; color: white; border-radius: 12px; width: 100%; font-weight: bold; height: 45px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Session State Initialization (Error se bachne ke liye)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'u_name' not in st.session_state:
    st.session_state['u_name'] = ""
if 'p_name' not in st.session_state:
    st.session_state['p_name'] = ""

# --- LOGIN PAGE ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center; color: #e67e22;'>🔐 Orange HR Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        # Blank fields
        u_input = st.text_input("Username", value="", placeholder="")
        p_input = st.text_input("Password", type="password", value="", placeholder="")
        if st.button("LOGIN"):
            if u_input == "Orange_Hr" and p_input == "Orange_Admin":
                st.session_state['logged_in'] = True
                st.session_state['u_name'] = u_input
                st.session_state['p_name'] = p_input
                st.rerun()
            else:
                st.error("Galt User ya Password!")

# --- DASHBOARD (Sirf Login ke baad dikhega) ---
else:
    # Sidebar Navigation (Wahi 9 Reports jo aapne batayi thi)
    st.sidebar.title("Navigation")
    menu = [
        "Attendance Muster", "Overtime Report", "Exception Summary",
        "Exception Detailed", "Miss Punch Tracker", "Half Day Report",
        "Absenteeism Report", "Attendance Summary", "Correction Module",
        "Holiday Settings", "Upload Excel Data"
    ]
    choice = st.sidebar.radio("", menu)

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear() # Poora session saaf
        st.rerun()

    st.title(f"📊 {choice}")
    st.divider()

    # --- 9 VALIDATION RULES (HAR REPORT MEIN DIKHEGA) ---
    st.subheader("🛡️ Security & Validation Report")
    u = st.session_state['u_name']
    p = st.session_state['p_name']
    
    rules = [
        {"ID": 1, "Rule": "Empty User Check", "Status": "✅ PASS" if u else "❌ FAIL"},
        {"ID": 2, "Rule": "Empty Pass Check", "Status": "✅ PASS" if p else "❌ FAIL"},
        {"ID": 3, "Rule": "Min Length (8)", "Status": "✅ PASS" if len(p)>=8 else "❌ FAIL"},
        {"ID": 4, "Rule": "Max Length (20)", "Status": "✅ PASS" if len(p)<=20 else "❌ FAIL"},
        {"ID": 5, "Rule": "No Space in User", "Status": "✅ PASS" if " " not in u else "❌ FAIL"},
        {"ID": 6, "Rule": "Special Char Check", "Status": "✅ PASS" if re.search(r"[!@#$%^&*]", p) else "❌ FAIL"},
        {"ID": 7, "Rule": "Numeric Check", "Status": "✅ PASS" if re.search(r"\d", p) else "❌ FAIL"},
        {"ID": 8, "Rule": "Admin Restricted", "Status": "✅ PASS" if u.lower() != "admin" else "❌ FAIL"},
        {"ID": 9, "Rule": "User ID Min Length", "Status": "✅ PASS" if len(u)>=4 else "❌ FAIL"}
    ]
    st.table(pd.DataFrame(rules))
    st.divider()

    # --- ACTUAL REPORT CONTENT ---
    if choice == "Attendance Muster":
        st.write("### 📅 Monthly Attendance Record")
        st.dataframe(pd.DataFrame({
            "Emp ID": ["1001", "1002", "1003"],
            "Name": ["Rahul Sharma", "Sonia Verma", "Amit Kumar"],
            "In-Time": ["09:00", "09:15", "08:50"],
            "Out-Time": ["18:00", "18:05", "18:15"],
            "Status": ["P", "P", "P"]
        }), use_container_width=True)

    elif choice == "Overtime Report":
        st.write("### 🕒 OT Calculation")
        st.table(pd.DataFrame({
            "Name": ["Rahul Sharma", "Amit Kumar"],
            "Total Hrs": ["10:00", "09:30"],
            "OT Hrs": ["01:30", "01:00"]
        }))

    elif choice == "Miss Punch Tracker":
        st.error("Miss Punches Identified:")
        st.table(pd.DataFrame({
            "Date": ["04-04-2026"], "Emp Name": ["Sonia Verma"], "Type": ["Out-Punch Missing"]
        }))

    elif choice == "Upload Excel Data":
        st.file_uploader("Upload Attendance File", type=['xlsx'])

    elif choice == "Holiday Settings":
        st.date_input("Select Date")
        st.text_input("Holiday Name")
        if st.button("Add Holiday"): st.success("Holiday Added!")

    else:
        st.info(f"Generating data for {choice}...")
