import streamlit as st
import pandas as pd

# 1. Page Config
st.set_page_config(layout="wide", page_title="HR Premium Dashboard")

# 2. Stylish CSS
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50; }
    [data-testid="stSidebar"] * { color: white !important; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #e67e22; color: white; }
    /* Navigation dots clean look */
    .nav-item { padding: 10px; border-bottom: 1px solid #34495e; cursor: pointer; }
    </style>
    """, unsafe_allow_html=True)

# 3. Login Session Logic
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- LOGIN PAGE ---
if not st.session_state['logged_in']:
    st.title("🔐 System Access")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.write("### Login to View Reports")
        # Blank inputs as requested
        u = st.text_input("Username", value="", placeholder="Enter Username")
        p = st.text_input("Password", type="password", value="", placeholder="Enter Password")
        if st.button("Login"):
            if u == "admin" and p == "1234": # Yahan apna password set karein
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Invalid Username or Password")

# --- DASHBOARD (After Login) ---
else:
    # Sidebar Navigation
    st.sidebar.title("Navigation")
    
    # Reports List (Numbers hataye gaye hain)
    menu = [
        "Attendance Muster", "Overtime Report", "Exception Summary", 
        "Exception Detailed", "Miss Punch Tracker", "Half Day Report", 
        "Absenteeism Report", "Attendance Summary", "Correction Module",
        "Holiday Settings", "Upload Data"
    ]
    choice = st.sidebar.radio("Select Module", menu)

    # Logout Button in Sidebar
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title(f"📊 {choice}")

    # --- MODULE 1: UPLOAD DATA ---
    if choice == "Upload Data":
        st.subheader("📁 Upload Your Attendance Excel")
        uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx', 'csv'])
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            st.success("File Uploaded Successfully!")
            st.dataframe(df)

    # --- MODULE 2: HOLIDAY SETTINGS ---
    elif choice == "Holiday Settings":
        st.subheader("📅 Manage Company Holidays")
        h_date = st.date_input("Select Holiday Date")
        h_name = st.text_input("Holiday Name (e.g. Diwali)")
        if st.button("Add Holiday"):
            st.write(f"Holiday '{h_name}' set for {h_date}")

    # --- OTHER REPORTS ---
    else:
        st.info(f"Showing data for {choice}")
        # Dummy Data Table
        st.write("### Recent Activity Report")
        sample_data = pd.DataFrame({
            "Employee ID": ["EMP_101", "EMP_102", "EMP_103"],
            "Name": ["Rahul Singh", "Sonia Verma", "Amit Kumar"],
            "Status": ["Present", "Correction Required", "Absent"]
        })
        st.table(sample_data)
