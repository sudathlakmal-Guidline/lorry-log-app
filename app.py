import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Smart Transport Tracker", page_icon="🚚")

st.title("🚚 Smart Transport Tracker (Petrol)")
st.subheader("Lorry No: DAF 7171")

# Google Sheets සම්බන්ධතාවය ලබා ගැනීම
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    existing_data = conn.read(worksheet="Sheet1", usecols=[0, 1, 2, 3, 4, 5])
    existing_data = existing_data.dropna(how="all")
except Exception as e:
    st.error(f"සම්බන්ධතාවයේ දෝෂයක් පවතී: {e}")
    st.stop()

# පෝරමය (Form) සැකසීම
with st.form(key="log_form"):
    date = st.date_input("දිනය")
    meter_reading = st.number_input("මීටර් කියවීම (km)", min_value=0)
    location = st.text_input("ස්ථානය")
    petrol_liters = st.number_input("පිරවූ පෙට්‍රල් ප්‍රමාණය (Liters)", min_value=0.0)
    cost = st.number_input("පිරිවැය (Rs.)", min_value=0.0)
    remarks = st.text_area("සටහන්")
    
    submit_button = st.form_submit_button(label="දත්ත ඇතුළත් කරන්න")

if submit_button:
    if location == "":
        st.warning("කරුණාකර ස්ථානය ඇතුළත් කරන්න.")
    else:
        # අලුත් දත්ත පේළිය සැකසීම
        new_row = pd.DataFrame([{
            "Date": date.strftime("%Y-%m-%d"),
            "Meter Reading": meter_reading,
            "Location": location,
            "Liters": petrol_liters,
            "Cost": cost,
            "Remarks": remarks
        }])
        
        # පැරණි දත්ත සමඟ අලුත් දත්ත එකතු කිරීම
        updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        
        # Google Sheet එකට නැවත ලියා තැබීම
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("දත්ත සාර්ථකව ඇතුළත් කරන ලදී!")
        st.balloons()
