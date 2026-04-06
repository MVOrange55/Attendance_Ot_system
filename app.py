import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIG ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")
st.title("📊 Orange House HR Master System")

# --- 2. HELPERS ---
def parse_time_safe(val):
    if pd.isna(val) or str(val).strip().lower() in ['', 'nan', '0', '00:00', 'none', 'null']: 
        return None
    try:
        v = str(val).strip()
        if ':' in v: return datetime.strptime(v[:5], '%H:%M').time()
        else: return (datetime(1900, 1, 1) + timedelta(days=float(v))).time()
    except: return None

def get_ot(work_hrs, status, is_h):
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

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.header("Settings")
uploaded_file = st.sidebar.file_uploader("1. Upload Excel", type=['xlsx'])

# Holiday Selection Option (Yahan se aap dates select kar sakte hain)
selected_holidays = st.sidebar.multiselect(
    "2. Select Holidays/Sundays for this Month",
    options=list(range(1, 32)),
    default=[]
)

report_choice = st.sidebar.selectbox("3. Navigation (Select Report)", 
    ["1. Attendance Muster", "2. OT Report", "3. Exception Summary", "4. Exception Detailed", "5. Miss Punch", "6. Final Summary"])

# --- 4. PROCESSING ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [str(c).strip() for c in df.columns]
        id_col, name_col = df.columns[0], df.columns[1]
        df[id_col], df[name_col] = df[id_col].ffill(), df[name_col].ffill()
        date_cols = [c for c in df.columns if c.replace('.0','').isdigit()]
        
        if not date_cols:
            st.error("❌ Excel mein Dates (1, 2, 3...) nahi mili.")
            st.stop()

        muster, ot_rep, ex_sum, ex_det, miss_list, final_sum = [], [], [], [], [], []

        for eid in df[id_col].unique():
            if pd.isna(eid): continue
            e_data = df[df[id_col] == eid].reset_index(drop=True)
            ename, type_col = str(e_data.iloc[0][name_col]), e_data.columns[2]
            in_row = e_data[e_data[type_col].astype(str).str.contains('In', case=False, na=False)].head(1)
            out_row = e_data[e_data[type_col].astype(str).str.contains('Out', case=False, na=False)].head(1)
            if in_row.empty or out_row.empty: continue

            p_c, a_c, ab_c, h_c, tot_ot = 0, 0, 0, 0, 0
            sl_used, ab_dates, late_logs = False, [], []
            m_row, o_row = {"ID": eid, "Name": ename}, {"ID": eid, "Name": ename}

            for d in date_cols:
                day_idx = int(float(d))
                t_in = parse_time_safe(in_row[d].values[0])
                t_out = parse_time_safe(out_row[d].values[0])
                
                # Check if this date is a selected holiday
                is_h = day_idx in selected_holidays

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
                    miss_list.append({"ID": eid, "Name": ename, "Date": d, "Issue": "Single Punch"})
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
                        late_logs.append(f"{d}({t_in.strftime('%H:%M')})")
                    daily_ot = get_ot(work_h, status, False)

                m_row[d], o_row[d] = status, daily_ot
                tot_ot += daily_ot

            m_row.update({"P": p_c, "AB/": ab_c, "A": a_c, "H": h_c})
            o_row["Total OT"] = tot_ot
            muster.append(m_row); ot_rep.append(o_row)
            ex_sum.append({"ID": eid, "Name": ename, "AB/ Count": ab_c, "SL Taken": "Yes" if sl_used else "No"})
            ex_det.append({"ID": eid, "Name": ename, "AB/ Dates": ", ".join(ab_dates), "Late Detail": ", ".join(late_logs)})
            final_sum.append({"ID": eid, "Name": ename, "Present": p_c, "AB/": ab_c, "Absent": a_c, "Holiday": h_c, "OT": tot_ot})

        reps = {
            "1. Attendance Muster": pd.DataFrame(muster), "2. OT Report": pd.DataFrame(ot_rep),
            "3. Exception Summary": pd.DataFrame(ex_sum), "4. Exception Detailed": pd.DataFrame(ex_det),
            "5. Miss Punch": pd.DataFrame(miss_list), "6. Final Summary": pd.DataFrame(final_sum)
        }

        st.info(f"Selected Holidays for this Month: {selected_holidays}")
        st.subheader(report_choice)
        st.dataframe(reps[report_choice], use_container_width=True)
        
        towrite = io.BytesIO()
        reps[report_choice].to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button("📥 Download Report", towrite.getvalue(), f"{report_choice}.xlsx")

    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")
else:
    st.info("👈 Sidebar se Excel upload karein aur Holidays select karein.")
