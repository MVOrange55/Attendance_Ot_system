import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. SETTINGS & PREMIUM STYLING ---
st.set_page_config(page_title="Orange House HR | Premium Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F4F7F9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #E67E22; }
    .stSidebar { background-color: #ffffff; border-right: 1px solid #ddd; }
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #E67E22; color: white; border: none; font-weight: bold; font-size: 16px;
    }
    .stButton>button:hover { background-color: #D35400; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    h1, h2, h3 { color: #2C3E50; font-family: 'Segoe UI', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIN SECURITY ---
VALID_USER = "Orange_HR"
VALID_PWD = "Orange_Admin"

if "auth" not in st.session_state: st.session_state["auth"] = False

def login_page():
    st.markdown("<div style='text-align: center; margin-top: 50px;'>", unsafe_allow_html=True)
    st.title("🍊 Orange House HR Portal")
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u = st.text_input("Username", placeholder="Orange_HR")
        p = st.text_input("Password", type="password", placeholder="Orange_Admin")
        if st.button("LOGIN TO SYSTEM"):
            if u == VALID_USER and p == VALID_PWD:
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Invalid Username or Password")
    st.markdown("</div>", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '00:00']: return None
    try: return datetime.strptime(str(val).strip(), '%H:%M').time()
    except: return None

def get_excel_download(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- 4. MASTER ENGINE (RULES & CALCULATIONS) ---
def process_data(df):
    df.columns = [str(c).strip() for c in df.columns]
    id_col, name_col = df.columns[0], df.columns[1]
    df[id_col], df[name_col] = df[id_col].ffill(), df[name_col].ffill()
    dates = [c for c in df.columns if c.isdigit()]
    
    muster, ot_rep, ex_sum, ex_det, miss_p, half_day_list, absent_list = [], [], [], [], [], [], []

    for eid in df[id_col].unique():
        if pd.isna(eid): continue
        block = df[df[id_col] == eid].reset_index(drop=True)
        ename, emp_id = block.iloc[0][name_col], str(int(float(eid)))
        
        row_m, row_ot = {"Emp ID": emp_id, "Name": ename}, {"Emp ID": emp_id, "Name": ename}
        l_cnt, e_cnt, ab_cnt, a_cnt, p_cnt = 0, 0, 0, 0, 0
        l_dt_tm, e_dt_tm, ab_dates = [], [], []
        sl_used = "--"

        for d in dates:
            tin_raw, tout_raw = block.iloc[1][d], block.iloc[2][d]
            tin, tout = parse_t(tin_raw), parse_t(tout_raw)
            
            # Miss Punch Logic
            if (tin and not tout) or (not tin and tout):
                miss_p.append({"Emp ID": emp_id, "Name": ename, "Date": d, "Status": "Single Punch Missing"})
                row_m[d] = "Miss"; continue
            if not tin and not tout:
                a_cnt += 1; row_m[d] = "A"; row_ot[d] = 0; continue

            # Attendance Rules (9:30 Lock, 8.5hrs)
            t_calc_in = max(tin, time(9, 30))
            d1, d2 = datetime.combine(datetime.today(), t_calc_in), datetime.combine(datetime.today(), tout)
            work_hrs = (d2 - d1).total_seconds() / 3600
            req_out = d1 + timedelta(hours=8.5)
            early_min = (req_out - d2).total_seconds() / 60

            is_late = tin > time(9, 35)
            is_early = early_min > 2 

            if is_late: l_cnt += 1; l_dt_tm.append(f"{d}({tin.strftime('%H:%M')})")
            if is_early: e_cnt += 1; e_dt_tm.append(f"{d}({tout.strftime('%H:%M')})")

            if is_late or is_early:
                if sl_used == "--" and time(9, 35) < tin <= time(10, 15) and not is_early:
                    day_status, sl_used = "P (SL)", d; p_cnt += 1
                else:
                    day_status = "AB/"; ab_cnt += 1; ab_dates.append(d)
            else:
                day_status = "P"; p_cnt += 1
                if work_hrs > 8.5:
                    ex = work_hrs - 8.5
                    row_ot[d] = 0.25 if ex < 2 else 0.5 if ex < 4 else 0.75 if ex < 6 else 1
            row_m[d] = day_status

        # Add to Specific Reports
        muster.append(row_m); ot_rep.append(row_ot)
        ex_sum.append({"Emp ID": emp_id, "Name": ename, "Late": l_cnt, "Early": e_cnt, "AB/": ab_cnt, "A": a_cnt})
        ex_det.append({"Emp ID": emp_id, "Name": ename, "Late Details": ", ".join(l_dt_tm), "AB/ Dates": ", ".join(ab_dates)})
        if ab_cnt > 0: half_day_list.append({"Sr No": len(half_day_list)+1, "Emp ID": emp_id, "Name": ename, "Total Half Day": ab_cnt})
        if a_cnt > 0: absent_list.append({"Sr No": len(absent_list)+1, "Emp ID": emp_id, "Name": ename, "Total Absent": a_cnt})

    return pd.DataFrame(muster), pd.DataFrame(ot_rep), pd.DataFrame(ex_sum), pd.DataFrame(ex_det), pd.DataFrame(miss_p), pd.DataFrame(half_day_list), pd.DataFrame(absent_list)

# --- 5. MAIN UI ---
if st.session_state["auth"]:
    with st.sidebar:
        st.markdown("<h2 style='color: #E67E22;'>Navigation</h2>", unsafe_allow_html=True)
        nav = st.selectbox("Select Report", [
            "1. Attendance Muster", "2. Overtime Report", "3. Exception Summary", 
            "4. Exception Detailed", "5. Miss Punch Tracker", "6. Half Day Report", 
            "7. Absenteeism Report", "8. Attendance Summary", "9. Correction Module"
        ])
        f = st.file_uploader("Upload Excel", type=['xlsx'])
        if st.button("Logout"):
            st.session_state["auth"] = False
            st.rerun()

    if f:
        m_df, o_df, s_df, d_df, mp_df, hd_df, ab_df = process_data(pd.read_excel(f))
        
        # Dashboard Metrics
        st.title(f"📊 {nav}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Employees", len(m_df))
        c2.metric("Half Days", len(hd_df))
        c3.metric("Absents", len(ab_df))
        c4.metric("Miss Punches", len(mp_df))
        st.markdown("---")

        # Display Report
        rpt = pd.DataFrame()
        if "Muster" in nav: rpt = m_df
        elif "Overtime" in nav: rpt = o_df
        elif "Exception Summary" in nav: rpt = s_df
        elif "Exception Detailed" in nav: rpt = d_df
        elif "Miss Punch" in nav: rpt = mp_df
        elif "Half Day" in nav: rpt = hd_df
        elif "Absenteeism" in nav: rpt = ab_df
        
        st.dataframe(rpt, use_container_width=True)
        
        # Download
        st.download_button("📥 Download Excel Report", get_excel_download(rpt), f"{nav}.xlsx")
    else:
        st.info("Please upload the Biometric Excel file to generate all 9 reports.")
else:
    login_page()
