import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. UI & LOGIN ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .login-box {
        max-width: 400px; margin: auto; padding: 2rem;
        background: white; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-top: 8px solid #FF5722; margin-top: 50px;
        text-align: center;
    }
    [data-testid="stSidebar"] { background: linear-gradient(#FF5722, #E64A19); }
    [data-testid="stSidebar"] * { color: white !important; }
    </style>
""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.header("🍊 Orange House Login")
        u = st.text_input("User Name", placeholder="Orange_Hr")
        p = st.text_input("Password", type="password", placeholder="Orange_Admin")
        if st.button("Login"):
            if u == "Orange_Hr" and p == "Orange_Admin":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Wrong User/Pass")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 2. LOGIC HELPERS ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00', '0']: return None
    try:
        s = str(v).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(s))).time()
    except: return None

def get_ot(hrs, status, is_special_day):
    # Sunday ya Holiday pe Pura OT
    if is_special_day: 
        val = hrs
    elif status == "AB/": 
        val = max(0, hrs - 4.0)
    else: 
        val = max(0, hrs - 8.5)
    
    if val <= 0: return 0
    h, m = int(val), (val - int(val)) * 60
    rm = 0.75 if m >= 45 else (0.50 if m >= 30 else (0.25 if m >= 15 else 0))
    return h + rm

def style_muster(v):
    # WO aur H ko Green, P ko No Color
    c_map = {'WO': '#2ecc71', 'H': '#2ecc71', 'AB/': '#3498db', 'P (SL)': '#f1c40f', 'A': '#e74c3c', 'Miss': '#e67e22'}
    if v == 'P': return '' 
    c = c_map.get(v, '')
    return f'background-color: {c}; color: {"white" if c and c!="#f1c40f" else "black"}'

# --- 3. MAIN APP ---
st.sidebar.title("🛠️ HR Admin Panel")
if st.sidebar.button("🔓 Logout"):
    st.session_state.auth = False
    st.rerun()

f = st.sidebar.file_uploader("📂 Upload Attendance Excel", type=['xlsx'])
wo_dates = [1, 8, 15, 22, 29] # Sundays
h_days = st.sidebar.multiselect("📅 Select Holiday Dates", options=list(range(1, 32)))
nav = st.sidebar.radio("📋 Select Report", ["Muster (Attendance)", "OT Report", "Final Summary"])

if f:
    try:
        df = pd.read_excel(f)
        df.columns = [str(c).strip() for c in df.columns]
        id_c, name_c = df.columns[0], df.columns[1]
        df[id_c], df[name_c] = df[id_c].ffill(), df[name_c].ffill()
        
        date_cols = [c for c in df.columns if c.replace('.0','').isdigit()]
        sorted_d = sorted([int(float(d)) for d in date_cols])

        res_m, res_o, res_f = [], [], []

        for eid in df[id_c].unique():
            if pd.isna(eid): continue
            block = df[df[id_c] == eid].reset_index(drop=True)
            ename = str(block.iloc[0][name_c])
            type_col = block.columns[2]
            
            in_r = block[block[type_col].astype(str).str.contains('In', na=False, case=False)].head(1)
            out_r = block[block[type_col].astype(str).str.contains('Out', na=False, case=False)].head(1)
            
            if in_r.empty or out_r.empty: continue

            temp_s, sl_done = {}, False
            for d in sorted_d:
                ds = str(float(d)) if str(float(d)) in date_cols else str(d)
                t1, t2 = parse_t(in_r[ds].values[0]), parse_t(out_r[ds].values[0])
                
                if d in wo_dates: temp_s[d] = "WO"
                elif d in h_days: temp_s[d] = "H"
                elif not t
