import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import io

st.set_page_config(page_title="Final OT Fix", layout="wide")
st.title("📊 100% Fixed OT System")

def round_ot(hours):
    if hours <= 0: return 0
    full_hours = int(hours)
    rem = (hours - full_hours) * 60
    if rem < 15: rounded = 0
    elif rem < 30: rounded = 0.25
    elif rem < 45: rounded = 0.50
    elif rem < 60: rounded = 0.75
    else: 
        full_hours += 1
        rounded = 0
    return full_hours + rounded

def process_data(df):
    # खाली Rows हटाना
    df = df.dropna(how='all').reset_index(drop=True)
    
    # ID और Name को नीचे तक भरना
    df.iloc[:, 0] = df.iloc[:, 0].ffill() # Column 0: ID
    df.iloc[:, 1] = df.iloc[:, 1].ffill() # Column 1: Name
    
    # तारीख वाले कॉलम्स (जो Numbers हैं)
    date_cols = []
    for col in df.columns:
        if str(col).strip().isdigit():
            date_cols.append(col)

    results = []
    unique_ids = df.iloc[:, 0].unique()

    for eid in unique_ids:
        # एक कर्मचारी का पूरा 4-5 लाइन का ब्लॉक
        block = df[df.iloc[:, 0] == eid].reset_index(drop=True)
        
        if len(block) < 3: continue # अगर डेटा कम है तो छोड़ दो

        name = block.iloc[0, 1]
        row_data = {"Emp ID": eid, "Name": name}

        # ब्लॉक के अंदर फिक्स इंडेक्स:
        # Index 0 = Status, Index 1 = In Time, Index 2 = Out Time
        
        for day in date_cols:
            try:
                status = str(block.at[0, day]).strip().upper()
                out_val = str(block.at[2, day]).strip() # 3rd Row of block is Out Time

                # अगर Absent या खाली है
                if status == 'A' or out_val.lower() in ['nan', 'none', '']:
                    row_data[day] = 0
                    continue

                # टाइम पार्सिंग (कोशिश करें कि सही फॉर्मेट मिले)
                try:
                    # अगर एक्सेल टाइम फॉर्मेट में है
                    t_out = pd.to_datetime(out_val).time()
                except:
                    # अगर स्ट्रिंग फॉर्मेट में है
                    t_out = datetime.strptime(out_val, '%H:%M').time()

                dt_in = datetime.combine(datetime.today(), time(9, 30))
                dt_out = datetime.combine(datetime.today(), t_out)
                
                if dt_out <= dt_in: dt_out += timedelta(days=1)
                
                total_hrs = (dt_out - dt_in).total_seconds() / 3600

                if 'WO' in status:
                    ot = total_hrs
                else:
                    ot = max(0, total_hrs - 8.5)

                row_data[day] = round_ot(ot)
            except:
                row_data[day] = 0
        
        # टोटल OT जोड़ना
        row_data["Total Month OT"] = sum([v for k,v in row_data.items() if k in date_cols])
        results.append(row_data)

    return pd.DataFrame(results)

uploaded_file = st.file_uploader("Upload Excel", type=['xlsx'])

if uploaded_file:
    # फाइल लोड करना (Header=0 मतलब पहली लाइन में 1, 2, 3.. होना चाहिए)
    df = pd.read_excel(uploaded_file)
    
    if st.button("🚀 Calculate Final OT"):
        final_df = process_data(df)
        st.dataframe(final_df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False)
        st.download_button("📥 Download Report", output.getvalue(), "Final_OT.xlsx")
