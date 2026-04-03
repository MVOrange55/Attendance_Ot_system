import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

st.set_page_config(page_title="Admin HR Portal", layout="wide")

# --- CSS for Sidebar Styling ---
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    .stButton>button {width: 100%; border-radius: 5px; height: 3em; background-color: #f0f2f6;}
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
def parse_t(val):
    if pd.isna(val) or str(val).strip() == '' or str(val).lower() == 'nan': return None
    try:
        if isinstance(val, time): return val
        if isinstance(val, datetime): return val.time()
        val_str = str(val).strip()
        if ':' in val_str: return datetime.strptime(val_str[:5], '%H:%M').time()
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

# --- Session State for Editing ---
if 'master_data' not in st.session_state:
    st.session_state.master_data = None

# --- Main Processing ---
def process_data(df, holidays):
    df.columns = [str(c).strip().split('.')[0] for c in df.columns]
    cols = df.columns.tolist()
    eid_col, name_col = cols[0], cols[1]
    df[eid_col] = df[eid_col].ffill()
    df[name_col] = df[name_col].ffill()
    date_cols = [c for c in cols if c.isdigit() and 1 <= int(c) <= 31]
    
    results = []
    for eid in df[eid_col].unique():
        if pd.isna(eid) or str(eid).lower() == 'emp id': continue
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
                "Status": st_val, "Duration": dur, "Is_Holiday": is_h
            })
    return pd.DataFrame(results)

# --- Sidebar Navigation ---
with st.sidebar:
    st.title("⚙️ Admin Settings")
    u_file = st.file_uploader("Upload Excel", type=['xlsx'])
    h_days = st.multiselect("Select Holidays:", range(1, 32))
    
    st.markdown("---")
    st.subheader("📁 Navigation")
    page = st.radio("Go To:", ["📋 Attendance Master", "🕒 Late In Report", "🏃 Early Out Report", "💰 OT Report", "🛠️ Edit Miss Punch"])
    
    if st.session_state.master_data is not None:
        csv = st.session_state.master_data.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Final Report", csv, "HR_Final_Report.csv")

# --- Logic for File Upload ---
if u_file and st.session_state.master_data is None:
    raw_df = pd.read_excel(u_file, header=1)
    st.session_state.master_data = process_data(raw_df, h_days)

# --- Page Display Logic ---
if st.session_state.master_data is not None:
    df = st.session_state.master_data.copy()
    
    # Recalculate Logic for Late/OT/Early based on (possibly edited) data
    def apply_rules(row):
        in_t, out_t, dur = row['In'], row['Out'], row['Duration']
        res = {"Final_Status": "A", "Late": 0, "Early": 0, "OT": 0.0, "Is_Miss": False}
        
        if (in_t and not out_t) or (not in_t and out_t):
            res["Is_Miss"] = True
        elif in_t and out_t:
            if in_t > time(9, 35): res["Late"] = int((datetime.combine(datetime.today(), in_t) - datetime.combine(datetime.today(), time(9, 30))).total_seconds() / 60)
            if dur < 8.5 and not row['Is_Holiday']: res["Early"] = int((8.5 - dur) * 60)
            
            raw_ot = dur if row['Is_Holiday'] else (max(0, dur - 4.0) if in_t >= time(10, 16) else max(0, dur - 8.5))
            res["OT"] = get_ot_decimal(raw_ot)
            
            if row['Is_Holiday']: res["Final_Status"] = row['Status'] if row['Status'] else "WO"
            elif in_t >= time(10, 16): res["Final_Status"] = "AB/"
            else: res["Final_Status"] = "P"
        else:
            res["Final_Status"] = row['Status'] if row['Is_Holiday'] else "A"
        return pd.Series(res)

    rules_df = df.apply(apply_rules, axis=1)
    full_df = pd.concat([df, rules_df], axis=1)

    if page == "📋 Attendance Master":
        st.header("Attendance Master")
        st.dataframe(full_df.pivot(index=["Emp ID", "Name"], columns="Date", values="Final_Status"))

    elif page == "🕒 Late In Report":
        st.header("Late Coming Report (> 09:35)")
        st.dataframe(full_df[full_df["Late"] > 0][["Emp ID", "Name", "Date", "In", "Late"]])

    elif page == "🏃 Early Out Report":
        st.header("Early Out Report (< 8.5 hrs)")
        st.dataframe(full_df[full_df["Early"] > 0][["Emp ID", "Name", "Date", "Out", "Duration", "Early"]])

    elif page == "💰 OT Report":
        st.header("Monthly OT (Decimal Slabs)")
        ot_p = full_df.pivot(index=["Emp ID", "Name"], columns="Date", values="OT")
        ot_p["Total OT"] = ot_p.sum(axis=1)
        st.dataframe(ot_p.style.format("{:.2f}"))

    elif page == "🛠️ Edit Miss Punch":
        st.header("🛠️ Miss Punch Correction Panel")
        miss_df = full_df[full_df["Is_Miss"] == True]
        
        if not miss_df.empty:
            st.write("Niche di gayi entries mein Miss Punch hai. Inhe sahi karein:")
            for idx, row in miss_df.iterrows():
                with st.expander(f"Correction: {row['Name']} (Date: {row['Date']})"):
                    c1, c2 = st.columns(2)
                    new_in = c1.text_input(f"New In Time (HH:MM) - ID {row['Emp ID']}", value=str(row['In']) if row['In'] else "09:30")
                    new_out = c2.text_input(f"New Out Time (HH:MM) - ID {row['Emp ID']}", value=str(row['Out']) if row['Out'] else "18:30")
                    
                    if st.button(f"Update {row['Name']} - Day {row['Date']}"):
                        try:
                            # Update the main session state data
                            t_in = datetime.strptime(new_in[:5], '%H:%M').time()
                            t_out = datetime.strptime(new_out[:5], '%H:%M').time()
                            
                            # Update Duration also
                            new_dur = (datetime.combine(datetime.today(), t_out) - datetime.combine(datetime.today(), t_in)).total_seconds() / 3600
                            
                            st.session_state.master_data.at[idx, 'In'] = t_in
                            st.session_state.master_data.at[idx, 'Out'] = t_out
                            st.session_state.master_data.at[idx, 'Duration'] = new_dur
                            st.success(f"Updated! Please refresh the page.")
                            st.rerun()
                        except:
                            st.error("Format galat hai! Use HH:MM (e.g. 09:30)")
        else:
            st.success("Kamaal hai! Koi Miss Punch nahi mila.")
else:
    st.info("👈 Please upload the Excel file in the sidebar to start.")
