import streamlit as st

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Attendance System")

# 2. CSS for Attractive Sidebar and Clean Login (No Placeholders)
st.markdown("""
    <style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #2c3e50;
        color: white;
    }
    [data-testid="stSidebar"] h2 {
        color: #e67e22;
        font-weight: 600;
    }
    
    /* Input fields styling - Cleaning them up */
    div.stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #eee;
        padding: 10px;
    }
    
    /* Remove default labels if needed or style them */
    .stTextInput label {
        color: #e67e22;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Navigation Sidebar (Your 9 Reports)
st.sidebar.title("Navigation")
reports = [
    "1. Attendance Muster",
    "2. Overtime Report",
    "3. Exception Summary",
    "4. Exception Detailed",
    "5. Miss Punch Tracker",
    "6. Half Day Report",
    "7. Absenteeism Report",
    "8. Attendance Summary",
    "9. Correction Module"
]
selected_report = st.sidebar.radio("Select Report", reports, index=8)

# 4. Main Header
st.title(f"📊 {selected_report}")

# 5. Login Section (Blank Fields)
st.subheader("System Access")
col1, col2 = st.columns(2)

with col1:
    # label_visibility="collapsed" use karne se placeholder ya label box ke andar nahi dikhega
    username = st.text_input("Username", value="", placeholder="") 
with col2:
    password = st.text_input("Password", type="password", value="", placeholder="")

if st.button("Generate Report"):
    st.success(f"Generating {selected_report}...")
    # Yahan aapki report ka data aayega
    st.info("Report data loading...")

# 6. Dummy Report Data
st.divider()
st.write("### Recent Activity")
data = {
    "Employee ID": ["EMP_101", "EMP_102"],
    "Name": ["Rahul Singh", "Sonia Verma"],
    "Status": ["Present", "Correction Required"]
}
st.table(data)
