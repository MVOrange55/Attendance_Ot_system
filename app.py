import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. UI & LOGIN ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .login-box {
        max-width: 400px; margin: auto; padding: 2rem;
        background: white; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-top: 8px solid #FF5722; margin-top: 50px;
        text-align: center;
    }
    [data-testid="stSidebar"] { background: linear-gradient(#FF5722, #E64A19); }
    [data-testid="stSidebar"] * { color: white !important; }
    </style>
""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
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

# --- 2. LOGIC HELPERS ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00', '0']: return None
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

# YAHAN FIXED HAI: 'applymap' ki jagah ab 'map' use kiya hai
def style_m(v):
    c_map = {'AB/':'#3498db','P (SL)':'#f1c40f','A':'#e74c3c','Miss':'#e67e22','P':'#2ecc71','H':'#bdc3c7'}
    c = c_map.get(v, '')
    return f'background-color: {c}; color: {"white" if c and c!="#f1c40f" else "black"}'

# --- 3. MAIN APP ---
st.sidebar.title("🛠️ HR Admin Panel")
if st.sidebar.button("🔓 Logout"):
    st.session_state.auth = False
    st.rerun()

f = st.sidebar.file_uploader("📂 Upload Attendance Excel", type=['xlsx'])
h_days = st.sidebar.multiselect("📅 Select Holiday Dates", options=list(range(1, 32)))
nav = st.sidebar.radio("📋 Select Report to View", 
                      ["Muster (Attendance)", "OT Report", "Final Summary", "Exception Summary", "Miss Punch List"])

if f:
    try:
        df = pd.read_excel(f)
        df.columns = [str(c).strip() for c in df.columns]
        id_c, name_c = df.columns[0], df.columns[1]
        df[id_c], df[name_c] = df[id_c].ffill(), df[name_c].ffill()
        
        dates = [c for c in df.columns if c.replace('.0','').isdigit()]
        sorted_d = sorted([int(float(d)) for d in dates])

        res_m, res_o, res_f, res_ex, res_mp = [], [], [], [], []

        for eid in df[id_c].unique():
            if pd.isna(eid): continue
            block = df[df[id_c] == eid].reset_index(drop=True)
            ename = str(block.iloc[0][name_c])
            type_col = block.columns[2]
            
            in_r = block[block[type_col].astype(str).str.contains('In', na=False, case=False)].head(1)
            out_r = block[block[type_col].astype(str).str.contains('Out', na=False, case=False)].head(1)
            
            if in_r.empty or out_r.empty: continue

            temp_s, sl_done = {}, False
            for d in sorted_d:
                ds = str(float(d)) if str(float(d)) in dates else str(d)
                t1, t2 = parse_t(in_r[ds].values[0]), parse_t(out_r[ds].values[0])
                
                if d in h_days: temp_s[d] = "WAIT_H"
                elif not t1 or not t2:
                    temp_s[d] = "A" if (not t1 and not t2) else "Miss"
                    if temp_s[d] == "Miss": res_mp.append({"ID": eid, "Name": ename, "Date": d})
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
            res_f.append({"ID": eid, "Name": ename, "P": p, "AB/": ab, "A": a, "H": h, "Total OT": tot_ot})
            res_ex.append({"ID": eid, "Name": ename, "AB/ Count": ab, "SL Used": "Yes" if sl_done else "No"})

        # YAHAN FIXED HAI: Ab 'applymap' ki jagah 'map' use ho raha hai
        reports = {
            "Muster (Attendance)": pd.DataFrame(res_m),
            "OT Report": pd.DataFrame(res_o),
            "Final Summary": pd.DataFrame(res_f),
            "Exception Summary": pd.DataFrame(res_ex),
            "Miss Punch List": pd.DataFrame(res_mp)
        }

        st.success(f"✅ Displaying: {nav}")
        current_df = reports[nav]
        
        if nav == "Muster (Attendance)":
            st.dataframe(current_df.style.map(style_m), use_container_width=True)
        else:
            st.dataframe(current_df, use_container_width=True)
        
        out = io.BytesIO()
        current_df.to_excel(out, index=False)
        st.download_button(f"📥 Download {nav}", out.getvalue(), f"{nav}.xlsx")

    except Exception as e:
        st.error(f"❌ Data Processing Error: {str(e)}")
else:
    st.info("👈 Please upload the Excel file in the sidebar to start.")
