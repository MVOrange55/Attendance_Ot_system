import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. UI & NAVIGATION STYLING ---
st.set_page_config(page_title="Orange House HR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .login-card {
        max-width: 380px; margin: auto; padding: 25px;
        background: white; border-radius: 12px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border-top: 6px solid #FF5722; text-align: center;
    }
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#FF5722, #FF8A65);
        color: white;
    }
    [data-testid="stSidebar"] * { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIN SYSTEM ---
def show_login():
    if 'auth' not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown("<h2>🍊 Orange House</h2><p>HR Admin Access</p>", unsafe_allow_html=True)
            u = st.text_input("User Name", placeholder="Orange_Hr")
            p = st.text_input("Password", type="password", placeholder="Orange_Admin")
            if st.button("Login"):
                if u == "Orange_Hr" and p == "Orange_Admin":
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Wrong Details")
            st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

show_login()

# --- 3. HELPERS & COLORS ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00']: return None
    try:
        s = str(v).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(s))).time()
    except: return None

def get_ot(hrs, status, is_h):
    val = hrs if is_h else (max(0, hrs - 4.0) if status == "AB/" else max(0, hrs - 8.5))
    if val <= 0: return 0
    h, m = int(val), (val - int(val)) * 60
    rm = 0.75 if m >= 45 else (0.50 if m >= 30 else (0.25 if m >= 15 else 0))
    return h + rm

def style_m(v):
    c_map = {'AB/':'#3498db','P (SL)':'#f1c40f','A':'#e74c3c','Miss':'#e67e22','P':'#2ecc71','H':'#bdc3c7'}
    c = c_map.get(v, '')
    return f'background-color: {c}; color: {"white" if c and c!="#f1c40f" else "black"}'

# --- 4. MAIN APP ---
if st.sidebar.button("🔓 Logout"):
    st.session_state.auth = False
    st.rerun()

f = st.sidebar.file_uploader("📂 Upload Attendance", type=['xlsx'])
h_days = st.sidebar.multiselect("📅 Select Holidays", options=list(range(1, 32)))
nav = st.sidebar.radio("📋 Reports", ["Muster", "OT Report", "Final Summary"])

if f:
    try:
        df = pd.read_excel(f)
        df.columns = [str(c).strip() for c in df.columns]
        id_c, name_c = df.columns[0], df.columns[1]
        df[id_c], df[name_c] = df[id_c].ffill(), df[name_c].ffill()
        dates = [c for c in df.columns if c.replace('.0','').isdigit()]
        sorted_d = sorted([int(float(d)) for d in dates])

        res_m, res_o, res_f = [], [], []

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
                
                if s in ["P", "P (SL)"]: p += 1
                elif s == "AB/": ab += 1
                elif s == "A": a += 1
                r_m[d], r_o[d], tot_ot = s, dot, tot_ot + dot
            
            r_m.update({"P":p, "AB/":ab, "A":a, "H":h})
            r_o["Total OT"] = tot_ot
            res_m.append(r_m); res_o.append(r_o)
            res_f.append({"ID": eid, "Name": ename, "P": p, "AB/": ab, "A": a, "H": h, "OT": tot_ot})

        maps = {"Muster": pd.DataFrame(res_m), "OT Report": pd.DataFrame(res_o), "Final Summary": pd.DataFrame(res_f)}
        st.subheader(f"📊 Report: {nav}")
        if nav == "Muster": st.dataframe(maps[nav].style.applymap(style_m), use_container_width=True)
        else: st.dataframe(maps[nav], use_container_width=True)
        
        out = io.BytesIO()
        maps[nav].to_excel(out, index=False)
        st.download_button("📥 Download Excel", out.getvalue(), f"{nav}.xlsx")
    except Exception as e: st.error(f"Error: {e}")
else:
    st.info("👈 Sidebar se Excel file upload karein.")
