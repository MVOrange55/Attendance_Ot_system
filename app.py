import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIG & LOGIN ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

def check_auth():
    if 'auth' not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        st.markdown("<h2 style='text-align:center;'>🍊 Orange House Pvt Ltd</h2>", unsafe_allow_html=True)
        with st.container():
            u = st.text_input("User Name")
            p = st.text_input("Password", type="password")
            if st.button("Login"):
                if u == "Orange_Hr" and p == "Orange_Admin":
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Wrong Credentials")
        st.stop()

check_auth()

# --- 2. HELPERS ---
def parse_t(v):
    if pd.isna(v) or str(v).strip().lower() in ['', 'nan', '00:00']: return None
    try:
        s = str(v).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(s))).time()
    except: return None

def get_ot(hrs, status, is_h):
    if is_h: val = hrs
    elif status == "AB/": val = max(0, hrs - 4.0)
    else: val = max(0, hrs - 8.5)
    if val <= 0: return 0
    h = int(val)
    m = (val - h) * 60
    rm = 0.25 if m >= 15 else 0
    if m >= 30: rm = 0.50
    if m >= 45: rm = 0.75
    return h + rm

def style_m(v):
    colors = {'AB/': '#3498db', 'P (SL)': '#f1c40f', 'A': '#e74c3c', 'Miss': '#e67e22', 'P': '#2ecc71', 'H': '#bdc3c7'}
    c = colors.get(v, '')
    return f'background-color: {c}; color: {"white" if c else "black"}'

# --- 3. MAIN APP ---
st.sidebar.title("Navigation")
if st.sidebar.button("Logout"):
    st.session_state.auth = False
    st.rerun()

f = st.sidebar.file_uploader("Upload Excel", type=['xlsx'])
h_days = st.sidebar.multiselect("Select Holiday Dates", options=list(range(1, 32)))
nav = st.sidebar.radio("Reports", ["Muster", "OT Report", "Miss Punch", "Final Summary"])

if f:
    try:
        df = pd.read_excel(f)
        df.columns = [str(c).strip() for c in df.columns]
        id_c, name_c = df.columns[0], df.columns[1]
        df[id_c], df[name_c] = df[id_c].ffill(), df[name_c].ffill()
        dates = [c for c in df.columns if c.replace('.0','').isdigit()]
        sorted_d = sorted([int(float(d)) for d in dates])

        res_m, res_o, res_mp, res_f = [], [], [], []

        for eid in df[id_c].unique():
            if pd.isna(eid): continue
            block = df[df[id_c] == eid].reset_index(drop=True)
            ename = str(block.iloc[0][name_c])
            in_r = block[block.iloc[:,2].astype(str).str.contains('In', na=False)].head(1)
            out_r = block[block.iloc[:,2].astype(str).str.contains('Out', na=False)].head(1)
            
            if in_r.empty or out_r.empty: continue

            temp_s, sl_done = {}, False
            for d in sorted_d:
                ds = str(float(d)) if str(float(d)) in dates else str(d)
                t1, t2 = parse_t(in_r[ds].values[0]), parse_t(out_r[ds].values[0])
                if d in h_days: temp_s[d] = "WAIT_H"
                elif not t1 or not t2: temp_s[d] = "A" if (not t1 and not t2) else "Miss"
                else:
                    d1, d2 = datetime.combine(datetime.today(), t1), datetime.combine(datetime.today(), t2)
                    if d2 <= d1: d2 += timedelta(days=1)
                    wh = (d2-d1).total_seconds()/3600
                    if t1 <= time(10, 16) and wh >= 8.5: temp_s[d] = "P"
                    elif not sl_done: temp_s[d] = "P (SL)"; sl_done = True
                    else: temp_s[d] = "AB/"

            r_m, r_o, p, a, ab, h, tot_ot = {"ID": eid, "Name": ename}, {"ID": eid, "Name": ename}, 0, 0, 0, 0, 0
            for d in sorted_d:
                s = temp_s[d]
                if s == "WAIT_H":
                    if temp_s.get(d-1) in ["P","P (SL)","AB/"] or temp_s.get(d+1) in ["P","P (SL)","AB/"]:
                        s = "H"; h += 1
                    else: s = "A"; a += 1
                
                ds = str(float(d)) if str(float(d)) in dates else str(d)
                t1, t2 = parse_t(in_r[ds].values[0]), parse_t(out_r[ds].values[0])
                dot = 0
                if t1 and t2:
                    d1, d2 = datetime.combine(datetime.today(), t1), datetime.combine(datetime.today(), t2)
                    if d2 <= d1: d2 += timedelta(days=1)
                    dot = get_ot((d2-d1).total_seconds()/3600, s, (s=="H"))
                
                if s == "Miss": res_mp.append({"ID": eid, "Name": ename, "Date": d})
                if s in ["P", "P (SL)"]: p += 1
                elif s == "AB/": ab += 1
                elif s == "A": a += 1
                
                r_m[d], r_o[d], tot_ot = s, dot, tot_ot + dot
            
            r_m.update({"P":p, "AB/":ab, "A":a, "H":h})
            r_o["Total
