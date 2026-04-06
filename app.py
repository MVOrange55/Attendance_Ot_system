import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. SETTINGS ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    [data-testid="stSidebar"] { background-image: linear-gradient(#1e4d2b, #0a2e17); color: white; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #FF4B4B; color: white; }
    .report-lock-msg { text-align: center; padding: 50px; color: #666; border: 2px dashed #ccc; border-radius: 10px; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'data' not in st.session_state: st.session_state.data = None
if 'hols' not in st.session_state: st.session_state.hols = []
if 'corrs' not in st.session_state: st.session_state.corrs = []

# --- 3. LOGIN ---
def show_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container(border=True):
            st.title("🔐 Admin Login")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Unlock Dashboard"):
                if u == "admin" and p == "orange786":
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Galat ID ya Password hai bhai!")

# --- 4. CALCULATION CORE ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00', 'None']: return None
    try:
        s = str(v).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(s))).time()
    except: return None

def get_slab_ot(extra_hrs):
    if extra_hrs <= 0: return 0
    h, m = int(extra_hrs), round((extra_hrs - int(extra_hrs)) * 60)
    if 15 <= m < 30: return h + 0.25
    elif 30 <= m < 45: return h + 0.50
    elif 45 <= m < 60: return h + 0.75
    elif m >= 60: return h + 1.0
    return float(h)

def run_hr_engine(df, holidays, corrections):
    if df is None: return None, None, None, None
    df_c = df.copy()
    id_c, name_c = df_c.columns[0], df_c.columns[1]
    df_c[id_c], df_c[name_c] = df_c[id_c].ffill(), df_c[name_c].ffill()
    
    # Correction Transfer Logic
    for c in corrections:
        mask = df_c[id_c].astype(str).str.contains(str(c['id']))
        if any(mask):
            idx = df_c[mask].index[0]
            df_c.at[idx+1, str(c['date'])] = c['in']
            df_c.at[idx+2, str(c['date'])] = c['out']

    dates = [c for c in df_c.columns if str(c).replace('.0','').isdigit() or str(c).isdigit()]
    sundays = [1, 8, 15, 22, 29]
    m_list, s_list, o_list, ex_list = [], [], [], []

    for eid in df_c[id_c].unique():
        if pd.isna(eid): continue
        clean_id = str(int(float(eid))) if '.' in str(eid) else str(eid).replace(':', '')
        block = df_c[df_c[id_c] == eid].reset_index(drop=True)
        ename = str(block.iloc[0][name_c])
        
        row_m, row_o = {"ID": clean_id, "Name": ename}, {"ID": clean_id, "Name": ename}
        sl_used, p_c, a_c, ab_c, wo_c, h_c, tot_ot = False, 0, 0, 0, 0, 0, 0
        lates, earlys = [], []

        for d in dates:
            d_i = int(float(d))
            t_in, t_out = parse_t(block.iloc[1][d]), parse_t(block.iloc[2][d])
            status, day_ot = "", 0

            if d_i in sundays: status, wo_c = "WO", wo_c + 1
            elif d_i in holidays: status, h_c = "H", h_c + 1
            elif not t_in or not t_out: status, a_c = "A", a_c + 1
            else:
                t_eff = max(t_in, time(9, 30))
                if t_in >= time(13, 30): t_eff = time(14, 0)
                d1, d2 = datetime.combine(datetime.today(), t_eff), datetime.combine(datetime.today(), t_out)
                if d2 <= d1: d2 += timedelta(days=1)
                hrs = (d2 - d1).total_seconds() / 3600
                status = "P"
                
                if t_in > time(9, 35): lates.append(f"{d}({t_in.strftime('%H:%M')})")
                if hrs < 8.5: earlys.append(f"{d}({t_out.strftime('%H:%M')})")

                if time(9, 35) < t_in <= time(10, 16) and hrs < 8.5: status = "AB/"
                elif time(10, 16) < t_in <= time(11, 35) or (t_out < time(18, 0) and hrs < 8.5):
                    if not sl_used: status, sl_used = "P*", True
                    else: status = "AB/"
                elif t_in > time(11, 35) or hrs < 4.0: status = "AB/"

                day_ot = 0 if status == "P*" else get_slab_ot(hrs - (4.0 if status == "AB/" else 8.5))
                if "P" in status: p_c += 1
                elif status == "AB/": ab_c += 1

            if (d_i in sundays or d_i in holidays) and t_in and t_out:
                d1_s, d2_s = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
                if d2_s <= d1_s: d2_s += timedelta(days=1)
                day_ot = get_slab_ot((d2_s - d1_s).total_seconds() / 3600)

            row_m[d], row_o[d], tot_ot = status, day_ot, tot_ot + day_ot

        row_m.update({"P": p_c, "A": a_c, "AB/": ab_c, "WO": wo_c, "H": h_c})
        m_list.append(row_m)
        s_list.append({"ID": clean_id, "Name": ename, "P": p_c, "A": a_c, "AB/": ab_c, "WO": wo_c, "H": h_c, "Total OT": tot_ot})
        if lates or earlys:
            ex_list.append({"ID": clean_id, "Name": ename, "L-Days": len(lates), "Late Details": ", ".join(lates), "E-Days": len(earlys), "Early Details": ", ".join(earlys)})
        o_list.append(row_o)

    return pd.DataFrame(m_list), pd.DataFrame(s_list), pd.DataFrame(o_list), pd.DataFrame(ex_list)

# --- 5. APP ---
if not st.session_state.auth:
    show_login()
else:
    st.sidebar.title("🍊 Orange HR Menu")
    menu = st.sidebar.radio("Navigate:", ["Home / Upload", "Mark Holidays", "Punch Correction", "Attendance Muster", "Summary & OT", "Exception Report"])
    
    if st.sidebar.button("🔒 Logout"):
        st.session_state.auth = False
        st.session_state.data = None
        st.rerun()

    if menu == "Home / Upload":
        st.header("Step 1: Upload Attendance File")
        up = st.file_uploader("Excel File Upload Karein", type=['xlsx'])
        if up:
            try:
                st.session_state.data = pd.read_excel(up)
                st.success("File Sahi Se Load Ho Gayi Hai!")
            except Exception as e: st.error(f"File Error: {e}")

    elif menu == "Mark Holidays":
        st.header("Step 2: Holiday Mark Karein")
        st.
