import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIG & LOGIN ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

def login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Orange House Pvt Ltd</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center;'>HR Dashboard Login</h4>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            user = st.text_input("User Name")
            pas = st.text_input("Password", type="password")
            if st.button("Login"):
                if user == "Orange_Hr" and pas == "Orange_Admin":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
        st.stop()

login()

# --- 2. HELPERS ---
def parse_time_safe(val):
    if pd.isna(val) or str(val).strip().lower() in ['', 'nan', '0', '00:00', 'none']: 
        return None
    try:
        v = str(val).strip()
        if ':' in v: return datetime.strptime(v[:5], '%H:%M').time()
        else: return (datetime(1900, 1, 1) + timedelta(days=float(v))).time()
    except: return None

def get_ot(work_hrs, status, is_h):
    # Rule: Holiday/Sunday (is_h) par Full Time OT
    if is_h: 
        ot_val = work_hrs 
    elif status == "AB/": 
        ot_val = max(0, work_hrs - 4.0)
    else: 
        ot_val = max(0, work_hrs - 8.5)
    
    if ot_val <= 0: return 0
    h = int(ot_val)
    m = (ot_val - h) * 60
    if m < 15: rm = 0
    elif m < 30: rm = 0.25
    elif m < 45: rm = 0.50
    elif m < 60: rm = 0.75
    else: h += 1; rm = 0
    return h + rm

# --- 3. UI & SIDEBAR ---
st.title("📊 Orange House HR Master System")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

uploaded_file = st.sidebar.file_uploader("1. Upload Attendance Excel", type=['xlsx'])
selected_holidays = st.sidebar.multiselect("2. Select Holidays (Full OT Days)", options=list(range(1, 32)))
report_choice = st.sidebar.selectbox("3. Navigation", ["1. Attendance Muster", "2. OT Report", "3. Exception Summary", "4. Exception Detailed", "5. Miss Punch", "6. Final Summary"])

# --- 4. PROCESSING ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [str(c).strip() for c in df.columns]
        id_col, name_col = df.columns[0], df.columns[1]
        df[id_col], df[name_col] = df[id_col].ffill(), df[name_col].ffill()
        date_cols = [c for c in df.columns if c.replace('.0','').isdigit()]

        muster, ot_rep, ex_sum, ex_det, miss_p, final_sum = [], [], [], [], [], []

        for eid in df[id_col].unique():
            if pd.isna(eid): continue
            e_data = df[df[id_col] == eid].reset_index(drop=True)
            ename, type_col = str(e_data.iloc[0][name_col]), e_data.columns[2]
            
            in_row = e_data[e_data[type_col].astype(str).str.contains('In', case=False, na=False)].head(1)
            out_row = e_data[e_data[type_col].astype(str).str.contains('Out', case=False, na=False)].head(1)
            
            if in_row.empty or out_row.empty: continue

            p_c, a_c, ab_c, h_c, tot_ot = 0, 0, 0, 0, 0
            sl_used, ab_dates = False, []
            m_row, o_row = {"ID": eid, "Name": ename}, {"ID": eid, "Name": ename}

            for d in date_cols:
                day_num = int(float(d))
                t_in, t_out = parse_time_safe(in_row[d].values[0]), parse_time_safe(out_row[d].values[0])
                is_h = day_num in selected_holidays
                status, daily_ot = "", 0

                if is_h:
                    status = "H"
                    h_c += 1
                    if t_in and t_out:
                        d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
                        if d2 <= d1: d2 += timedelta(days=1)
                        daily_ot = get_ot((d2-d1).total_seconds()/3600, status, True)
                elif not t_in and not t_out:
                    status = "A"; a_c += 1
                elif not t_in or not t_out:
                    status = "Miss"
                    miss_p.append({"ID": eid, "Name": ename, "Date": d})
                else:
                    d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
                    if d2 <= d1: d2 += timedelta(days=1)
                    work_h = (d2 - d1).total_seconds() / 3600
                    if t_in <= time(10, 16) and work_h >= 8.5:
                        status = "P"; p_c += 1
                    elif not sl_used:
                        status = "P (SL)"; sl_used = True; p_c += 1
                    else:
                        status = "AB/"; ab_c += 1; ab_dates.append(str(d))
                    daily_ot = get_ot(work_h, status, False)

                m_row[d], o_row[d] = status, daily_ot
                tot_ot += daily_ot

            m_row.update({"P": p_c, "AB/": ab_c, "A": a_c, "H": h_c})
            o_row["Total OT"] = tot_ot
            muster.append(m_row); ot_rep.append(o_row)
            ex_sum.append({"ID": eid, "Name": ename, "AB/": ab_c, "SL": sl_used})
            ex_det.append({"ID": eid, "Name": ename, "AB/ Dates": ", ".join(ab_dates)})
            final_sum.append({"ID": eid, "Name": ename, "P": p_c, "AB/": ab_c, "A": a_c, "H": h_c, "OT": tot_ot})

        reps = {"1. Attendance Muster": pd.DataFrame(muster), "2. OT Report": pd.DataFrame(ot_rep), "3. Exception Summary": pd.DataFrame(ex_sum), "4. Exception Detailed": pd.DataFrame(ex_det), "5. Miss Punch": pd.DataFrame(miss_p), "6. Final Summary": pd.DataFrame(final_sum)}
        st.subheader(report_choice)
        st.dataframe(reps[report_choice], use_container_width=True)
        
        towrite = io.BytesIO()
        reps[report_choice].to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button("📥 Download Excel", towrite.getvalue(), f"{report_choice}.xlsx")

    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")
