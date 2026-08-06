import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
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
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

lottie_anime = load_lottieurl("https://assets8.lottiefiles.com/packages/lf20_1pfig97b.json") if HAS_LOTTIE else None

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="Orange House HR Portal", 
    layout="wide", 
    page_icon="🌲",
    initial_sidebar_state="expanded"
)

# --- 2. MISTY FOREST BACKGROUND & GLASSMORPHISM CSS ---
# Aap apni image URL ko niche 'bg_url' me Replace kar sakte hain
bg_url = "https://images.unsplash.com/photo-1511497584788-876761c119ef?auto=format&fit=crop&w=1920&q=80"

st.markdown(f"""
<style>
    /* App Background with Dark Overlay for Image */
    .stApp {{
        background: linear-gradient(rgba(11, 14, 20, 0.75), rgba(11, 14, 20, 0.88)), 
                    url('{bg_url}') no-repeat center center fixed !important;
        background-size: cover !important;
        color: #F3F4F6 !important;
        font-family: 'Inter', -apple-system, sans-serif;
    }}

    /* Keyframe Pulse Animation for Login Glow */
    @keyframes cozyGlow {{
        0% {{ box-shadow: 0 0 15px rgba(245, 158, 11, 0.3); }}
        50% {{ box-shadow: 0 0 30px rgba(245, 158, 11, 0.7), 0 0 15px rgba(34, 197, 94, 0.4); }}
        100% {{ box-shadow: 0 0 15px rgba(245, 158, 11, 0.3); }}
    }}

    /* Glassmorphism Login Card Box */
    .login-box {{
        background: rgba(17, 24, 39, 0.85) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        padding: 35px;
        border-radius: 18px;
        border: 1px solid rgba(245, 158, 11, 0.5);
        animation: cozyGlow 4s infinite ease-in-out;
    }}

    /* Top Banner Header */
    .hero-header {{
        background: linear-gradient(135deg, rgba(180, 83, 9, 0.9) 0%, rgba(20, 83, 45, 0.9) 100%);
        backdrop-filter: blur(8px);
        padding: 22px 28px;
        border-radius: 14px;
        color: #FFFFFF !important;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 25px rgba(0,0,0,0.4);
    }}
    .hero-header h1 {{ color: #FFFFFF !important; margin: 0; font-size: 2.2rem; font-weight: 800; }}
    .hero-header p {{ color: #FEF2F2 !important; margin: 4px 0 0 0; font-size: 0.95rem; }}

    /* --- SIDEBAR & WIDGET VISIBILITY OVERRIDES --- */
    section[data-testid="stSidebar"] {{
        background-color: rgba(3, 7, 18, 0.92) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid #1F2937;
    }}
    
    /* Universal Text Color Override */
    label, p, span, h1, h2, h3, h4, h5, h6, div {{
        color: #F9FAFB !important;
    }}

    /* File Uploader FIX */
    [data-testid="stFileUploadDropzone"] {{
        background-color: rgba(30, 41, 59, 0.85) !important;
        border: 2px dashed #F59E0B !important;
        border-radius: 10px !important;
    }}
    [data-testid="stFileUploadDropzone"] * {{
        color: #F8FAFC !important;
        background-color: transparent !important;
    }}

    /* Selectbox & Multiselect FIX */
    div[data-baseweb="select"] > div {{
        background-color: #1E293B !important;
        border-color: #374151 !important;
        color: #FFFFFF !important;
    }}
    div[data-baseweb="select"] * {{
        color: #FFFFFF !important;
        background-color: transparent !important;
    }}
    div[data-baseweb="popover"] {{
        background-color: #111827 !important;
    }}
    li[role="option"] {{
        background-color: #1E293B !important;
        color: #FFFFFF !important;
    }}
    li[role="option"]:hover {{
        background-color: #F59E0B !important;
    }}

    /* Multiselect Tags Styling */
    span[data-baseweb="tag"] {{
        background-color: #D97706 !important;
        border-radius: 4px !important;
    }}
    span[data-baseweb="tag"] * {{
        color: #FFFFFF !important;
    }}

    /* Inputs Focus */
    input, textarea {{
        color: #FFFFFF !important;
        background-color: #1E293B !important;
        border-color: #374151 !important;
    }}
    input:focus, textarea:focus {{
        border-color: #22C55E !important;
        box-shadow: 0 0 8px rgba(34, 197, 94, 0.5) !important;
    }}

    /* Buttons Styling */
    .stButton > button {{
        background: #15803D !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
    }}
    .stButton > button:hover {{
        background: #22C55E !important;
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.6) !important;
        transform: translateY(-2px);
    }}
    
    /* Form Submit Button */
    div[data-testid="stFormSubmitButton"] > button {{
        background: linear-gradient(135deg, #D97706 0%, #F59E0B 100%) !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4) !important;
    }}

    /* Metric Cards */
    .metric-card {{
        background: rgba(17, 24, 39, 0.85);
        backdrop-filter: blur(8px);
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #374151;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        text-align: center;
    }}
    .metric-card .num {{ font-size: 1.8rem; font-weight: 800; color: #F59E0B; }}
    .metric-card .label {{ font-size: 0.85rem; color: #9CA3AF !important; font-weight: 700; text-transform: uppercase; }}

    /* Data Frame Tables */
    div[data-testid="stDataFrame"] {{
        background-color: rgba(17, 24, 39, 0.9) !important;
        border-radius: 10px;
        border: 1px solid #374151;
    }}

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: rgba(17, 24, 39, 0.85) !important;
        padding: 6px;
        border-radius: 8px;
        border: 1px solid #1F2937;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: #9CA3AF !important;
        font-weight: 700 !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #D97706 !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'corrs' not in st.session_state:
    st.session_state.corrs = []
if 'profiles' not in st.session_state:
    st.session_state.profiles = []

# --- 4. HELPER & ENGINE FUNCTIONS ---
def get_pdf_download_link(df):
    return df.to_html(index=False)

def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00']:
        return None
    try:
        s = str(v).strip()
        if ':' in s:
            return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(s))).time()
    except Exception:
        return None

def get_slab_ot(extra_hrs):
    if extra_hrs < 0.25:
        return 0.0
    h = int(extra_hrs)
    m = round((extra_hrs - h) * 60)
    if 15 <= m < 27:
        slab = 0.00
    elif 29 <= m < 43:
        slab = 0.50
    elif 44 <= m < 57:
        slab = 0.75
    elif 59 <= m < 60:
        slab = 1.0
    elif m >= 60:
        h += 1
        slab = 0.0
    else:
        slab = 0.0
    return float(h + slab)

def run_hr_engine(df, holidays, corrections):
    if df is None or df.empty:
        return None, None, None, None, None
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
        if pd.isna(eid):
            continue
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
                if d_i in sundays:
                    status, wo_c = "WO", wo_c + 1
                elif d_i in holidays:
                    status, h_c = "H", h_c + 1
                else:
                    status, a_c = "A", a_c + 1
            elif (t_in and not t_out) or (not t_in and t_out):
                status, a_c = "A", a_c + 1
                miss_type = "OUT Punch Missing" if t_in else "IN Punch Missing"
                res_mi.append({"ID": clean_id, "Name": ename, "Date": d_i, "Status": "Miss Punch", "Detail": miss_type})
            else:
                d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
                if d2 <= d1:
                    d2 += timedelta(days=1)
                actual_dur = (d2 - d1).total_seconds() / 3600
                if is_off_day:
                    status = "WO" if d_i in sundays else "H"
                    day_ot = get_slab_ot(actual_dur)
                    if d_i in sundays:
                        wo_c += 1 
                    else:
                        h_c += 1
                else:
                    if t_in >= time(13, 30):
                        work_hrs = (d2 - datetime.combine(datetime.today(), time(14, 0))).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 4.0) if work_hrs > 4.0 else 0.0
                        status = "AB/"
                    else:
                        work_hrs = (d2 - datetime.combine(datetime.today(), max(t_in, time(9, 30)))).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 8.5) if work_hrs > 8.5 else 0.0
                        if actual_dur < 4.0:
                            status = "AB/"
                        elif t_in > time(10, 16) or t_out < time(16, 0):
                            if not sl_used and actual_dur >= 6.0:
                                status, sl_used = "P*", True
                            else:
                                status = "AB/"
                        else:
                            status = "P"
                        if t_in is not None and t_in > time(9, 35):
                            late_log.append(f"{d_i}({t_in.strftime('%H:%M')})")
                        if work_hrs < 8.5:
                            out_str = t_out.strftime('%H:%M') if t_out is not None else "N/A"
                            early_log.append(f"{d_i}({out_str})")
                    if status in ["P", "P*"]:
                        p_c += 1
                    elif status == "AB/":
                        ab_c += 0.5
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
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        if HAS_LOTTIE and lottie_anime:
            st_lottie(lottie_anime, height=420, key="anime_login_art")
        else:
            st.markdown("""
                <br><br>
                <div style='text-align: center;'>
                    <h1 style='font-size: 100px; margin: 0; text-shadow: 0 0 25px #F59E0B;'>🛖</h1>
                    <h1 style='color: #F59E0B; font-weight: 900; letter-spacing: 2px;'>MISTY HR REALM</h1>
                    <p style='color: #22C55E; font-weight: 600;'>Orange House Portal Access</p>
                </div>
            """, unsafe_allow_html=True)
            
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div class="login-box">
                <h2 style='color: #F9FAFB; margin: 0; font-weight: 800;'>Login to your account</h2>
                <p style='color: #9CA3AF; font-size: 0.9rem; margin-bottom: 25px;'>Welcome back! Enter credentials to continue.</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            u = st.text_input("User ID", placeholder="admin")
            p = st.text_input("Password", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("LOG IN TO SYSTEM", use_container_width=True)
            
            if submit:
                if u == "admin" and p == "H_r":
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Invalid Credentials. Please try again.")
else:
    # Sidebar Navigation
    st.sidebar.markdown("""
        <div style='text-align: center; padding: 10px 0 20px 0;'>
            <h2 style='color: #F59E0B !important; margin: 0; font-weight: 900;'>🔥 Orange House</h2>
            <span style='font-size: 0.85rem; color: #22C55E !important; font-weight: 700;'>HR Management Suite</span>
        </div>
        <hr style='border-color: #374151;'>
    """, unsafe_allow_html=True)
    
    nav = st.sidebar.radio("Navigation Menu:", ["📊 Attendance Engine", "👤 Employee Directory"])
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("🔒 Logout Account", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

    # Main Hero Banner
    st.markdown("""
        <div class="hero-header">
            <h1>Orange House HR Portal</h1>
            <p>High-Performance Workforce Engine & Analytics Directory</p>
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
            with st.spinner("Crunching analytics..."):
                m, s, o, ex, mi = run_hr_engine(pd.read_excel(file), hols, st.session_state.corrs)
            
            if m is not None:
                st.subheader(f"Output Matrix: {menu.strip()}")
                if menu == " 📊 Attendance Muster":
                    st.dataframe(m, use_container_width=True)
                elif menu == "📈 Summary Report":
                    st.dataframe(s, use_container_width=True)
                elif menu == "💰 OT Slab Report":
                    st.dataframe(o, use_container_width=True)
                elif menu == "⚠️ Late/Early Log":
                    st.dataframe(ex, use_container_width=True)
                elif menu == "❌ Miss Punch":
                    st.dataframe(mi, use_container_width=True)
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
            "📄 CSV Upload", 
            "🗑️ Delete Record", 
            "🔍 Search & Edit", 
            "📥 Export Data", 
            "ℹ️ System Info"
        ])
        
        with t1:
            with st.form("manual_emp", clear_on_submit=True):
                c1, c2 = st.columns(2)
                data = {
                    "ID": c1.text_input("ID"), 
                    "Name": c1.text_input("Name"), 
                    "Gender": c1.selectbox("Gender", ["Male", "Female"]), 
                    "DOB": str(c1.date_input("DOB")), 
                    "DOJ": str(c2.date_input("DOJ")), 
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
                
