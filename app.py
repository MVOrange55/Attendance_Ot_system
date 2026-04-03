import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

st.set_page_config(page_title="Orange House HR Automation", layout="wide")

# --- Custom Styling ---
st.markdown("""
    <style>
    .report-header { font-size: 24px; font-weight: bold; text-align: center; color: #FF4B4B; margin-bottom: 0px; }
    .report-title { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 20px; text-decoration: underline; }
    table { width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Time Parsing Logic ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() == '' or str(val).lower() == 'nan': return None
    try:
        if isinstance(val, time): return val
        if isinstance(val, datetime): return val.time()
        v_str = str(val).strip()
        if ':' in v_str: return datetime.strptime(v_str[:5], '%H:%M').time()
        return (datetime(1900, 1, 1) + timedelta(days=float(val))).time()
    except: return None

def get_ot_decimal(total_hrs):
    h = int(total_hrs)
    m = round((total_hrs - h) * 60)
    if m < 15: dec = 0.0
    elif m < 30: dec = 0.25
    elif m < 45: dec = 0.50
    elif m < 60: dec = 0.75
    else: h += 1; dec = 0.0
    return float(h + dec)

# --- Data Processing ---
if 'master_data' not in st.session_state:
    st.session_state.master_data = None

def process_data(df, holidays):
    df.columns = [str(c).strip().split('.')[0] for c in df.columns]
    cols = df.columns.tolist()
    eid_col, name_col = cols[0], cols[1]
    df[eid_col] = df[eid_col].ffill()
    df[name_col] = df[name_col].ffill()
    date_cols = [c for c in cols if c.isdigit() and 1 <= int(c) <= 31]
    
    results = []
    for eid in df[eid_col].unique():
        if pd.isna(eid) or "id" in str(eid).lower(): continue
        block = df[df[eid_col] == eid].reset_index(drop=True)
        if len(block) < 4: continue
        name = block.iloc[0][name_col]
        for d in date_cols:
            day_num = int(d)
            st_val = str(block.iloc[0][d]).strip().upper()
            in_t, out_t = parse_t(block.iloc[1][d]), parse_t(block.iloc[2][d])
            try: dur = float(block.iloc[3][d]) * 24 if pd.notna(block.iloc[3][d]) else 0
            except: dur = 0
            is_h = (day_num in holidays) or any(x in st_val for x in ['WO', 'WOP', 'W'])
            results.append({
                "Emp ID": eid, "Name": name, "Date": day_num, "In": in_t, "Out": out_t, 
                "Status": st_val if st_val != "NAN" else "", "Duration": dur, "Is_Holiday": is_h
            })
    return pd.DataFrame(results)

# --- Sidebar Controls ---
with st.sidebar:
    st.title("🍊 Orange House Admin")
    u_file = st.file_uploader("Upload Excel File", type=['xlsx'])
    h_days = st.multiselect("Select Holidays:", range(1, 32))
    st.markdown("---")
    # All reports in one navigation
    page = st.selectbox("📂 Reports Navigation:", [
        "📋 Muster Report (Monthly)", 
        "📊 Attendance Summary", 
        "⚠️ Exception Report", 
        "💰 OT Report (Decimal)",
        "🕒 Late In Report", 
        "🏃 Early Out Report", 
        "🌓 Half Day Report", 
        "🚫 Continuous Absenteeism", 
        "📉 Late Penalty Report", 
        "🛠️ Edit Miss Punch"
    ])

if u_file and st.session_state.master_data is None:
    df_raw = pd.read_excel(u_file, header=1)
    st.session_state.master_data = process_data(df_raw, h_days)

if st.session_state.master_data is not None:
    df = st.session_state.master_data.copy()
    
    # Core Logic for Calculation
    def apply_rules(row):
        in_t, out_t, dur = row['In'], row['Out'], row['Duration']
        res = {"Final_Status": "A", "Late": 0, "Early": 0, "OT": 0.0, "Is_Miss": False, "Half_Day": False}
        if (in_t and not out_t) or (not in_t and out_t): res["Is_Miss"] = True
        elif in_t and out_t:
            if in_t > time(9, 35): res["Late"] = 1
            if dur < 8.5 and not row['Is_Holiday']: res["Early"] = 1
            # OT Calc
            raw_ot = dur if row['Is_Holiday'] else (max(0, dur - 4.0) if in_t >= time(10, 16) else max(0, dur - 8.5))
            res["OT"] = get_ot_decimal(raw_ot)
            # Status
            if 3.5 <= dur <= 5.0: res["Half_Day"] = True; res["Final_Status"] = "HD"
            elif row['Is_Holiday']: res["Final_Status"] = row['Status'] if row['Status'] else "WO"
            elif in_t >= time(10, 16): res["Final_Status"] = "AB/"
            else: res["Final_Status"] = "P"
        else: res["Final_Status"] = row['Status'] if row['Is_Holiday'] else "A"
        return pd.Series(res)

    f_df = pd.concat([df, df.apply(apply_rules, axis=1)], axis=1)

    def show_header(title):
        st.markdown(f'<p class="report-header">Orange House Pvt Ltd.</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="report-title">{title}</p>', unsafe_allow_html=True)

    # --- Pages Management ---
    if page == "📋 Muster Report (Monthly)":
        show_header("Attendance Muster Report")
        st.table(f_df.pivot(index=["Emp ID", "Name"], columns="Date", values="Final_Status"))

    elif page == "📊 Attendance Summary":
        show_header("Attendance Summary")
        summary = f_df.groupby(["Emp ID", "Name"]).agg(
            Working_Days=('Final_Status', lambda x: (x == 'P').sum() + (x == 'HD').sum()*0.5),
            Present=('Final_Status', lambda x: (x == 'P').sum()),
            Absent=('Final_Status', lambda x: (x == 'A').sum()),
            Late_Count=('Late', 'sum'),
            Early_Out=('Early', 'sum')
        ).reset_index()
        st.table(summary)

    elif page == "⚠️ Exception Report":
        show_header("Exception Report")
        excep = f_df.groupby(["Emp ID", "Name"]).agg(
            Late=('Late', 'sum'), Early_Out=('Early', 'sum'),
            Miss_Punch=('Is_Miss', 'sum'), Absents=('Final_Status', lambda x: (x == 'A').sum())
        ).reset_index()
        st.table(excep)

    elif page == "💰 OT Report (Decimal)":
        show_header("Monthly OT Report (Decimal Slabs)")
        ot_p = f_df.pivot(index=["Emp ID", "Name"], columns="Date", values="OT")
        ot_p["Total OT"] = ot_p.sum(axis=1)
        st.dataframe(ot_p.style.format("{:.2f}"))

    elif page == "🕒 Late In Report":
        show_header("Late In Report")
        st.table(f_df[f_df["Late"] > 0][["Emp ID", "Name", "Date", "In"]])

    elif page == "🏃 Early Out Report":
        show_header("Early Out Report")
        st.table(f_df[f_df["Early"] > 0][["Emp ID", "Name", "Date", "Out", "Duration"]])

    elif page == "🌓 Half Day Report":
        show_header("Half Day Report")
        st.table(f_df[f_df["Half_Day"] == True][["Emp ID", "Name", "Date", "Duration"]])

    elif page == "🚫 Continuous Absenteeism":
        show_header("Continuous Absenteeism Report (3+ Days)")
        # Simple logic to show multiple absents
        absents = f_df[f_df["Final_Status"] == "A"].groupby(["Emp ID", "Name"]).size().reset_index(name='Total_Absents')
        st.table(absents[absents['Total_Absents'] >= 3])

    elif page == "📉 Late Penalty Report":
        show_header("Late Penalty Report")
        st.table(f_df.groupby(["Emp ID", "Name"]).agg(Late_Count=('Late', 'sum')).reset_index())

    elif page == "🛠️ Edit Miss Punch":
        st.header("Correction Panel")
        miss_df = f_df[f_df["Is_Miss"] == True]
        if miss_df.empty: st.success("No Miss Punches found!")
        for idx, r in miss_df.iterrows():
            with st.expander(f"Fix {r['Name']} - Day {r['Date']}"):
                c1, c2 = st.columns(2)
                ni = c1.text_input("In Time", "09:30", key=f"i{idx}")
                no = c2.text_input("Out Time", "18:30", key=f"o{idx}")
                if st.button("Update", key=f"b{idx}"):
                    ti, to = datetime.strptime(ni, '%H:%M').time(), datetime.strptime(no, '%H:%M').time()
                    st.session_state.master_data.at[idx, 'In'], st.session_state.master_data.at[idx, 'Out'] = ti, to
                    st.session_state.master_data.at[idx, 'Duration'] = (datetime.combine(datetime.today(), to) - datetime.combine(datetime.today(), ti)).total_seconds() / 3600
                    st.rerun()

else:
    st.info("👈 Excel file upload kijiye aur sidebar se report select kijiye.")
