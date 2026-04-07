import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Orange House HR Portal", layout="wide", page_icon="🍊")

# --- 2. ENGINE FUNCTIONS ---
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
    if 15 <= m < 30: slab = 0.25
    elif 30 <= m < 45: slab = 0.50
    elif 45 <= m < 60: slab = 0.75
    elif m >= 60: h += 1; slab = 0.0
    else: slab = 0.0
    return float(h + slab)

def run_hr_engine(df, holidays, corrections):
    if df is None: return None, None, None, None, None
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
    sundays = [1, 8, 15, 22, 29] 
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
                res_mi.append({"ID": clean_id, "Name": ename, "Date": d_i, "In": t_in.strftime('%H:%M') if t_in else "", "Out": t_out.strftime('%H:%M') if t_out else "", "Status": "Single Punch"})
            else:
                d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
                if d2 <= d1: d2 += timedelta(days=1)
                actual_duration = (d2 - d1).total_seconds() / 3600

                if is_off_day:
                    # RULE 4: Off Day (Full OT)
                    status = "WO" if d_i in sundays else "H"
                    day_ot = get_slab_ot(actual_duration)
                    if d_i in sundays: wo_c += 1 
                    else: h_c += 1
                else:
                    # RULE 3: 1:30 PM Entry
                    if t_in >= time(13, 30):
                        t_start = time(14, 0)
                        d_start = datetime.combine(datetime.today(), t_start)
                        if d2 > d_start:
                            work_hrs = (d2 - d_start).total_seconds() / 3600
                            day_ot = get_slab_ot(work_hrs - 4.0) if work_hrs > 4.0 else 0.0
                        else: day_ot = 0.0
                        status = "AB/"
                    else:
                        # RULE 1 & 2: Morning/Late Joiners
                        t_start = max(t_in, time(9, 30))
                        d_start = datetime.combine(datetime.today(), t_start)
                        work_hrs = (d2 - d_start).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 8.5) if work_hrs > 8.5 else 0.0
                        
                        # Attendance Logic
                        if actual_duration < 4.0: status = "AB/"
                        elif t_in > time(10, 16) or t_out < time(16, 0):
                            if not sl_used and actual_duration >= 6.0: status, sl_used = "P*", True
                            else: status = "AB/"
                        else: status = "P"

                    # Late In / Early Out Logs (Sirf Working Days pe)
                    if t_in > time(9, 35): late_log.append(f"({t_in.strftime('%H:%M')} - {d_i})")
                    if t_out < time(18, 0): early_log.append(f"({t_out.strftime('%H:%M')} - {d_i})")

                    if status in ["P", "P*"]: p_c += 1
                    elif status == "AB/": ab_c += 0.5

            row_m[str(d_i)], row_o[str(d_i)] = status, day_ot
            tot_ot += day_ot

        row_m.update({"P": p_c, "A": a_c, "AB/": ab_c, "WO": wo_c, "H": h_c})
        row_o["Grand Total OT"] = tot_ot
        res_m.append(row_m); res_s.append({"ID": clean_id, "Name": ename, "P": p_c, "A": a_c, "AB/": ab_c, "WO": wo_c, "H": h_c, "Total OT": tot_ot}); res_o.append(row_o)
        res_ex.append({"Emp ID": clean_id, "Name": ename, "Late In": ", ".join(late_log), "Early Out": ", ".join(early_log)})
    
    return pd.DataFrame(res_m), pd.DataFrame(res_s), pd.DataFrame(res_o), pd.DataFrame(res_ex), pd.DataFrame(res_mi)

# --- 3. SESSION STATES ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'corrs' not in st.session_state: st.session_state.corrs = []

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color: #f97316;'>Orange House HR Portal</h1>", unsafe_allow_html=True)
    u = st.text_input("User ID"); p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "admin" and p == "orange786": st.session_state.auth = True; st.rerun()
        else: st.error("Wrong Password!")
else:
    st.sidebar.title("🍊 Orange HR")
    file = st.sidebar.file_uploader("Upload Excel", type=['xlsx'])
    hols = st.sidebar.multiselect("Select Holidays (Dates):", range(1, 32))
    menu = st.sidebar.selectbox("Navigation", ["📊 Muster", "📈 Summary", "💰 OT Report", "⚠️ Late/Early Log", "❌ Miss Punch", "🛠️ Correction"])
    
    if file:
        df_in = pd.read_excel(file)
        m, s, o, ex, mi = run_hr_engine(df_in, hols, st.session_state.corrs)
        st.markdown(f"### {menu}")
        if menu == "📊 Muster": st.dataframe(m, use_container_width=True)
        elif menu == "📈 Attendance Summary": st.dataframe(s, use_container_width=True)
        elif menu == "💰 OT Report": st.dataframe(o, use_container_width=True)
        elif menu == "⚠️ Late/Early Log": st.dataframe(ex, use_container_width=True)
        elif menu == "❌ Miss Punch": st.dataframe(mi, use_container_width=True)
        elif menu == "🛠️ Miss Punch Correction":
            with st.form("corr_form"):
                c1, c2 = st.columns(2); cid = c1.text_input("Emp ID"); cdt = c2.number_input("Date", 1, 31)
                cin = c1.text_input("New IN (HH:MM)"); cout = c2.text_input("New OUT (HH:MM)")
                if st.form_submit_button("Update"):
                    st.session_state.corrs.append({'id': cid, 'date': int(cdt), 'in': cin, 'out': cout}); st.rerun()
