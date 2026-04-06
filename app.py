import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIGURATION & LOGIN SECURITY ---
st.set_page_config(page_title="Orange House HR Master System", layout="wide")

VALID_USERNAME = "Orange_HR"
VALID_PASSWORD = "Orange_Admin"

def check_login():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.markdown("<h2 style='text-align: center; color: #d35400;'>🍊 Orange House HR Login</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            user = st.text_input("यूजरनेम (Username):")
            pwd = st.text_input("पासवर्ड (Password):", type="password")
            if st.button("Login"):
                if user == VALID_USERNAME and pwd == VALID_PASSWORD:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("गलत यूजरनेम या पासवर्ड! कृपया सही क्रेडेंशियल डालें।")
        return False
    return True

# --- 2. CORE UTILITIES ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '00:00']: return None
    try: return datetime.strptime(str(val).strip(), '%H:%M').time()
    except: return None

def get_excel_download(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- 3. MASTER CALCULATION ENGINE (ALL RULES) ---
def process_hr_system(df, nh_list):
    df.columns = [str(c).strip() for c in df.columns]
    id_col, name_col = df.columns[0], df.columns[1]
    df[id_col] = df[id_col].ffill()
    df[name_col] = df[name_col].ffill()
    dates = [c for c in df.columns if c.isdigit()]
    
    muster, ot_rep, ex_sum, ex_det, miss_p = [], [], [], [], []

    for eid in df[id_col].unique():
        if pd.isna(eid): continue
        block = df[df[id_col] == eid].reset_index(drop=True)
        ename, emp_id = block.iloc[0][name_col], str(int(float(eid)))
        
        row_m, row_ot = {"Emp ID": emp_id, "Name": ename}, {"Emp ID": emp_id, "Name": ename}
        l_cnt, e_cnt, ab_cnt, a_cnt, p_cnt = 0, 0, 0, 0, 0
        l_dt_tm, e_dt_tm, ab_dates = [], [], []
        sl_used_date = "--"

        for d in dates:
            t_in_raw = parse_t(block.iloc[1][d])
            t_out = parse_t(block.iloc[2][d])
            
            # 1. Miss Punch Rule (Single Punch Missing)
            if (t_in_raw and not t_out):
                miss_p.append({"Emp ID": emp_id, "Name": ename, "Date": d, "In": t_in_raw.strftime('%H:%M'), "Out": "--:--", "Status": "Out Missing"})
                row_m[d] = "Miss"; continue
            if (not t_in_raw and t_out):
                miss_p.append({"Emp ID": emp_id, "Name": ename, "Date": d, "In": "--:--", "Out": t_out.strftime('%H:%M'), "Status": "In Missing"})
                row_m[d] = "Miss"; continue
            if not t_in_raw and not t_out:
                a_cnt += 1; row_m[d] = "A"; row_ot[d] = 0; continue

            # 2. 9:30 AM Hard Lock & 8.5 Hours Quota
            t_in = max(t_in_raw, time(9, 30))
            d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
            work_hrs = (d2 - d1).total_seconds() / 3600
            req_out = d1 + timedelta(hours=8.5)
            early_min = (req_out - d2).total_seconds() / 60

            is_late = t_in_raw > time(9, 35)
            is_early = early_min > 2 # 2-min grace logic
            
            if is_late: l_cnt += 1; l_dt_tm.append(f"{d}({t_in_raw.strftime('%H:%M')})")
            if is_early: e_cnt += 1; e_dt_tm.append(f"{d}({t_out.strftime('%H:%M')})")

            # 3. Short Leave (SL) vs Half Day (AB/) Rules
            day_ot = 0
            if is_late or is_early:
                # 9:35 to 10:15 SL Rule (Only once per month, and if not early out)
                if sl_used_date == "--" and time(9, 35) < t_in_raw <= time(10, 15) and not is_early:
                    day_status = "P (SL)"; sl_used_date = d; p_cnt += 1
                else:
                    day_status = "AB/"; ab_cnt += 1; ab_dates.append(d)
            else:
                day_status = "P"; p_cnt += 1
                # 4. OT Slab Logic: .25, .50, .75, 1
                if work_hrs > 8.5:
                    ex = work_hrs - 8.5
                    day_ot = 0.25 if ex < 2 else 0.5 if ex < 4 else 0.75 if ex < 6 else 1

            row_m[d], row_ot[d] = day_status, day_ot

        # Data Packing for Final Reports
        muster.append(row_m); ot_rep.append(row_ot)
        ex_sum.append({
            "Emp ID": emp_id, "Name": ename, 
            "Total Late In": l_cnt, "Total Early Out": e_cnt, 
            "SL Status": sl_used_date, "Total AB/ (Blue)": ab_cnt, "Total Absent (A)": a_cnt
        })
        ex_det.append({
            "Emp ID": emp_id, "Name": ename, 
            "Late In (Date:Time)": ", ".join(l_dt_tm), 
            "Early Out (Date:Time)": ", ".join(e_dt_tm), 
            "Final Status & AB/ Dates": f"SL Used: {sl_used_date} | AB/ Dates: {', '.join(ab_dates)}"
        })

    return pd.DataFrame(muster), pd.DataFrame(ot_rep), pd.DataFrame(ex_sum), pd.DataFrame(ex_det), pd.DataFrame(miss_p)

# --- 4. APP UI ---
if check_login():
    st.sidebar.title("🍊 Orange House HR")
    st.sidebar.info(f"User: {VALID_USERNAME}")
    
    nav = st.sidebar.selectbox("📋 रिपोर्ट का चयन करें", [
        "1. Attendance Muster", "2. Overtime (OT) Report", 
        "3. Exception Summary Report", "4. Exception Detailed Report", 
        "5. Miss Punch Report", "6. Miss Punch Correction", "7. Attendance Summary"
    ])
    
    uploaded_file = st.sidebar.file_uploader("बायोमेट्रिक एक्सेल फाइल अपलोड करें", type=['xlsx'])
    nh_days = st.sidebar.multiselect("NH छुट्टियां चुनें", range(1, 32))

    if uploaded_file:
        m_df, o_df, s_df, d_df, mp_df = process_hr_system(pd.read_excel(uploaded_file), nh_days)
        
        # Display selection
        active_df = pd.DataFrame()
        if "1." in nav: active_df = m_df
        elif "2." in nav: active_df = o_df
        elif "3." in nav: active_df = s_df
        elif "4." in nav: active_df = d_df
        elif "5." in nav: active_df = mp_df
        elif "7." in nav: active_df = s_df # Summary shared view
        
        st.subheader(nav)
        if not active_df.empty:
            st.dataframe(active_df, use_container_width=True)
            
            # --- DOWNLOAD BUTTONS ---
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                excel_bin = get_excel_download(active_df)
                st.download_button(label="📥 Download as EXCEL", data=excel_bin, file_name=f"{nav}.xlsx")
            with col2:
                st.button("📄 Download as PDF (Coming Soon)")
        else:
            st.warning("इस रिपोर्ट के लिए कोई डेटा उपलब्ध नहीं है।")

    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()
