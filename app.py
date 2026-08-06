import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import json
import requests

# --- LOTTIE ANIMATION HELPER ---
try:
    from streamlit_lottie import st_lottie
    HAS_LOTTIE = True
except ImportError:
    HAS_LOTTIE = False

def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=3)
        if r.status_code != 200: return None
        return r.json()
    except: return None

# Load Login Animation JSON
lottie_login_json = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_kvwa8b2v.json") if HAS_LOTTIE else None

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="Orange House HR Portal", 
    layout="wide", 
    page_icon="🍊",
    initial_sidebar_state="expanded"
)

# --- 2. HIGH-CONTRAST VISIBILITY & ANIMATION CSS ---
st.markdown("""
<style>
    /* Main App Background */
    .stApp {
        background-color: #F8FAFC !important;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Hero Banner Header */
    .hero-header {
        background: linear-gradient(135deg, #FF6B00 0%, #E05200 100%);
        padding: 22px 28px;
        border-radius: 14px;
        color: #FFFFFF !important;
        margin-bottom: 20px;
        box-shadow: 0 8px 20px rgba(255, 107, 0, 0.25);
    }
    .hero-header h1 { color: #FFFFFF !important; margin: 0; font-size: 2rem; font-weight: 800; }
    .hero-header p { color: #FFEDD5 !important; margin: 4px 0 0 0; font-size: 0.95rem; }

    /* --- SIDEBAR VISIBILITY FIXES --- */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p {
        color: #F8FAFC !important;
        font-weight: 600 !important;
    }

    /* Fix Sidebar Dropdowns, Inputs & Selectboxes Text */
    section[data-testid="stSidebar"] div[data-baseweb="select"] *,
    section[data-testid="stSidebar"] .stSelectbox div,
    section[data-testid="stSidebar"] .stMultiSelect div,
    section[data-testid="stSidebar"] input {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* File Uploader Visibility Fix in Sidebar */
    section[data-testid="stSidebar"] section[data-testid="stFileUploadDropzone"] {
        background-color: #1E293B !important;
        border: 2px dashed #FF6B00 !important;
        border-radius: 10px !important;
    }
    section[data-testid="stSidebar"] section[data-testid="stFileUploadDropzone"] * {
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] section[data-testid="stFileUploadDropzone"] button {
        background-color: #FF6B00 !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
    }

    /* Keyframe Animations */
    @keyframes floatAnim {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    .floating-logo {
        animation: floatAnim 3s ease-in-out infinite;
        text-align: center;
        font-size: 80px;
        margin-bottom: 10px;
    }

    /* Buttons Styling */
    .stButton > button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #1E293B !important;
        transform: translateY(-1px);
    }
    
    div[data-testid="stFormSubmitButton"] > button, .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF6B00 0%, #E05200 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(255, 107, 0, 0.3) !important;
    }

    /* Metric Cards */
    .metric-card {
        background: #FFFFFF;
        padding: 16px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        text-align: center;
    }
    .metric-card .num { font-size: 1.6rem; font-weight: 800; color: #FF6B00; }
    .metric-card .label { font-size: 0.8rem; color: #64748B; font-weight: 600; text-transform: uppercase; }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #E2E8F0 !important;
        padding: 4px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #475569 !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #FF6B00 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'corrs' not in st.session_state: st.session_state.corrs = []
if 'profiles' not in st.session_state: st.session_state.profiles = []

# --- 4. HELPER & ENGINE FUNCTIONS ---
def get_pdf_download_link(df):
    return df.to_html(index=False)

def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00']: return None
    try:
        s = str(v).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(s))).time()
    except: return None

def get_slab_ot(extra_hrs):
    if extra_hrs < 0.25: return 0.0
    h = int(extra_hrs)
    m = round((extra_hrs - h) * 60)
    if 15 <= m < 27: slab = 0.00
    elif 29 <= m < 43: slab = 0.50
    elif 44 <= m < 57: slab = 0.75
    elif 59 <= m < 60: slab = 1.0
    elif m >= 60: h += 1; slab = 0.0
    else: slab = 0.0
    return float(h + slab)

def run_hr_engine(df, holidays, corrections):
    if df is None or df.empty: return None, None, None, None, None
    df_w = df.copy()
    id_c, name_c = df_w.columns[0], df_w.columns[1]
    df_w[id_c], df_w[name_c] = df_w[id_c].ffill(), df_w[name_c].ffill()
    for c in corrections:
        mask = df_w[id_c].astype(str).str.contains(str(c['id']))
        if any(mask):
            idx = df_w[mask].index[0]
            df_w.at[idx+1, str(c['date'])] = c['in']
            df_w.at[idx+2, str(c['date'])] = c['out']
    dates = [c for c in df_w.columns if str(c).replace('.0','').strip().isdigit()]
    sundays = [2, 9, 16, 23, 30] 
    res_m, res_s, res_o, res_ex, res_mi = [], [], [], [], []
    for eid in df_w[id_c].unique():
        if pd.isna(eid): continue
        clean_id = str(int(float(eid))) if '.' in str(eid) else str(eid).replace(':', '')
        block = df_w[df_w[id_c] == eid].reset_index(drop=True)
        ename = str(block.iloc[0][name_c])
        row_m, row_o = {"ID": clean_id, "Name": ename}, {"ID": clean_id, "Name": ename}
        sl_used, p_c, a_c, ab_c, wo_c, h_c, tot_ot = False, 0, 0, 0, 0, 0, 0.0
        late_log, early_log = [], []
        for d in dates:
            d_i = int(float(d))
            t_in, t_out = parse_t(block.iloc[1][d]), parse_t(block.iloc[2][d])
            status, day_ot = "A", 0.0
            is_off_day = d_i in holidays or d_i in sundays
            if not t_in and not t_out:
                if d_i in sundays: status, wo_c = "WO", wo_c + 1
                elif d_i in holidays: status, h_c = "H", h_c + 1
                else: status, a_c = "A", a_c + 1
            elif (t_in and not t_out) or (not t_in and t_out):
                status, a_c = "A", a_c + 1
                miss_type = "OUT Punch Missing" if t_in else "IN Punch Missing"
                res_mi.append({"ID": clean_id, "Name": ename, "Date": d_i, "Status": "Miss Punch", "Detail": miss_type})
            else:
                d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
                if d2 <= d1: d2 += timedelta(days=1)
                actual_dur = (d2 - d1).total_seconds() / 3600
                if is_off_day:
                    status = "WO" if d_i in sundays else "H"
                    day_ot = get_slab_ot(actual_dur)
                    if d_i in sundays: wo_c += 1 
                    else: h_c += 1
                else:
                    if t_in >= time(13, 30):
                        work_hrs = (d2 - datetime.combine(datetime.today(), time(14, 0))).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 4.0) if work_hrs > 4.0 else 0.0
                        status = "AB/"
                    else:
                        work_hrs = (d2 - datetime.combine(datetime.today(), max(t_in, time(9, 30)))).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 8.5) if work_hrs > 8.5 else 0.0
                        if actual_dur < 4.0: status = "AB/"
                        elif t_in > time(10, 16) or t_out < time(16, 0):
                            if not sl_used and actual_dur >= 6.0: status, sl_used = "P*", True
                            else: status = "AB/"
                        else: status = "P"
                        if t_in is not None and t_in > time(9, 35):
                            late_log.append(f"{d_i}({t_in.strftime('%H:%M')})")
                        if work_hrs < 8.5:
                            out_str = t_out.strftime('%H:%M') if t_out is not None else "N/A"
                            early_log.append(f"{d_i}({out_str})")
                    if status in ["P", "P*"]: p_c += 1
                    elif status == "AB/": ab_c += 0.5
            row_m[str(d_i)], row_o[str(d_i)] = status, day_ot
            tot_ot += day_ot
        res_m.append(row_m)
        res_s.append({"Emp ID": clean_id, "Name": ename, "P": p_c, "A": a_c, "AB/": ab_c, "H": h_c, "WO": wo_c, "OT": tot_ot})
        row_o["Total OT"] = tot_ot
        res_o.append(row_o)
        res_ex.append({
            "Emp ID": clean_id, "Name": ename, "Late Days": len(late_log), "Late In Detail": " | ".join(late_log),
            "Early Out Days": len(early_log), "Early Out Detail ( < 8.5h )": " | ".join(early_log)
        })
    return pd.DataFrame(res_m), pd.DataFrame(res_s), pd.DataFrame(res_o), pd.DataFrame(res_ex), pd.DataFrame(res_mi)

# --- 5. UI FLOW ---
if not st.session_state.auth:
    c1, c2 = st.columns([1.1, 1])
    
    with c1:
        if HAS_LOTTIE and lottie_login_json:
            st_lottie(lottie_login_json, height=360, key="login_animation")
        else:
            st.markdown("""
                <br><br>
                <div class="floating-logo">🍊</div>
                <h2 style='text-align: center; color: #FF6B00; font-weight: 800;'>Orange House HR</h2>
            """, unsafe_allow_html=True)
            
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='background: white; padding: 30px; border-radius: 16px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05);'>
                <h2 style='color: #FF6B00; margin: 0; font-weight: 800;'>Admin Sign In</h2>
                <p style='color: #64748B; font-size: 0.9rem; margin-bottom: 20px;'>Enter credentials to access HR Engine</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            u = st.text_input("User ID", placeholder="admin")
            p = st.text_input("Password", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("🔒 Secure Login", use_container_width=True)
            
            if submit:
                if u == "admin" and p == "H_r":
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
else:
    # Sidebar
    st.sidebar.markdown("""
        <div style='text-align: center; padding: 10px 0 20px 0;'>
            <h2 style='color: #FF6B00 !important; margin: 0;'>🍊 Orange House</h2>
            <span style='font-size: 0.8rem; color: #94A3B8 !important;'>HR Management Studio</span>
        </div>
        <hr style='border-color: #334155;'>
    """, unsafe_allow_html=True)
    
    nav = st.sidebar.radio("Navigation:", ["📊 Attendance Engine", "👤 Employee Directory"])
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("🔒 Logout Account", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

    # Top Banner
    st.markdown("""
        <div class="hero-header">
            <h1>Orange House HR Portal</h1>
            <p>Smart Attendance Analytics & Employee Directory Workspace</p>
        </div>
    """, unsafe_allow_html=True)
    
    if nav == "📊 Attendance Engine":
        st.sidebar.markdown("### ⚙️ Engine Options")
        file = st.sidebar.file_uploader("Upload Attendance Excel", type=['xlsx'])
        hols = st.sidebar.multiselect("Select Holidays:", range(1, 32))
        menu = st.sidebar.selectbox("Select Report View:", [
            " 📊 Attendance Muster", 
            "📈 Summary Report", 
            "💰 OT Slab Report", 
            "⚠️ Late/Early Log", 
            "❌ Miss Punch", 
            "🛠️ Correction"
        ])
        
        if file:
            with st.spinner("Processing calculations..."):
                m, s, o, ex, mi = run_hr_engine(pd.read_excel(file), hols, st.session_state.corrs)
            
            if m is not None:
                st.subheader(f"Output Matrix: {menu.strip()}")
                if menu == " 📊 Attendance Muster": st.dataframe(m, use_container_width=True)
                elif menu == "📈 Summary Report": st.dataframe(s, use_container_width=True)
                elif menu == "💰 OT Slab Report": st.dataframe(o, use_container_width=True)
                elif menu == "⚠️ Late/Early Log": st.dataframe(ex, use_container_width=True)
                elif menu == "❌ Miss Punch": st.dataframe(mi, use_container_width=True)
        else:
            st.info("👈 Upload an Excel dataset via sidebar control panel to generate live workforce calculations.")

        if menu == "🛠️ Correction":
            st.markdown("### 🛠️ Manual Punch Adjustment")
            with st.form("corr_form"):
                c1, c2, c3, c4 = st.columns(4)
                eid = c1.text_input("Employee ID")
                dt = c2.number_input("Day of Month", 1, 31)
                cin = c3.text_input("Punch IN Time (HH:MM)")
                cout = c4.text_input("Punch OUT Time (HH:MM)")
                if st.form_submit_button("Submit Punch Adjustment"):
                    st.session_state.corrs.append({'id': eid, 'date': int(dt), 'in': cin, 'out': cout})
                    st.success("Punch Override Applied!")
                    st.rerun()
    
    else:
        # Directory Metrics
        m1, m2, m3, m4 = st.columns(4)
        df_prof = pd.DataFrame(st.session_state.profiles) if st.session_state.profiles else pd.DataFrame()
        
        tot = len(df_prof)
        act = len(df_prof[df_prof['Status'] == 'Active']) if not df_prof.empty and 'Status' in df_prof.columns else 0
        depts = df_prof['Dept'].nunique() if not df_prof.empty and 'Dept' in df_prof.columns else 0
        
        m1.markdown(f'<div class="metric-card"><div class="num">{tot}</div><div class="label">Total Records</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><div class="num">{act}</div><div class="label">Active Staff</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><div class="num">{depts}</div><div class="label">Departments</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-card"><div class="num">{len(st.session_state.corrs)}</div><div class="label">Active Overrides</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        t1, t2, t3, t4, t5, t6 = st.tabs([
            "➕ Add Manual", 
            "📄 Important Uploads", 
            "🗑️ Delete Record", 
            "🔍 Filter/Edit", 
            "📥 Download", 
            "ℹ️ Help"
        ])
        
        with t1:
            with st.form("manual_emp", clear_on_submit=True):
                c1, c2 = st.columns(2)
                data = {
                    "ID": c1.text_input("ID"), 
                    "Name": c1.text_input("Name"), 
                    "Gender": c1.selectbox("Gender", ["Male", "Female"]), 
                    "DOB": str(c1.date_input("DOB")), 
                    "DOJ": str(c1.date_input("DOJ")), 
                    "Dept": c2.text_input("Dept"), 
                    "Contact": c1.text_input("Contact (Max 10)", max_chars=10), 
                    "PF": c2.text_input("PF (Max 12)", max_chars=12), 
                    "Aadhaar": c1.text_input("Aadhaar (Max 12)", max_chars=12), 
                    "Status": c2.selectbox("Status", ["Active", "Inactive"]), 
                    "Designation": c2.text_input("Designation"), 
                    "Manager": c2.text_input("Manager"), 
                    "FatherName": c1.text_input("FatherName"), 
                    "Email": c2.text_input("Email"), 
                    "Address": c2.text_area("Address", height=100), 
                    "EmergencyName": c1.text_input("EmergencyName"), 
                    "EmergencyContact": c1.text_input("EmergencyContact"), 
                    "ESIC": c2.text_input("ESIC"), 
                    "Qualification": c1.text_input("Qualification"), 
                    "Experience": c2.text_input("Experience"), 
                    "PAN": c2.text_input("PAN"), 
                    "MaritalStatus": c1.selectbox("MaritalStatus", ["Single", "Married"]), 
                    "Nationality": c2.text_input("Nationality"), 
                    "BloodGroup": c1.text_input("BloodGroup")
                }
                photo = st.file_uploader("Upload Employee Photo", type=['jpg', 'png'])
                if st.form_submit_button("Save Record", use_container_width=True):
                    if photo: data["Photo"] = photo.name
                    st.session_state.profiles.append(data)
                    st.success("Record Saved Successfully!")

        with t2:
            up = st.file_uploader("Upload CSV", type=['csv'])
            if up: 
                try:
                    df_up = pd.read_csv(up, encoding='latin1').dropna(how='all').fillna('')
                    st.write(f"Total Rows Found: {len(df_up)}")
                    st.dataframe(df_up, use_container_width=True) 
                    if st.button("Confirm & Upload"): 
                        st.session_state.profiles.extend(df_up.to_dict('records'))
                        st.success("Data Imported Successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error reading file: {e}")

        with t3:
            st.subheader("Batch Delete Employees")
            if st.session_state.profiles:
                options = {f"{p.get('ID')} - {p.get('Name')}": p.get('ID') for p in st.session_state.profiles}
                del_ids = st.multiselect("Select Employees to Delete:", options=list(options.keys()))
                if st.button("Confirm Delete Selected", type="primary"):
                    selected_ids = [options[k] for k in del_ids]
                    st.session_state.profiles = [p for p in st.session_state.profiles if p.get('ID') not in selected_ids]
                    st.success("Selected records deleted!")
                    st.rerun()
            else:
                st.info("No employee profiles found.")

        with t4:
            st.subheader("Search & Filter Employees")
            if st.session_state.profiles:
                df = pd.DataFrame(st.sessio
