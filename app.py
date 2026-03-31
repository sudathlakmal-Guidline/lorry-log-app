import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import requests

st.set_page_config(page_title="Lorry Logistics Dashboard", layout="wide")

# --- සජීවීව ඉන්ධන මිල ලබා ගැනීම (Live Fuel Price) ---
@st.cache_data(ttl=3600)
def get_live_fuel_price():
    try:
        # Note: Replace with a working local API if available
        return 310.0 
    except:
        return 310.0

LIVE_FUEL_PRICE = get_live_fuel_price()

st.title("🚚 Lorry Log Dashboard - DAF 7171")
st.write(f"**වත්මන් සජීවී පෙට්‍රල් මිල / Current Live Petrol Price:** Rs. {LIVE_FUEL_PRICE:.2f}")

# Parameters
KM_PER_LITER = 8.0   
OFFICE_DISTANCE = 50 

# Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    df = conn.read(worksheet="Sheet1")
    df = df.dropna(how="all")
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
    return df

data = load_data()

# --- Data Input Sidebar ---
with st.sidebar.form("input_form"):
    st.header("නව දත්ත ඇතුළත් කරන්න (Add New Data)")
    new_date = st.date_input("දිනය (Date)", datetime.date.today())
    start_km = st.number_input("ආරම්භක මීටරය (Start KM Reading)", min_value=0)
    end_km = st.number_input("අවසාන මීටරය (End KM Reading)", min_value=0)
    fuel_type = st.selectbox("ඉන්ධන වර්ගය (Fuel Type)", ["Petrol 92", "Petrol 95"])
    fuel_liters = st.number_input("පිරවූ ලීටර් ගණන (Fuel Liters Filled)", min_value=0.0)
    trip_details = st.text_input("ට්‍රිප් එකේ විස්තර (Trip Details)")
    
    submitted = st.form_submit_button("දත්ත සුරකින්න (Save Data)")

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
    st.sidebar.success("දත්ත සාර්ථකව ඇතුළත් කළා! (Data Saved Successfully!)")
    st.rerun()

# --- Dashboard Calculations ---
if not data.empty:
    data['Total_Fuel_Cost'] = data['Difference'] / KM_PER_LITER * LIVE_FUEL_PRICE
    data['Office_Fuel_Cost'] = OFFICE_DISTANCE / KM_PER_LITER * LIVE_FUEL_PRICE
    data['Job_Fuel_Cost'] = data['Per_Job_KM'] / KM_PER_LITER * LIVE_FUEL_PRICE

# --- Dashboard Display ---
st.header("📊 ඉන්ධන සහ ට්‍රිප් විශ්ලේෂණය (Fuel & Trip Analytics)")

tab1, tab2, tab3 = st.tabs([
    "සතිපතා වාර්තාව (Weekly Report)", 
    "මාසික වාර්තාව (Monthly Report)", 
    "සම්පූර්ණ දත්ත (Full Data Log)"
])

if not data.empty:
    with tab1:
        st.subheader("පසුගිය දින 7 (Last 7 Days)")
        last_week = data[data['Date'] > (pd.Timestamp.now() - pd.Timedelta(days=7))]
        col1, col2, col3 = st.columns(3)
        col1.metric("මුළු දුර (Total Distance)", f"{last_week['Difference'].sum():.1f} KM")
        col2.metric("මුළු ඉන්ධන වියදම (Total Fuel Cost)", f"Rs. {last_week['Total_Fuel_Cost'].sum():,.2f}")
        col3.metric("ට්‍රිප් ගණන (No. of Trips)", len(last_week))

    with tab2:
        st.subheader("මේ මාසයේ වාර්තාව (Monthly Summary)")
        this_month = data[data['Date'].dt.month == datetime.date.today().month]
        col1, col2, col3 = st.columns(3)
        col1.metric("ට්‍රිප් වල වියදම (Net Job Cost)", f"Rs. {this_month['Job_Fuel_Cost'].sum():,.2f}")
        col2.metric("කාර්යාල ගමන් වියදම (Office Commute)", f"Rs. {this_month['Office_Fuel_Cost'].sum():,.2f}")
        col3.metric("මුළු පිරිවැය (Total Monthly Cost)", f"Rs. {this_month['Total_Fuel_Cost'].sum():,.2f}")

    with tab3:
        st.dataframe(data)
        csv = data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="වාර්තාව බාගත කරගන්න (Download Summary Report)",
            data=csv,
            file_name=f"Lorry_Report_{datetime.date.today()}.csv",
            mime="text/csv",
        )
else:
    st.warning("තවමත් දත්ත ඇතුළත් කර නොමැත. (No data available yet.)")
