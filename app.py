import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Orange House HR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .login-card {
        max-width: 400px; margin: auto; padding: 25px; background: white;
        border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-top: 8px solid #FF5722; text-align: center;
    }
    [data-testid="stSidebar"] { background: linear-gradient(#FF5722, #E64A19); }
    [data-testid="stSidebar"] * { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIN SYSTEM ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.header("🍊 Orange House Login")
        u = st.text_input("User Name", placeholder="Orange_Hr")
        p = st.text_input("Password", type="password", placeholder="Orange_Admin")
        if st.button("Login"):
            if u == "Orange_Hr" and p == "Orange_Admin":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Wrong User/Pass")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 3. LOGIC HELPERS ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00', '0']: return None
    try:
        s = str(v).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(1900,1,1)+timedelta(days=float(s))).time()
    except: return None

def get_ot(hrs, status, is_sp):
    v = hrs if is_sp else (max(0, hrs-4.0) if status == "AB/" else max(0, hrs-8.5))
    if v <= 0: return 0
    h, m = int(v), (v - int(v)) * 60
    rm = 0.75 if m >= 45 else (0.5 if m >= 30 else (0.25 if m >= 15 else 0))
    return h + rm

def style_m(v):
    cmap = {'WO':'#2ecc71','H':'#2ecc71','AB/':'#3498db','P (SL)':'#f1c40f','A':'#e74c3c','Miss':'#e67e22'}
    if v == 'P': return ''
    c = cmap.get(v, '')
    return f'background-color: {c}; color: {"white" if c and c!="#f1c40f" else "black"}'

# --- 4. MAIN APP ---
if st.sidebar.button("🔓 Logout"):
    st.session_state.auth = False
    st.rerun()

f = st.sidebar.file_uploader("📂 Upload Attendance Excel", type=['xlsx'])
wo_dates = [1, 8, 15, 22, 29]
h_days = st.sidebar.multiselect("📅 Select Holidays", options=list(range(1, 32)))
nav = st.sidebar.radio("📋 Select Report", ["Muster", "OT Report", "Summary"])

if f:
    try:
        df = pd.read_excel(f)
        df.columns = [str(c).strip() for c in df.columns]
        id_c, name_c = df.columns[0], df.columns[1]
        df[id_c], df[name_c] = df[id_c].ffill(), df[name_c].ffill()
        dates = [c for c in df.columns if c.replace('.0','').isdigit()]
        sd = sorted([int(float(d)) for d in dates])
        rm, ro, rf = [], [], []

        for eid in df[id_c].unique():
            if pd.isna(eid): continue
            bk = df[df[id_c] == eid].reset_index(drop=True)
            en = str(bk.iloc[0][name_c])
            in_r = bk[bk.iloc[:,2].astype(str).str.contains('In', na=False, case=False)].head(1)
            out_r = bk[bk.iloc[:,2].astype(str).str.contains('Out', na=False, case=False)].head(1)
            if in_r.empty or out_r.empty: continue

            ts, sl = {}, False
            for d in sd:
                ds = str(float(d)) if str(float(d)) in dates else str(d)
                t1, t2 = parse_t(in_r[ds].values[0]), parse_t(out_r[ds].values[0])
                if d in wo_dates: ts[d] = "WO"
                elif d in h_days: ts[d] = "H"
                elif not t1 or not t2: ts[d] = "A" if (not t1 and not t2) else "Miss"
                else:
                    d1, d2 = datetime.combine(datetime.today(),t1), datetime.combine(datetime.today(),t2)
                    if d2 <= d1: d2 += timedelta(days=1)
                    wh = (d2-d1).total_seconds()/3600
                    if t1 <= time(10,16) and wh >= 8.5: ts[d] = "P"
                    elif not sl: ts[d] = "P (SL)"; sl = True
                    else: ts[d] = "AB/"

            m, o, p, ab, tot_ot = {"ID":eid,"Name":en}, {"ID":eid,"Name":en}, 0, 0, 0
            for d in sd:
                s, ds = ts[d], (str(float(d)) if str(float(d)) in dates else str(d))
                t1, t2 = parse_t(in_r[ds].values[0]), parse_t(out_r[ds].values[0])
                dot = 0
                if t1 and t2:
                    d1, d2 = datetime.combine(datetime.today(),t1), datetime.combine(datetime.today(),t2)
                    if d2 <= d1: d2 += timedelta(days=1)
                    dot = get_ot((d2-d1).total_seconds()/3600, s, (s in ["WO","H"]))
                if s in ["P","P (SL)"]: p += 1
                elif s == "AB/": ab += 1
                m[d], o[d], tot_ot = s, dot, tot_ot + dot
            m.update({"P":p,"AB/":ab}); o["Total OT"] = tot_ot
            rm.append(m); ro.append(o); rf.append({"ID":eid,"Name":en,"P":p,"AB/":ab,"OT":tot_ot})

        reps = {"Muster": pd.DataFrame(rm), "OT Report": pd.DataFrame(ro), "Summary": pd.DataFrame(rf)}
        st.success(f"✅ Displaying: {nav}")
        if nav == "Muster": st.dataframe(reps[nav].style.map(style_m), use_container_width=True)
        else: st.dataframe(reps[nav], use_container_width=True)
        
        buf = io.BytesIO()
        reps[nav].to_excel(buf, index=False)
        st.download_button(f"📥 Download {nav}", buf.getvalue(), f"{nav}.xlsx")
    except Exception as e: st.error(f"❌ Error: {e}")
else: st.info("👈 Upload Excel file to start.")
