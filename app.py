import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. PAGE CONFIG & APP STYLE ---
st.set_page_config(page_title="Orange House HR Dashboard", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .login-box {
        max-width: 400px; margin: auto; padding: 2rem;
        background: white; border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-top: 5px solid #FF4B1F; margin-top: 50px;
    }
    .header { text-align: center; color: #333; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ATTRACTIVE LOGIN SYSTEM ---
def login():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.markdown('<h2 class="header">🍊 Orange House Pvt Ltd</h2>', unsafe_allow_html=True)
            st.markdown('<p style="text-align:center;">HR Master Dashboard</p>', unsafe_allow_html=True)
            
            u = st.text_input("User Name")
            p = st.text_input("Password", type="password")
            
            if st.button("Login to Dashboard"):
                if u == "Orange_Hr" and p == "Orange_Admin":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Ghalat Password ya User Name")
            st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

login()

# --- 3. COLORS & LOGIC HELPERS ---
def apply_color(val):
    colors = {
        'AB/': 'background-color: #3498db; color: white;', # Blue
        'P (SL)': 'background-color: #f1c40f; color: black;', # Yellow
        'A': 'background-color: #e74c3c; color: white;', # Red
        'Miss': 'background-color: #e67e22; color: white;', # Orange
        'P': 'background-color: #2ecc71; color: white;', # Green
        'H': 'background-color: #bdc3c7; color: black;'  # Gray
    }
    return colors.get(val, '')

def parse_time(val):
    if pd.isna(val) or str(val).strip().lower() in ['', 'nan', '0', '00:00', 'none']: 
        return None
    try:
        v = str(val).strip()
        if ':' in v: return datetime.strptime(v[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(v))).time()
    except: return None

def get_ot(work_hrs, status, is_h):
    if is_h: ot = work_hrs
    elif status == "AB/": ot = max(0, work_hrs - 4.0)
    else: ot = max(0, work_hrs - 8.5)
    
    if ot <= 0: return 0
    h = int(ot)
    m = (ot - h) * 60
    if m < 15: rm = 0
    elif m < 30: rm = 0.25
    elif m < 45: rm = 0.50
    elif m < 60: rm = 0.75
    else: h += 1; rm = 0
    return h + rm

# --- 4. MAIN DASHBOARD ---
st.sidebar.title("🛠️ HR Navigation")
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()

uploaded_file = st.sidebar.file_uploader("1. Upload Excel File", type=['xlsx'])
selected_holidays = st.sidebar.multiselect("2. Select Holidays", options=list(range(1, 32)))
report_nav = st.sidebar.radio("3. Reports", ["Attendance Muster", "OT Report", "Exception Summary", "Miss Punch", "Final Summary"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [str(c).strip() for c in df.columns]
        id_col, name_col = df.columns[0], df.columns[1]
        df[id_col], df[name_col] = df[id_col].ffill(), df[name_col].ffill()
        
        # Detect Date Columns
        date_cols = [c for c in df.columns if c.replace('.0','').isdigit()]
        sorted_dates = sorted([int(float(d)) for d in date_cols])

        muster_data, ot_data, ex_sum, miss_p, final_sum = [], [], [], [], []

        for eid in df[id_col].unique():
            if pd.isna(eid): continue
            emp_block = df[df[id_col] == eid].reset_index(
