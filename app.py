import streamlit as st
import pandas as pd
import re

# 1. Page Config
st.set_page_config(layout="wide", page_title="Orange HR Dashboard")

# 2. Premium CSS (No Dots, No Numbers, Clean Nav)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50; min-width: 300px; }
    [data-testid="stSidebar"] * { color: white !important; }
    /* Navigation cleanup: Hide dots/radio buttons */
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 12px 20px; border-radius: 8px; margin-bottom: 8px;
        transition: 0.3s; background: rgba(255,255,255,0.05); cursor: pointer;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: #e67e22; }
    .stButton > button { background-color: #e67e22; color: white; border-radius: 10px; width: 100%; font-weight: bold; }
    
    /* Table Styling */
    .status-pass { color: #27ae60; font-weight: bold; }
    .status-fail { color: #e74c3c; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. Login Session Logic
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- LOGIN PAGE ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center; color: #e67e22;'>🔐 Orange HR Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        # Username aur Password column mein show nahi ho rahe (Stacked/Rows mein hain)
        # Placeholder khali hai (Blank boxes)
        u_val = st.text_input("Username", value="", placeholder="")
        p_val = st.text_input("Password", type="password", value="", placeholder="")
        
        if st.button("LOGIN"):
            if u_val == "Orange_Hr" and p_val == "Orange_Admin":
                st.session_state['logged_in'] = True
                st.session_state['user'] = u_val
                st.session_state['pass'] = p_val
                st.rerun()
            else:
                st.error("Invalid Credentials!")

# --- DASHBOARD (After Login) ---
else:
    # Sidebar Navigation (Numbers aur Dots hata diye hain)
    st.sidebar.title("Navigation")
    reports_list = [
        "Attendance Muster", "Overtime Report", "Exception Summary",
        "Exception Detailed", "Miss Punch Tracker", "Half Day Report",
        "Absenteeism Report", "Attendance Summary", "Correction Module",
        "Holiday Settings", "Upload File"
    ]
    choice = st.sidebar.radio("", reports_list)

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title(f"📊 {choice}")
    st.write("---")

    # --- THE 9 ORIGINAL RULES (Pahle Jese) ---
    st.subheader(f"Validation Analysis for: {choice}")
    
    user = st.session_state['user']
    pwd = st.session_state['pass']

    # Wahi 9 Reports/Rules jo aapne banwayi thi:
    rules_data = [
        {"ID": 1, "Report Rule": "Empty Username Check", "Status": "PASSED" if user else "FAILED", "Remark": "Field is filled"},
        {"ID": 2, "Report Rule": "Empty Password Check", "Status": "PASSED" if pwd else "FAILED", "Remark": "Field is filled"},
        {"ID": 3, "Report Rule": "Minimum Length (8)", "Status": "PASSED" if len(pwd)>=8 else "FAILED", "Remark": "Security requirement"},
        {"ID": 4, "Report Rule": "Maximum Length (20)", "Status": "PASSED" if len(pwd)<=20 else "FAILED", "Remark": "Char limit check"},
        {"ID": 5, "Report Rule": "No Space Check", "Status": "PASSED" if " " not in user else "FAILED", "Remark": "Username format"},
        {"ID": 6, "Report Rule": "Special Character Check", "Status": "PASSED" if re.search(r"[!@#$%^&*]", pwd) else "FAILED", "Remark": "Complexity check"},
        {"ID": 7, "Report Rule": "Numeric Value Check", "Status": "PASSED" if re.search(r"\d", pwd) else "FAILED", "Remark": "Contains digits"},
        {"ID": 8, "Report Rule": "Admin Name Restriction", "Status": "PASSED" if user.lower() != "admin" else "FAILED", "Remark": "Role security"},
        {"ID": 9, "Report Rule": "User ID Min Length (4)", "Status": "PASSED" if len(user)>=4 else "FAILED", "Remark": "ID verification"}
    ]

    # Displaying as a professional table
    df_rules = pd.DataFrame(rules_data)
    st.table(df_rules)

    # Extra features niche
    if choice == "Upload File":
        st.file_uploader("Upload Excel", type=['xlsx'])
    elif choice == "Holiday Settings":
        st.date_input("Set Holiday")
        st.text_input("Holiday Name", placeholder="")
