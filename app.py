import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. CONFIG ---
st.set_page_config(page_title="Orange House HR Master", layout="wide")

# --- 2. HELPERS ---
def parse_t(v):
    if pd.isna(v) or str(v).strip() in ['', 'nan', '00:00']: return None
    try:
        s = str(v).strip()
        if ':' in s: return datetime.strptime(s[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(s))).time()
    except: return None

def style_muster(v):
    if v in ['WO', 'H']: return 'background-color: #d4edda; color: #155724;'
    if v == 'AB/': return 'background-color: #f8d7da; color: #721c24;'
    if v == 'Miss': return 'background-color: #fff3cd; color: #856404;'
    if v == 'P (SL)': return 'background-color: #e2e3e5; color: #383d41;'
    return ''

# --- 3. ENGINE ---
def process_data(df, nh_list):
    df.columns = [str(c).strip() for c in df.columns]
    id_c, name_c = df.columns[0], df.columns[1]
    df[id_c] = df[id_c].ffill()
    df[name_c] = df[name_c].ffill()
    
    dates = [c for c in df.columns if c.replace('.0','').isdigit()]
    muster, ot_rep, summary, miss_p, ext_rep = [], [], [], [], []

    for eid in df[id_c].unique():
        if pd.isna(eid): continue
        block = df[df[id_c] == eid].reset_index(drop=True)
        ename = str(block.iloc[0][name_c])
        
        row_m, row_ot = {"ID": eid, "Name": ename}, {"ID": eid, "Name": ename}
        sl_used = False
        p_cnt, ab_cnt, tot_ot = 0, 0, 0

        for d in dates:
            d_int = int(float(d))
            t_in_raw = parse_t(block.iloc[1][d])
            t_out = parse_t(block.iloc[2][d])
            
            if d_int in nh_list:
                row_m[d], row_ot[d] = "H", 0; continue

            if (t_in_raw and not t_out) or (not t_in_raw and t_out):
                row_m[d] = "Miss"; row_ot[d] = 0; 
                miss_p.append({"ID": eid, "Name": ename, "Date": d, "In": t_in_raw, "Out": t_out})
                continue
            
            if not t_in_raw and not t_out:
                row_m[d], row_ot[d] = "A", 0; continue

            # Logic Rules
            t_in_eff = t_in_raw
            if t_in_raw >= time(13, 30): t_in_eff = time(14, 0)

            d1, d2 = datetime.combine(datetime.today(), t_in_eff), datetime.combine(datetime.today(), t_out)
            if d2 <= d1: d2 += timedelta(days=1)
            work_hrs = (d2 - d1).total_seconds() / 3600

            status = "P"
            # SL & AB/ Rules
            if t_in_raw > time(10, 16) or t_out < time(16, 0):
                if not sl_used: status = "P (SL)"; sl_used = True
                else: status = "AB/"
            
            if work_hrs <= 4.1 or t_in_raw >= time(13, 30): status = "AB/"

            # Extension Report Data
            if t_in_raw > time(9, 35) or t_out < time(18, 0):
                ext_rep.append({"ID": eid, "Name": ename, "Date": d, "In": t_in_raw, "Out": t_out, "Status": status})

            # OT Slab
            day_ot = 0
            base = 8.5 if "P" in status else 4.0
            if work_hrs > base:
                ex = work_hrs - base
                day_ot = 0.25 if ex < 2 else 0.5 if ex < 4 else 0.75 if ex < 6 else 1

            row_m[d], row_ot[d] = status, day_ot
            tot_ot += day_ot
            if "P" in status: p_cnt += 1
            elif status == "AB/": ab_cnt += 1

        muster.append(row_m); ot_rep.append(row_ot)
        summary.append({"ID": eid, "Name": ename, "P": p_cnt, "AB/": ab_cnt, "OT": tot_ot})

    return pd.DataFrame(muster), pd.DataFrame(ot_rep), pd.DataFrame(summary), pd.DataFrame(miss_p), pd.DataFrame(ext_rep)

# --- 4. UI ---
st.title("🍊 Orange House HR Master")
with st.sidebar:
    f = st.file_uploader("Upload Excel", type=['xlsx'])
    h = st.multiselect("Select Holidays", range(1, 32))
    nav = st.radio("Reports", ["Muster", "OT Report", "Extension", "Miss Punch", "Summary"])

if f:
    m, o, s, mp, ex = process_data(pd.read_excel(f), h)
    reps = {"Muster": m, "OT Report": o, "Summary": s, "Miss Punch": mp, "Extension": ex}
    
    df_show = reps[nav]
    st.subheader(f"📊 {nav}")
    
    if nav == "Muster":
        # applymap ki jagah naya .map() use kiya hai
        st.dataframe(df_show.style.map(style_muster), use_container_width=True)
    else:
        st.dataframe(df_show, use_container_width=True)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df_show.to_excel(writer, index=False)
    st.download_button("📥 Download Excel", buf.getvalue(), f"{nav}.xlsx")
else:
    st.info("Sidebar se file upload karein.")
