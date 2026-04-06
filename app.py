import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

# Custom CSS for Attractive Login & UI
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .login-box {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.1);
        border-top: 5px solid #ff4b1f;
    }
    .stButton>button {
        background-color: #ff4b1f;
        color: white;
        border-radius: 8px;
        width: 100%;
        height: 45px;
        font-weight: bold;
    }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIN SYSTEM ---
def login_page():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.image("https://cdn-icons-png.flaticon.com/512/912/912265.png", width=80)
            st.markdown("<h2 style='text-align: center; color: #333;'>Orange House Pvt Ltd</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #666;'>HR Master Dashboard Access</p>", unsafe_allow_html=True)
            
            user = st.text_input("Username", placeholder="Enter Username")
            pas = st.text_input("Password", type="password", placeholder="Enter Password")
            
            if st.button("Access Dashboard"):
                if user == "Orange_Hr" and pas == "Orange_Admin":
                    st.session_state.logged_in = True
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Invalid Credentials. Please try again.")
            st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

login_page()

# --- 3. HELPER FUNCTIONS ---
def parse_time_safe(val):
    if pd.isna(val) or str(val).strip().lower() in ['', 'nan', '0', '00:00', 'none']: 
        return None
    try:
        v = str(val).strip()
        if ':' in v: return datetime.strptime(v[:5], '%H:%M').time()
        else: return (datetime(1900, 1, 1) + timedelta(days=float(v))).time()
    except: return None

def get_ot(work_hrs, status, is_h):
    # Rule: Holiday (is_h) par Full OT. AB/ par 4h deduction, P par 8.5h deduction.
    if is_h: ot_val = work_hrs 
    elif status == "AB/": ot_val = max(0, work_hrs - 4.0)
    else: ot_val = max(0, work_hrs - 8.5)
    
    if ot_val <= 0: return 0
    h = int(ot_val)
    m = (ot_val - h) * 60
    if m < 15: rm = 0
    elif m < 30: rm = 0.25
    elif m < 45: rm = 0.50
    elif m < 60: rm = 0.75
    else: h += 1; rm = 0
    return h + rm

# --- 4. DASHBOARD UI ---
st.sidebar.markdown("### 🛠️ Navigation")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

uploaded_file = st.sidebar.file_uploader("📂 Upload Attendance File", type=['xlsx'])
selected_holidays = st.sidebar.multiselect("📅 Select Holidays/Sundays", options=list(range(1, 32)))

report_choice = st.sidebar.radio("📊 Choose Report", 
    ["Attendance Muster", "OT Report", "Exception Summary", "Exception Detailed", "Miss Punch", "Final Summary"])

# --- 5. CORE LOGIC WITH PWP HOLIDAY RULE ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [str(c).strip() for c in df.columns]
        id_col, name_col = df.columns[0], df.columns[1]
        df[id_col], df[name_col] = df[id_col].ffill(), df[name_col].ffill()
        date_cols = [c for c in df.columns if c.replace('.0','').isdigit()]
        sorted_dates = sorted([int(float(d)) for d in date_cols])

        muster, ot_rep, ex_sum, ex_det, miss_p, final_sum = [], [], [], [], [], []

        for eid in df[id_col].unique():
            if pd.isna(eid): continue
            e_data = df[df[id_col] == eid].reset_index(drop=True)
            ename, type_col = str(e_data.iloc[0][name_col]), e_data.columns[2]
            
            in_row = e_data[e_data[type_col].astype(str).str.contains('In', case=False, na=False)].head(1)
            out_row = e_data[e_data[type_col].astype(str).str.contains('Out', case=False, na=False)].head(1)
            if in_row.empty or out_row.empty: continue

            temp_status_map = {}
            sl_used = False
            
            # Phase 1: Determine Normal Day Status
            for d in sorted_dates:
                d_str = str(float(d)) if str(float(d)) in date_cols else str(d)
                t_in = parse_time_safe(in_row[d_str].values[0])
                t_out = parse_time_safe(out_row[d_str].values[0])
                
                if d in selected_holidays:
                    temp_status_map[d] = "H_PENDING"
                elif not t_in or not t_out:
                    temp_status_map[d] = "A" if (not t_in and not t_out) else "Miss"
                else:
                    d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
                    if d2 <= d1: d2 += timedelta(days=1)
                    work_h = (d2 - d1).total_seconds() / 3600
                    if t_in <= time(10, 16) and work_h >= 8.5: temp_status_map[d] = "P"
                    elif not sl_used: temp_status_map[d] = "P (SL)"; sl_used = True
                    else: temp_status_map[d] = "AB/"

            # Phase 2: Apply PWP Rule for Holidays
            m_row, o_row = {"ID": eid, "Name": ename}, {"ID": eid, "Name": ename}
            p_c, a_c, ab_c, h_c, tot_ot = 0, 0, 0, 0, 0
            ab_dates = []

            for d in sorted_dates:
                d_str = str(float(d)) if str(float(d)) in date_cols else str(d)
                status = temp_status_map[d]
                
                if status == "H_PENDING":
                    # Check Preceding & Following
                    prev_s = temp_status_map.get(d-1, "A")
                    next_s = temp_status_map.get(d+1, "A")
                    # Agar aage ya piche Present/AB/ hai toh Holiday milega, warna A
                    if (prev_s in ["P", "P (SL)", "AB/"]) or (next_s in ["P", "P (SL)", "AB/"]):
                        status = "H"; h_c += 1
                    else:
                        status = "A"; a_c += 1
                
                # OT Calculation
                daily_ot = 0
                t_in = parse_time_safe(in_row[d_str].values[0])
                t_out = parse_time_safe(out_row[d_str].values[0])
                if t_in and t_out:
                    d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
                    if d2 <= d1: d2 += timedelta(days=1)
                    daily_ot = get_ot((d2-d1).total_seconds()/3600, status, (status=="H"))

                if status in ["P", "P (SL)"]: p_c += 1
                elif status == "AB/": ab_c += 1; ab_dates.append(str(d))
                
                m_row[d], o_row[d] = status, daily_ot
                tot_ot += daily_ot

            m_row.update({"P": p_c, "AB/": ab_c, "A": a_c, "H": h_c})
            o_row["Total OT"] = tot_ot
            muster.append(m_row); ot_rep.append(o_row)
            ex_sum.append({"ID": eid, "Name": ename, "AB/": ab_c, "SL": sl_used})
            ex_det.append({"ID": eid, "Name": ename, "AB/ Dates": ", ".join(ab_dates)})
            final_sum.append({"ID": eid, "Name": ename, "P": p_c, "AB/": ab_c, "A": a_c, "H": h_c, "OT": tot_ot})

        reps = {"Attendance Muster": pd.DataFrame(muster), "OT Report": pd.DataFrame(ot_rep), "Exception Summary": pd.DataFrame(ex_sum), "Exception Detailed": pd.DataFrame(ex_det), "Miss Punch": pd.DataFrame(miss_p), "Final Summary": pd.DataFrame(final_sum)}
        
        st.markdown(f"### {report_choice}")
        st.dataframe(reps[report_choice], use_container_width=True)
        
        towrite = io.BytesIO()
        reps[report_choice].to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button("📥 Download Excel", towrite.getvalue(), f"{report_choice}.xlsx")

    except Exception as e:
        st.error(f"⚠️ Error: {str(e
