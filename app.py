import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Orange House HR Master", layout="wide", page_icon="🍊")

st.markdown("""
    <style>
    .main { background-color: #fff9f0; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #ffedd5; border-radius: 5px; padding: 10px; color: #9a3412;
    }
    .stTabs [aria-selected="true"] { background-color: #fb923c !important; color: white !important; }
    div[data-testid="stSidebarNav"] { background-image: linear-gradient(#fed7aa, #fff9f0); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE CORE FUNCTIONS (LOCKED) ---
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
    df_w = df.copy()
    id_c, name_c = df_w.columns[0], df_w.columns[1]
    df_w[id_c], df_w[name_c] = df_w[id_c].ffill(), df_w[name_c].ffill()
    
    # APPLY CORRECTIONS (Update & Transfer Logic)
    for c in corrections:
        mask = df_w[id_c].astype(str).str.contains(str(c['id']))
        if any(mask):
            idx = df_w[mask].index[0]
            df_w.at[idx+1, str(c['date'])] = c['in']
            df_w.at[idx+2, str(c['date'])] = c['out']

    dates = [c for c in df_w.columns if str(c).replace('.0','').strip().isdigit()]
    sundays = [1, 8, 15, 22, 29] # Adjust as per month
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

            if d_i in sundays: status, wo_c = "WO", wo_c + 1
            elif d_i in holidays: status, h_c = "H", h_c + 1
            elif (t_in and not t_out) or (not t_in and t_out):
                status, a_c = "A", a_c + 1
                res_mi.append({"ID": clean_id, "Name": ename, "Date": d_i, "In": t_in.strftime('%H:%M') if t_in else "", "Out": t_out.strftime('%H:%M') if t_out else "", "Status": "Missing Punch"})
            elif not t_in and not t_out:
                status, a_c = "A", a_c + 1
            else:
                d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
                if d2 <= d1: d2 += timedelta(days=1)
                actual_hrs = (d2 - d1).total_seconds() / 3600
                
                # Effective Time (1:30 PM Rule)
                t_eff_start = time(14, 0) if t_in >= time(13, 30) else max(t_in, time(9, 30))
                d1_eff, d2_eff = datetime.combine(datetime.today(), t_eff_start), datetime.combine(datetime.today(), t_out)
                if d2_eff <= d1_eff: d2_eff += timedelta(days=1)
                eff_hrs = (d2_eff - d1_eff).total_seconds() / 3600
                
                status = "P"
                if actual_hrs < 4.0: status = "AB/"
                elif t_in > time(10, 16) or t_out < time(16, 0) or (time(9,30)<t_in<=time(10,16) and actual_hrs<8.5):
                    if not sl_used and actual_hrs >= 6.0: status, sl_used = "P*", True
                    else: status = "AB/"

                if status == "P": day_ot = get_slab_ot(eff_hrs - 8.5)
                elif status == "AB/": day_ot = get_slab_ot(eff_hrs - 4.0) if eff_hrs > 4.0 else 0.0

                if t_in > time(9, 35): late_log.append(f"({t_in.strftime('%H:%M')} - {d_i})")
                if (status == "P" and t_out < time(18, 0)) or (status == "P*" and t_out < time(16, 0)):
                    early_log.append(f"({t_out.strftime('%H:%M')} - {d_i})")

                if "P" in status: p_c += 1
                elif status == "AB/": ab_c += 0.5

            row_m[str(d_i)], row_o[str(d_i)] = status, day_ot
            tot_ot += day_ot

        row_m.update({"P": p_c, "A": a_c, "AB/": ab_c, "WO": wo_c, "H": h_c})
        row_o["Grand Total OT"] = tot_ot
        res_m.append(row_m); res_o.append(row_o)
        res_s.append({"ID": clean_id, "Name": ename, "P": p_c, "A": a_c, "AB/": ab_c, "WO": wo_c, "H": h_c, "Total OT": tot_ot})
        res_ex.append({"Emp ID": clean_id, "Name": ename, "Late In (Total)": len(late_log), "Late In (Times-Dates)": ", ".join(late_log), "Early Out (Total)": len(early_log), "Early Out (Times-Dates)": ", ".join(early_log)})

    return pd.DataFrame(res_m), pd.DataFrame(res_s), pd.DataFrame(res_o), pd.DataFrame(res_ex), pd.DataFrame(res_mi)

# --- 3. SESSION STATES ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'data' not in st.session_state: st.session_state.data = None
if 'corrs' not in st.session_state: st.session_state.corrs = []
if 'hols' not in st.session_state: st.session_state.hols = []

# --- 4. UI COMPONENTS ---
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: #f97316;'>🍊 Orange House Login</h1>", unsafe_allow_html=True)
        u = st.text_input("User ID")
        p = st.text_input("Password", type="password")
        if st.button("Access Dashboard"):
            if u == "admin" and p == "orange786":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Invalid Credentials")

# --- 5. MAIN APP ---
if not st.session_state.auth:
    login_page()
else:
    st.sidebar.markdown("<h2 style='color: #f97316;'>Navigation</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("Select Section", ["📤 Data Upload", "🛠️ Punch Correction", "📊 Reports Dashboard"])
    
    if st.sidebar.button("Logout"):
        st.session_state.auth = False
        st.rerun()

    if menu == "📤 Data Upload":
        st.header("Step 1: Upload Excel & Set Holidays")
        file = st.file_uploader("Select Biometric File", type=['xlsx'])
        if file: st.session_state.data = pd.read_excel(file)
        st.session_state.hols = st.multiselect("Select Monthly Holidays:", range(1, 32), default=st.session_state.hols)

    elif menu == "🛠️ Punch Correction":
        st.header("✍️ Miss Punch Correction Panel")
        with st.form("corr_form"):
            c1, c2 = st.columns(2)
            cid = c1.text_input("Employee ID")
            cdt = c2.number_input("Date (1-31)", 1, 31)
            cin = c1.text_input("Correct IN (e.g., 09:30)")
            cout = c2.text_input("Correct OUT (e.g., 18:30)")
            if st.form_submit_button("Update & Transfer to Reports"):
                if cid and cin and cout:
                    st.session_state.corrs.append({'id': cid, 'date': int(cdt), 'in': cin, 'out': cout})
                    st.success(f"Correction for ID {cid} Locked!")
                else: st.warning("Please fill all fields.")
        if st.session_state.corrs:
            st.subheader("Correction Log")
            st.dataframe(pd.DataFrame(st.session_state.corrs))

    elif menu == "📊 Reports Dashboard":
        if st.session_state.data is not None:
            m, s, o, ex, mi = run_hr_engine(st.session_state.data, st.session_state.hols, st.session_state.corrs)
            tabs = st.tabs(["📊 Muster", "📈 Summary", "💰 OT Slab", "⚠️ Late/Early", "❌ Miss Punch"])
            with tabs[0]: st.subheader("1. Attendance Master Master"); st.dataframe(m)
            with tabs[1]: st.subheader("2. Monthly Payroll Summary"); st.dataframe(s)
            with tabs[2]: st.subheader("3. Overtime Slab Report"); st.dataframe(o)
            with tabs[3]: st.subheader("4. Late In & Early Out Detail"); st.dataframe(ex)
            with tabs[4]: st.subheader("5. Miss Punch List (Single Punch)"); st.dataframe(mi)
        else:
            st.warning("Please upload a file first.")
            
