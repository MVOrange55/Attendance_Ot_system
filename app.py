import streamlit as st
import pandas as pd

# --- DIRECTORY MODULE ---
if 'profiles' not in st.session_state: st.session_state.profiles = []

st.title("👤 Employee Profile Directory")

t1, t2 = st.tabs(["➕ Add Profile", "📋 Directory / Filter / Delete"])

with t1:
    with st.form("emp_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            eid = st.text_input("Employee ID *")
            name = st.text_input("Full Name *")
            dept = st.text_input("Department")
            cont = st.text_input("Contact Number *")
        with c2:
            stat = st.selectbox("Status", ["Active", "Inactive"])
            photo = st.file_uploader("Photo Upload", type=['jpg', 'png'])
            res = st.file_uploader("Resume Upload", type=['pdf'])
        
        if st.form_submit_button("Save Profile"):
            if eid and name and cont:
                st.session_state.profiles.append({
                    "ID": eid, "Name": name, "Dept": dept, "Contact": cont, "Status": stat
                })
                st.success("Profile Saved!")
            else: st.error("Fill mandatory fields (*)")

with t2:
    if st.session_state.profiles:
        df = pd.DataFrame(st.session_state.profiles)
        
        # --- FILTER OPTION ---
        st.subheader("Filter & Delete")
        f_dept = st.multiselect("Filter by Department:", df["Dept"].unique())
        
        filtered_df = df[df["Dept"].isin(f_dept)] if f_dept else df
        st.dataframe(filtered_df, use_container_width=True)
        
        # --- DELETE OPTION ---
        st.divider()
        del_id = st.selectbox("Select Employee ID to Delete:", df["ID"].unique())
        if st.button("Delete Selected Employee"):
            st.session_state.profiles = [p for p in st.session_state.profiles if p["ID"] != del_id]
            st.warning(f"Employee {del_id} deleted!")
            st.rerun()
            
        # --- DOWNLOAD OPTION ---
        st.download_button("Download CSV", df.to_csv(index=False), "Directory.csv")
    else:
        st.info("No data in directory.")
