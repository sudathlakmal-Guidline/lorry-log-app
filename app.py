import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="DAF 7171 - Petrol Log", layout="centered")
st.title("🚚 Smart Transport Tracker (Petrol)")
st.subheader("Lorry No: DAF 7171")

# Google Sheets සම්බන්ධතාවය
conn = st.connection("gsheets", type=GSheetsConnection)

with st.form("driver_form", clear_on_submit=True):
    today_date = st.date_input("දිනය (Date)", date.today())
    
    col1, col2 = st.columns(2)
    with col1:
        start_km = st.number_input("ආරම්භක මීටරය (Start KM)", min_value=0)
    with col2:
        end_km = st.number_input("අවසාන මීටරය (End KM)", min_value=0)

    st.markdown("---")
    st.write("⛽ **ඉන්ධන විස්තර (Fuel Details):**")
    
    # මෙතැන Petrol වර්ග තෝරන්න දී ඇත
    fuel_type = st.selectbox("ඉන්ධන වර්ගය (Fuel Type)", ["None", "Petrol Octane 92", "Petrol Octane 95"])
    
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        fuel_liters = st.number_input("ලීටර් ගණන (Liters)", min_value=0.0, step=0.1)
    with f_col2:
        fuel_img = st.file_uploader("Fuel Meter/Bill Photo", type=['jpg', 'jpeg', 'png'])

    st.markdown("---")
    trip_details = st.text_area("ගමන් විස්තර (Trip Details)")
    
    submit = st.form_submit_button("Submit Data to Office")

if submit:
    if end_km > start_km:
        diff = end_km - start_km
        per_job_km = max(0, diff - 50) 
        
        new_row = {
            "Date": str(today_date),
            "Start_KM": start_km,
            "End_KM": end_km,
            "Difference": diff,
            "Per_Job_KM": per_job_km,
            "Fuel_Type": fuel_type if fuel_type != "None" else "",
            "Fuel_Liters": fuel_liters if fuel_liters > 0 else "",
            "Trip_Details": trip_details
        }
        
        try:
            # Sheet එක කියවා අලුත් දත්ත පේළිය එක් කිරීම
            existing_data = conn.read()
            updated_df = pd.concat([existing_data, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success("සාර්ථකයි! පෙට්‍රල් විස්තර Office එකට ලැබුණා.")
            st.balloons()
        except Exception as e:
            st.error(f"Error: {e}. කරුණාකර secrets.toml පරීක්ෂා කරන්න.")
    else:
        st.error("කරුණාකර මීටර් කියවීම් නැවත පරීක්ෂා කරන්න.")