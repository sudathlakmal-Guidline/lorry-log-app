import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

st.set_page_config(page_title="Lorry Logistics Dashboard", layout="wide")

# Fuel Price & Settings
LIVE_FUEL_PRICE = 310.0 
KM_PER_LITER = 8.0   
OFFICE_DISTANCE = 50 

# Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1")
        df = df.dropna(how="all") # හිස් පේළි ඉවත් කරයි
        
        if not df.empty and 'Date' in df.columns:
            # දින ආකෘතිය නිවැරදිව පරිවර්තනය කරයි, වැරදි දත්ත ඇත්නම් ඒවා මඟහරියි
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date']) # දිනය වැරදි පේළි ඉවත් කරයි
        return df
    except Exception as e:
        st.error(f"දත්ත කියවීමේදී ගැටලුවක් පවතී: {e}")
        return pd.DataFrame()

data = load_data()

st.title("🚚 Lorry Log Dashboard - DAF 7171")
st.write(f"**වත්මන් ඉන්ධන මිල / Current Fuel Price:** Rs. {LIVE_FUEL_PRICE:.2f}")

# --- දත්ත ඇතුළත් කිරීමේ Sidebar ---
with st.sidebar.form("input_form"):
    st.header("නව දත්ත ඇතුළත් කරන්න (Add Data)")
    new_date = st.date_input("දිනය (Date)", datetime.date.today())
    start_km = st.number_input("ආරම්භක මීටරය (Start KM)", min_value=0)
    end_km = st.number_input("අවසාන මීටරය (End KM)", min_value=0)
    fuel_type = st.selectbox("ඉන්ධන වර්ගය", ["Petrol 92", "Petrol 95"])
    fuel_liters = st.number_input("පිරවූ ලීටර් ගණන", min_value=0.0)
    trip_details = st.text_input("ට්‍රිප් එකේ විස්තර")
    
    submitted = st.form_submit_button("දත්ත සුරකින්න (Save)")

if submitted:
    diff = end_km - start_km
    per_job_km = max(0, diff - OFFICE_DISTANCE)
    
    new_row = pd.DataFrame([{
        "Date": new_date.strftime("%Y-%m-%d"),
        "Start_KM": start_km,
        "End_KM": end_km,
        "Difference": diff,
        "Per_Job_KM": per_job_km,
        "Fuel_Type": fuel_type,
        "Fuel_Liters": fuel_liters,
        "Trip_Details": trip_details
    }])
    
    updated_df = pd.concat([data, new_row], ignore_index=True)
    conn.update(worksheet="Sheet1", data=updated_df)
    st.sidebar.success("දත්ත සුරැකුණා! (Saved!)")
    st.rerun()

# --- Dashboard Display ---
if not data.empty:
    data['Total_Fuel_Cost'] = data['Difference'] / KM_PER_LITER * LIVE_FUEL_PRICE
    data['Office_Fuel_Cost'] = OFFICE_DISTANCE / KM_PER_LITER * LIVE_FUEL_PRICE
    data['Job_Fuel_Cost'] = data['Per_Job_KM'] / KM_PER_LITER * LIVE_FUEL_PRICE

    st.header("📊 විශ්ලේෂණය (Analytics)")
    tab1, tab2, tab3 = st.tabs(["සතිපතා", "මාසික", "සම්පූර්ණ දත්ත"])

    with tab1:
        last_week = data[data['Date'] > (pd.Timestamp.now() - pd.Timedelta(days=7))]
        col1, col2, col3 = st.columns(3)
        col1.metric("මුළු දුර", f"{last_week['Difference'].sum():.1f} KM")
        col2.metric("වියදම", f"Rs. {last_week['Total_Fuel_Cost'].sum():,.2f}")
        col3.metric("ට්‍රිප් ගණන", len(last_week))

    with tab2:
        this_month = data[data['Date'].dt.month == datetime.date.today().month]
        col1, col2, col3 = st.columns(3)
        col1.metric("Job Cost", f"Rs. {this_month['Job_Fuel_Cost'].sum():,.2f}")
        col2.metric("Office Cost", f"Rs. {this_month['Office_Fuel_Cost'].sum():,.2f}")
        col3.metric("මුළු වියදම", f"Rs. {this_month['Total_Fuel_Cost'].sum():,.2f}")

    with tab3:
        st.dataframe(data)
else:
    st.info("පෙන්වීමට දත්ත කිසිවක් නොමැත. (No data to display.)")
