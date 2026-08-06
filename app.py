import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="Orange House HR Portal", 
    layout="wide", 
    page_icon="🍊",
    initial_sidebar_state="expanded"
)

# --- CUSTOM MODERN STYLING (CSS) ---
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #FAFAFA;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Primary Accent Styling */
    :root {
        --primary-color: #F97316;
        --primary-dark: #EA580C;
        --bg-card: #FFFFFF;
    }

    /* Headings */
    h1, h2, h3 {
        color: #1E293B !important;
        font-weight: 700 !important;
    }
    
    /* Custom Header Card */
    .brand-header {
        background: linear-gradient(135deg, #FF8C00 0%, #F97316 100%);
        padding: 24px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(249, 115, 22, 0.3);
    }
    .brand-header h1 {
        color: white !important;
        margin: 0;
        font-size: 2rem;
    }
    .brand-header p {
        margin: 5px 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }

    /* Login Box Glassmorphism */
    .login-container {
        max-width: 420px;
        margin: 60px auto;
        padding: 40px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 20px 25px -5px rgba(0,0,0,0.08), 0 8px 10px -6px rgba(0,0,0,0.01);
        border: 1px solid #F1F5F9;
        text-align: center;
    }

    /* Styled Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        border: none !important;
    }
    
    /* Primary Button Styling */
    div[data-testid="stFormSubmitButton"] > button, .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #F97316 0%, #EA580C 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.25) !important;
    }
    
    div[data-testid="stFormSubmitButton"] > button:hover, .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(249, 115, 22, 0.35) !important;
    }

    /* Input Fields */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
    }
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #F97316 !important;
        box-shadow: 0 0 0 2px rgba(249, 115, 22, 0.2) !important;
    }

    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background-color: #1E293B !important;
    }
    section[data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 4px;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #F1F5F9;
        padding: 6px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        color: #64748B !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #F97316 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
    }

    /* Data Editor / Dataframes */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE INITIALIZATION ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'corrs' not in st.session_state: st.session_state.corrs = []
if 'profiles' not in st.session_state: st.session_state.profiles = []

# --- 3. HELPER FUNCTION ---
def get_pdf_download_link(df):
    html = df.to_html(index=False)
    return html

# --- 4. ENGINE FUNCTIONS ---
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

# Fast Calculation via Caching
@st.cache_data(show_spinner=False)
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

