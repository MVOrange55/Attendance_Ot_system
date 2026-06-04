import streamlit as st
import pandas as pd
import io

# --- 1. SETTINGS ---
st.set_page_config(page_title="HR Portal", layout="wide")

# --- 2. STORAGE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'profiles' not in st.session_state: st.session_state.profiles = []

# --- 3. LOGIN UI ---
if not st.session_state.auth:
    st.title("Login")
    u = st.text_input("User ID")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "admin" and p == "orange_hr":
            st.session_state.auth = True
            st.rerun()
        else: st.error("Invalid")
else:
    # --- 4. MAIN APP ---
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("Go to:", ["Attendance", "Directory"])
    
    if app_mode == "Attendance":
        st.title("Attendance")
        file = st.file_uploader("Upload Excel", type=['xlsx'])
        if file: st.success("File Ready")
            
    else:
        st.title("Directory")
        tab1, tab2 = st.tabs(["Manual Add", "Bulk Import"])
        
        with tab1:
            with st.form("add_form"):
                eid = st.text_input("ID")
                name = st.text_input("Name")
                if st.form_submit_button("Save"):
                    st.session_state.profiles.append({'ID': eid, 'Name': name})
                    st.success("Saved")
                    
        with tab2:
            up_file = st.file_uploader("Upload CSV", type=['csv'])
            if up_file:
                if st.button("Import Data"):
                    df = pd.read_csv(up_file)
                    for _, row in df.iterrows():
                        st.session_state.profiles.append({
                            'ID': str(row.get('Employee ID', '')),
                            'Name': str(row.get('Full Name', ''))
                        })
                    st.success("Imported")
                    st.rerun()
        
        if st.session_state.profiles:
            st.dataframe(pd.DataFrame(st.session_state.profiles))
