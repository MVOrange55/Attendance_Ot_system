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

# --- 2. GLOBAL CSS / THEME OVERHAUL ---
st.markdown("""
<style>
    /* Global Page Styling */
    .stApp {
        background: #F1F5F9;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Top Header Banner */
    .hero-header {
        background: linear-gradient(135deg, #FF6B00 0%, #E05200 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: white !important;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(255, 107, 0, 0.3);
    }
    .hero-header h1 { color: #FFFFFF !important; margin: 0; font-size: 2.2rem; font-weight: 800; }
    .hero-header p { color: #FFEDD5 !important; margin-top: 4px; font-size: 1rem; opacity: 0.9; }

    /* Custom Cards */
    .metric-card {
        background: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .metric-card .num { font-size: 1.8rem; font-weight: 800; color: #FF6B00; }
    .metric-card .label { font-size: 0.85rem; color: #64748B; font-weight: 600; text-transform: uppercase; }

    /* Buttons Overhaul */
    .stButton > button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #1E293B !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
    }
    
    /* Primary Action Buttons */
    div[data-testid="stFormSubmitButton"] > button, .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF6B00 0%, #E05200 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 14px rgba(255, 107, 0, 0.35) !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover, .stButton > button[kind="primary"]:hover {
        opacity: 0.95;
        transform: translateY(-1px);
    }

    /* Input Controls */
    .stTextInput input, .stSelectbox > div, .stNumberInput input, .stTextArea textarea {
        border-radius: 8px !important;
        border: 1.5px solid #CBD5E1 !important;
        background-color: #FFFFFF !important;
    }
    .stTextInput input:focus, .stSelectbox > div:focus, .stTextArea textarea:focus {
        border-color: #FF6B00 !important;
        box-shadow: 0 0 0 3px rgba(255, 107, 0, 0.15) !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
    }
    section[data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #E2E8F0;
        padding: 6px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
        color: #475569;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #FF6B00 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'corrs' not in st.session_state: st.session_state.corrs = []
if 'profiles' not in st.session_state: st.session_state.profiles = []

# --- 4. HELPER FUNCTIONS ---
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
    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align: center; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border: 1px solid #E2E8F0;'>
                <span style='font-size: 60px;'>🍊</span>
                <h2 style='color: #FF6B00; font-weight: 800; margin-top: 10px; margin-bottom: 0;'>Orange House</h2>
                <p style='color: #64748B; font-size: 0.95rem;'>Enterprise HR Portal Sign-In</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            u = st.text_input("User ID", placeholder="admin")
            p = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Sign In to Portal", use_container_width=True)
            if submit:
                if u == "admin" and p == "H_r":
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Invalid credentials entered.")
else:
    # Sidebar Branding
    st.sidebar.markdown("""
        <div style='text-align: center; padding: 15px 0;'>
            <h2 style='color: #FF6B00 !important; margin:0;'>🍊 Orange House</h2>
            <p style='font-size: 0.8rem; color: #94A3B8 !important; margin:0;'>HR Management Studio</p>
        </div>
        <hr style="border-color: #334155; margin: 15px 0;">
    """, unsafe_allow_html=True)
    
    nav = st.sidebar.radio("Navigation", ["📊 Attendance Engine", "👤 Employee Directory"])
    
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    if st.sidebar.button("🔒 Logout Account", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

    # Top Banner Header
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
            "📊 Attendance Muster", 
            "📈 Summary Report", 
            "💰 OT Slab Report", 
            "⚠️ Late/Early Log", 
            "❌ Miss Punch", 
            "🛠️ Correction"
        ])
        
        if file:
            with st.spinner("Calculating Shifts & Overtime..."):
                m, s, o, ex, mi = run_hr_engine(pd.read_excel(file), hols, st.session_state.corrs)
            
            if m is not None:
                st.subheader(f"Output Matrix: {menu}")
                if menu == "📊 Attendance Muster": st.dataframe(m, use_container_width=True)
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
        # Directory Summary Metrics
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
            "➕ Add Profile", 
            "📄 Batch Import", 
            "🗑️ Batch Delete", 
            "🔍 Find & Edit", 
            "📥 Export Data", 
            "ℹ️ System Guide"
        ])
        
        with t1:
            st.markdown("##### Direct Profile Entry")
            with st.form("manual_emp", clear_on_submit=True):
                c1, c2 = st.columns(2)
                data = {
                    "ID": c1.text_input("ID"), 
                    "Name": c1.text_input("Name"), 
                    "Gender": c1.selectbox("Gender", ["Male", "Female"]), 
                    "DOB": str(c1.date_input("DOB")), 
                    "DOJ": str(c1.date_input("DOJ")), 
                    "Dept": c2.text_input("Department"), 
                    "Contact": c1.text_input("Contact No.", max_chars=10), 
                    "PF": c2.text_input("PF Number", max_chars=12), 
                    "Aadhaar": c1.text_input("Aadhaar Number", max_chars=12), 
                    "Status": c2.selectbox("Status", ["Active", "Inactive"]), 
                    "Designation": c2.text_input("Designation"), 
                    "Manager": c2.text_input("Reporting Manager"), 
                    "FatherName": c1.text_input("Father's Name"), 
                    "Email": c2.text_input("Work Email"), 
                    "Address": c2.text_area("Permanent Address", height=100), 
                    "EmergencyName": c1.text_input("Emergency Contact Person"), 
                    "EmergencyContact": c1.text_input("Emergency Phone"), 
                    "ESIC": c2.text_input("ESIC No."), 
                    "Qualification": c1.text_input("Highest Qualification"), 
                    "Experience": c2.text_input("Experience (Years)"), 
                    "PAN": c2.text_input("PAN Card No."), 
                    "MaritalStatus": c1.selectbox("Marital Status", ["Single", "Married"]), 
                    "Nationality": c2.text_input("Nationality", value="Indian"), 
                    "BloodGroup": c1.text_input("Blood Group")
                }
                photo = st.file_uploader("Upload Employee Picture", type=['jpg', 'png'])
                if st.form_submit_button("Save New Employee", use_container_width=True):
                    if photo: data["Photo"] = photo.name
                    st.session_state.profiles.append(data)
                    st.success("New Profile Registered Successfully!")

        with t2:
            st.markdown("##### Upload Bulk CSV Dataset")
            up = st.file_uploader("Choose CSV Source File", type=['csv'])
            if up: 
                try:
                    df_up = pd.read_csv(up, encoding='latin1').dropna(how='all').fillna('')
                    st.write(f"Detected Records: `{len(df_up)} Rows`")
                    st.dataframe(df_up, use_container_width=True) 
                    if st.button("Import Entire Dataset", type="primary"): 
                        st.session_state.profiles.extend(df_up.to_dict('records'))
                        st.success("Directory Data Imported Successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to read dataset: {e}")

        with t3:
            st.markdown("##### Bulk Delete Records")
            if st.session_state.profiles:
                options = {f"{p.get('ID')} - {p.get('Name')}": p.get('ID') for p in st.session_state.profiles}
                del_ids = st.multiselect("Target Employees to Delete:", options=list(options.keys()))
                if st.button("Confirm Purge Selected Records", type="primary"):
                    selected_ids = [options[k] for k in del_ids]
                    st.session_state.profiles = [p for p in st.session_state.profiles if p.get('ID') not in selected_ids]
                    st.success("Target profiles cleared!")
                    st.rerun()
            else:
                st.info("No saved records to delete.")

        with t4:
            st.markdown("##### Search & Inline Table Editor")
            if st.session_state.profiles:
                df = pd.DataFrame(st.session_state.profiles)
                c1, c2, c3 = st.columns(3)
                dept_list = df['Dept'].unique().tolist() if 'Dept' in df.columns else []
                desig_list = df['Designation'].unique().tolist() if 'Designation' in df.columns else []
                
                dept_filter = c1.multiselect("Filter Department:", dept_list)
                desig_filter = c2.multiselect("Filter Designation:", desig_list)
                search_term = c3.text_input("🔍 Quick Keyword Query:", placeholder="Type Name or Employee ID...")

                filt = df.copy()
                if dept_filter: filt = filt[filt['Dept'].isin(dept_filter)]
                if desig_filter: filt = filt[filt['Designation'].isin(desig_filter)]
                if search_term:
                    filt = filt[filt['Name'].astype(str).str.contains(search_term, case=False) | 
                                filt['ID'].astype(str).str.contains(search_term)]

                filt.insert(0, 'Sr. No.', range(1, len(filt) + 1))
                edited_df = st.data_editor(filt, use_container_width=True, num_rows="dynamic")
                
                if st.button("💾 Apply & Save Directory Edits", use_container_width=True):
                    if 'Sr. No.' in edited_df.columns: edited_df = edited_df.drop(columns=['Sr. No.'])
                    st.session_state.profiles = edited_df.to_dict('records')
                    st.success("Employee records synchronized!")
                    st.rerun()