# --- 5. UI APP FLOW ---
if not st.session_state.auth:
    # Modern Login Layout
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align: center; margin-bottom: 20px;'>
                <span style='font-size: 64px;'>🍊</span>
                <h2 style='margin-top: 10px; font-weight: 800; color: #1E293B;'>Orange House</h2>
                <p style='color: #64748B;'>Enterprise HR Management Portal</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.subheader("Sign In")
            u = st.text_input("User ID", placeholder="Enter your username")
            p = st.text_input("Password", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Login to Portal", use_container_width=True)
            
            if submit:
                if u == "admin" and p == "H_r": 
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
else:
    # Sidebar Header Branding
    st.sidebar.markdown("""
        <div style='padding: 10px 0px 20px 0px; text-align: center;'>
            <h2 style='color: #F97316 !important; margin: 0;'>🍊 Orange House</h2>
            <span style='font-size: 0.8rem; color: #94A3B8;'>HR Operations Suite</span>
        </div>
    """, unsafe_allow_html=True)
    
    nav = st.sidebar.radio("Navigation", ["📊 Attendance Engine", "👤 Employee Directory"])
    st.sidebar.markdown("---")
    if st.sidebar.button("🔒 Logout", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

    # Main Top Banner
    st.markdown("""
        <div class="brand-header">
            <h1>Orange House HR Portal</h1>
            <p>Attendance Processing, OT Calculation & Employee Directory Management</p>
        </div>
    """, unsafe_allow_html=True)
    
    if nav == "📊 Attendance Engine":
        st.sidebar.markdown("### ⚙️ Engine Settings")
        file = st.sidebar.file_uploader("Upload Attendance Excel", type=['xlsx'])
        hols = st.sidebar.multiselect("Select Holidays:", range(1, 32))
        menu = st.sidebar.selectbox("Select Report View:", ["📊 Attendance Muster", "📈 Summary Report", "💰 OT Slab Report", "⚠️ Late/Early Log", "❌ Miss Punch", "🛠️ Correction"])
        
        if file:
            with st.spinner("Processing attendance calculations..."):
                m, s, o, ex, mi = run_hr_engine(pd.read_excel(file), hols, tuple(st.session_state.corrs))
            
            if m is not None:
                st.subheader(f"Report Output: {menu.strip()}")
                if menu == "📊 Attendance Muster": st.dataframe(m, use_container_width=True)
                elif menu == "📈 Summary Report": st.dataframe(s, use_container_width=True)
                elif menu == "💰 OT Slab Report": st.dataframe(o, use_container_width=True)
                elif menu == "⚠️ Late/Early Log": st.dataframe(ex, use_container_width=True)
                elif menu == "❌ Miss Punch": st.dataframe(mi, use_container_width=True)
        else:
            st.info("👈 Please upload an Attendance Excel file from the sidebar to begin processing.")

        if menu == "🛠️ Correction":
            st.markdown("### 🛠️ Attendance Punch Correction")
            with st.form("corr_form"):
                c1, c2, c3, c4 = st.columns(4)
                eid = c1.text_input("Employee ID")
                dt = c2.number_input("Date", 1, 31)
                cin = c3.text_input("IN Time (HH:MM)")
                cout = c4.text_input("OUT Time (HH:MM)")
                
                if st.form_submit_button("Add Correction"):
                    st.session_state.corrs.append({'id': eid, 'date': int(dt), 'in': cin, 'out': cout})
                    st.success("Correction entry saved successfully!")
                    st.rerun()
    
    else:
        st.subheader("Employee Profile Management")
        t1, t2, t3, t4, t5, t6 = st.tabs([
            "➕ Add Manual", "📄 Import CSV", "🗑️ Delete Record", 
            "🔍 Filter & Edit", "📥 Export", "ℹ️ Help"
        ])
        
        with t1:
            st.markdown("##### Fill Employee Details")
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
                if st.form_submit_button("💾 Save Record", use_container_width=True):
                    if photo: data["Photo"] = photo.name
                    st.session_state.profiles.append(data)
                    st.success("Employee Record Saved Successfully!")

        with t2:
            st.markdown("##### Batch Import Profiles")
            up = st.file_uploader("Upload CSV File", type=['csv'])
            if up: 
                try:
                    df_up = pd.read_csv(up, encoding='latin1').dropna(how='all').fillna('')
                    st.success(f"Total Rows Found: {len(df_up)}")
                    st.dataframe(df_up, use_container_width=True) 
                    if st.button("Confirm & Upload Records", type="primary"): 
                        st.session_state.profiles.extend(df_up.to_dict('records'))
                        st.success("Data Imported Successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error reading file: {e}")

        with t3:
            st.markdown("##### Batch Delete Employees")
            if st.session_state.profiles:
                options = {f"{p.get('ID')} - {p.get('Name')}": p.get('ID') for p in st.session_state.profiles}
                del_ids = st.multiselect("Select Employees to Delete:", options=list(options.keys()))
                if st.button("Confirm Delete Selected", type="primary"):
                    selected_ids = [options[k] for k in del_ids]
                    st.session_state.profiles = [p for p in st.session_state.profiles if p.get('ID') not in selected_ids]
                    st.success("Selected records deleted!")
                    st.rerun()
            else:
                st.info("No employee profiles available to delete.")

        with t4:
            st.markdown("##### Search & Filter Employees")
            if st.session_state.profiles:
                df = pd.DataFrame(st.session_state.profiles)
                c1, c2, c3 = st.columns(3)
                dept_list = df['Dept'].unique().tolist() if 'Dept' in df.columns else []
                desig_list = df['Designation'].unique().tolist() if 'Designation' in df.columns else []
                
                dept_filter = c1.multiselect("Filter by Dept:", dept_list)
                desig_filter = c2.multiselect("Filter by Designation:", desig_list)
                search_term = c3.text_input("🔍 Quick Find:", placeholder="Search by name or ID...")

                filt = df.copy()
                if dept_filter: filt = filt[filt['Dept'].isin(dept_filter)]
                if desig_filter: filt = filt[filt['Designation'].isin(desig_filter)]
                if search_term:
                    filt = filt[filt['Name'].astype(str).str.contains(search_term, case=False) | 
                                filt['ID'].astype(str).str.contains(search_term)]

                filt.insert(0, 'Sr. No.', range(1, len(filt) + 1))
                edited_df = st.data_editor(filt, use_container_width=True, num_rows="dynamic")
                
                if st.button("💾 Save All Changes", use_container_width=True, type="primary"):
                    if 'Sr. No.' in edited_df.columns: edited_df = edited_df.drop(columns=['Sr. No.'])
                    st.session_state.profiles = edited_df.to_dict('records')
                    st.success("Changes saved successfully!")
                    st.rerun()
            else:
                st.info("No employee profiles found.")

        with t5:
            st.markdown("##### Export Employee Directory")
            if st.session_state.profiles:
                df = pd.DataFrame(st.session_state.profiles)
                c1, c2 = st.columns(2)
                c1.download_button("📥 Export CSV Data", df.to_csv(index=False), "Employee_Report.csv", use_container_width=True)
                c2.markdown(f'<a href="data:text/html;charset=utf-8,{get_pdf_download_link(df)}" download="Report.html" style="text-decoration:none;"><button style="width:100%; height:40px; border-radius:10px; background:#1E293B; color:white; border:none; font-weight:600; cursor:pointer;">📥 Download Printable HTML/PDF</button></a>', unsafe_allow_html=True)
            else:
                st.info("No employee profiles available for export.")

        with t6:
            st.warning("⚠️ Ensure CSV headers match the exact template schema before uploading.")
