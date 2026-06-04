import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Orange House HR Portal", layout="wide", page_icon="🍊")

# --- 2. ENGINE FUNCTIONS (ORIGINAL - NO CHANGES) ---
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
    if 15 <= m < 27: slab = 0.00
    elif 29 <= m < 43: slab = 0.50
    elif 44 <= m < 57: slab = 0.75
    elif 59 <= m < 60: slab = 1.0
    elif m >= 60: h += 1; slab = 0.0
    else: slab = 0.0
    return float(h + slab)

def run_hr_engine(df, holidays, corrections):
    if df is None or df.empty: return None, None, None, None, None
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
    sundays = [3, 10, 17, 24 ] 
    res_m, res_s, res_o, res_ex, res_mi = [], [], [], [], []

    for eid in df_w[id_c].unique():
        if pd.isna(eid): continue
        clean_id = str(int(float(eid))) if '.' in str(eid) else str(eid).replace(':', '')
        block = df_w[df_w[id_c] == eid].reset_index(drop=True)
        ename = str(block.iloc[0][name_c])
        
        row_m, row_o = {"ID": clean_id, "Name": ename}, {"ID": clean_id, "Name": ename}
        sl_used, p_c, a_c, ab_c, wo_c, h_c, tot_ot = False, 0, 0, 0, 0, 0.0
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
                m_type = "Out Missing" if t_in else "In Missing"
                res_mi.append({"ID": clean_id, "Name": ename, "Date": d_i, "In": t_in.strftime('%H:%M') if t_in else "", "Out": t_out.strftime('%H:%M') if t_out else "", "Status": m_type})
            else:
                d1, d2 = datetime.combine(datetime.today(), t_in), datetime.combine(datetime.today(), t_out)
                if d2 <= d1: d2 += timedelta(days=1)
                actual_dur = (d2 - d1).total_seconds() / 3600

                if is_off_day:
                    status = "WO" if d_i in sundays else "H"
                    day_ot = get_slab_ot(actual_dur)
                    if d_i in sundays: wo_c += 1 
                    else: h_c += 1
                else:
                    if t_in >= time(13, 30):
                        t_start = time(14, 0)
                        d_start = datetime.combine(datetime.today(), t_start)
                        work_hrs = (d2 - d_start).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 4.0) if work_hrs > 4.0 else 0.0
                        status = "AB/"
                        if work_hrs < 4.0:
                            early_log.append(f"{t_out.strftime('%H:%M')} (Dt:{d_i})")
                    else:
                        t_start_calc = max(t_in, time(9, 30))
                        d_start_calc = datetime.combine(datetime.today(), t_start_calc)
                        work_hrs = (d2 - d_start_calc).total_seconds() / 3600
                        day_ot = get_slab_ot(work_hrs - 8.5) if work_hrs > 8.5 else 0.0
                        
                        if actual_dur < 4.0: status = "AB/"
                        elif t_in > time(10, 16) or t_out < time(16, 0):
                            if not sl_used and actual_dur >= 6.0: status, sl_used = "P*", True
                            else: status = "AB/"
                        else: status = "P"

                        if t_in > time(9, 35): 
                            late_log.append(f"{t_in.strftime('%H:%M')} (Dt:{d_i})")
                        
                        if work_hrs < 8.5:
                            early_log.append(f"{t_out.strftime('%H:%M')} (Dt:{d_i})")

                    if status in ["P", "P*"]: p_c += 1
                    elif status == "AB/": ab_c += 0.5

            row_m[str(d_i)], row_o[str(d_i)] = status, day_ot
            tot_ot += day_ot

        res_m.append(row_m)
        res_s.append({
            "Emp ID": clean_id, "Name": ename, 
            "Present (P)": p_c, "Absent (A)": a_c, "Half Day (AB/)": ab_c, 
            "Holiday (H)": h_c, "Weekly Off (WO)": wo_c, 
            "Total OT Hours": tot_ot, "Payable Days": (p_c + ab_c + wo_c + h_c)
        })
        row_o["Total OT Hours"] = tot_ot
        res_o.append(row_o)
        res_ex.append({
            "Emp ID": clean_id, "Name": ename, 
            "Late Days": len(late_log), "Late In Detail": " | ".join(late_log),
            "Early Out Days": len(early_log), "Early Out Detail ( < 8.5h )": " | ".join(early_log)
        })
    
    return pd.DataFrame(res_m), pd.DataFrame(res_s), pd.DataFrame(res_o), pd.DataFrame(res_ex), pd.DataFrame(res_mi)

# --- PROFILE EXPORT HELPERS ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Employee Directory')
    return output.getvalue()

def to_html_for_pdf(df):
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 10px; }}
            th, td {{ border: 1px solid #dddddd; text-align: left; padding: 6px; white-space: nowrap; }}
            th {{ background-color: #f97316; color: white; font-weight: bold; }}
            h2 {{ color: #f97316; font-family: Arial, sans-serif; }}
        </style>
    </head>
    <body>
        <h2>Orange House - Employee Profile Directory</h2>
        <p>Generated on: {datetime.today().strftime('%Y-%m-%d %H:%M')}</p>
        <div style="overflow-x: auto;">
            {df.to_html(index=False)}
        </div>
