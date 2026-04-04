import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="HR Premium Dashboard")

# 2. Custom CSS for Premium Look (No Dots, No Numbers in Nav)
st.markdown("""
    <style>
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #2c3e50;
        min-width: 300px;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    /* Hide Radio Buttons (Dots) to make it a clean list */
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 8px;
        transition: 0.3s ease;
        background: rgba(255,255,255,0.05);
        cursor: pointer;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: #e67e22;
        transform: translateX(5px);
    }
    /* Login Button Styling */
    div.stButton > button:first-child {
        background-color: #e67e22;
        color: white;
        border-radius: 10px;
        width: 100%;
        height: 50px;
        font-weight: bold;
    }
    /* Input Field Styling */
    .stTextInput input {
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Session State for Login Tracking
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- LOGIN PAGE LOGIC ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center; color: #e67e22; margin-top: 50px;'>🔐 HR System Login</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("---")
        # Inputs without placeholders
        u_name = st.text_input("Username", value="", placeholder="")
        p_name = st.text_input("Password", type="password", value="", placeholder="")
        
        if st.button("LOGIN TO DASHBOARD"):
            if u_name == "Orange_Hr" and p_name == "Orange_Admin":
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Invalid Username or Password. Please try again!")
    st.markdown("<p style='text-align: center; color: grey;'>Fields are blank for security.</p>", unsafe_allow_html=True)

# --- PROTECTED DASHBOARD PAGE ---
else:
    # Sidebar Navigation - Removed Numbers and Dots
    st.sidebar.markdown("## 🧭 Navigation")
    
    reports_list = [
        "Attendance Muster",
        "Overtime Report",
        "Exception Summary",
        "Exception Detailed",
        "Miss Punch Tracker",
        "Half Day Report",
        "Absenteeism Report",
        "Attendance Summary",
        "Correction Module",
        "Holiday Settings",
        "Upload Attendance File"
    ]
    
    choice = st.sidebar.radio("", reports_list)

    # Logout functionality
    st.sidebar.write("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # Main Display Area
    st.title(f"📊 {choice}")
    st.write(f"Current System Date: 4th April, 2026")

    # --- 1. UPLOAD FILE MODULE ---
    if choice == "Upload Attendance File":
        st.subheader("📁 Upload Data for Processing")
        up_file = st.file_uploader("Select Excel File (.xlsx)", type=['xlsx'])
        if up_file:
            data_df = pd.read_excel(up_file)
            st.success("File Processed Successfully!")
            st.dataframe(data_df, use_container_width=True)

    # --- 2. HOLIDAY SETTINGS MODULE ---
    elif choice == "Holiday Settings":
        st.subheader("📅 Configure Calendar Holidays")
        h_date = st.date_input("Select Date")
        h_desc = st.text_input("Reason / Holiday Name")
        if st.button("Add to Holiday List"):
            st.success(f"Holiday '{h_desc}' saved for {h_date}")

    # --- 3. ALL 9 REPORTS DATA ---
    else:
        st.markdown(f"### Generating {choice}...")
        # Showing a sample table for the reports
        st.write("Recent Records Found:")
        sample_report = pd.DataFrame({
            "Emp ID": ["1001", "1002", "1003", "1004"],
            "Employee Name": ["Rahul Sharma", "Sonia Verma", "Amit Kumar", "Priya Das"],
            "Department": ["IT", "HR", "Sales", "Finance"],
            "Status": ["Present", "Correction Required", "On Leave", "Half Day"]
        })
        st.table(sample_report)
        
        st.download_button(
            label=f"Download {choice} Excel",
            data="Sample Data",
            file_name=f"{choice.replace(' ', '_')}.csv",
            mime="text/csv"
        )
