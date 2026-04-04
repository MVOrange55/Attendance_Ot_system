import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Orange HR Management")

# 2. Styling (No Dots, No Numbers, Professional Sidebar)
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
    .stButton > button { background-color: #e67e22; color: white; border-radius: 10px; width: 100%; font-weight: bold; }
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
        # Blank fields (No placeholders)
        u_name = st.text_input("Username", value="", placeholder="")
        p_name = st.text_input("Password", type="password", value="", placeholder="")
        if st.button("LOGIN"):
            if u_name == "Orange_Hr" and p_name == "Orange_Admin":
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Invalid Credentials!")

# --- DASHBOARD (After Login) ---
else:
    st.sidebar.title("Navigation")
    reports_list = [
        "Attendance Muster", "Overtime Report", "Exception Summary",
        "Exception Detailed", "Miss Punch Tracker", "Half Day Report",
        "Absenteeism Report", "Attendance Summary", "Correction Module",
        "Holiday Settings", "Upload Excel File"
    ]
    choice = st.sidebar.radio("", reports_list)

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title(f"📄 {choice}")
    st.divider()

    # --- 1. ATTENDANCE MUSTER REPORT ---
    if choice == "Attendance Muster":
        st.subheader("Monthly Attendance Muster")
        muster_data = pd.DataFrame({
            "Emp ID": ["101", "102", "103"],
            "Name": ["Rahul Sharma", "Sonia Verma", "Amit Kumar"],
            "Shift": ["General", "General", "Night"],
            "In-Time": ["09:00", "09:15", "21:00"],
            "Out-Time": ["18:00", "18:05", "06:00"],
            "Status": ["P", "P", "P"]
        })
        st.dataframe(muster_data, use_container_width=True)

    # --- 2. OVERTIME (OT) REPORT ---
    elif choice == "Overtime Report":
        st.subheader("Overtime (OT) Calculation Report")
        ot_data = pd.DataFrame({
            "Emp ID": ["101", "104", "105"],
            "Name": ["Rahul Sharma", "Priya Das", "Vikram Singh"],
            "Total Hrs": ["10:30", "11:00", "09:45"],
            "Standard Hrs": ["08:30", "08:30", "08:30"],
            "OT Hours": ["02:00", "02:30", "01:15"],
            "OT Pay": ["₹400", "₹500", "₹250"]
        })
        st.dataframe(ot_data, use_container_width=True)

    # --- 3. MISS PUNCH TRACKER ---
    elif choice == "Miss Punch Tracker":
        st.subheader("Missing Punch Details")
        miss_data = pd.DataFrame({
            "Emp ID": ["102", "106"],
            "Name": ["Sonia Verma", "Rajesh Khana"],
            "Date": ["03-04-2026", "04-04-2026"],
            "Type": ["Out-Punch Missing", "In-Punch Missing"]
        })
        st.table(miss_data)

    # --- 4. UPLOAD & HOLIDAY ---
    elif choice == "Upload Excel File":
        st.file_uploader("Upload Attendance Sheet", type=['xlsx'])
    
    elif choice == "Holiday Settings":
        st.date_input("Select Date")
        st.text_input("Holiday Name")
        st.button("Save Holiday")

    # --- DEFAULT FOR OTHERS ---
    else:
        st.info(f"Loading data for {choice}...")
        st.write("Data table will appear here after processing.")

    # Download Button Common for all
    st.download_button(label="Download Excel Report", data="Sample", file_name=f"{choice}.csv")
