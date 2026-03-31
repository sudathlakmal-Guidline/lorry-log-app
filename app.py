import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import requests

st.set_page_config(page_title="Lorry Logistics Dashboard", layout="wide")

# --- සජීවීව ඉන්ධන මිල ලබා ගැනීම (Live Fuel Price) ---
@st.cache_data(ttl=3600)  # පැයකට වරක් මිල පරීක්ෂා කරයි
def get_live_fuel_price():
    try:
        # ශ්‍රී ලංකාවේ ඉන්ධන මිල පෙන්වන විශ්වාසවන්ත API එකක් භාවිතා කිරීම
        response = requests.get("https://api.ceypetco.gov.lk/prices") # උදාහරණ API එකක්
        if response.status_code == 200:
            prices = response.json()
            # මෙහිදී Petrol 92 මිල තෝරා ගනී (API එකේ ආකෘතිය අනුව මෙය වෙනස් විය හැක)
            return float(prices['petrol_92'])
    except:
        return 310.0  # API එක වැඩ නොකළහොත් පෙරනිමි මිල (Default) භාවිතා වේ

LIVE_FUEL_PRICE = get_live_fuel_price()

st.title("🚚 Lorry Log Dashboard - DAF 7171")
st.info(f"වත්මන් සජීවී පෙට්‍රල් මිල: Rs. {LIVE_FUEL_PRICE:.2f}")

# පරාමිතීන්
KM_PER_LITER = 8.0   
OFFICE_DISTANCE = 50 

# Google Sheets සම්බන්ධතාවය
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    df = conn.read(worksheet="Sheet1")
    df = df.dropna(how="all")
    df['Date'] = pd.to_datetime(df['Date'])
    return df

data = load_data()

# දත්ත ඇතුළත් කිරීමේ Sidebar
with st.sidebar.form("input_form"):
    st.header("නව දත්ත ඇතුළත් කරන්න")
    new_date = st.date_input("දිනය", datetime.date.today())
    start_km = st.number_input("ආරම්භක මීටරය", min_value=0)
    end_km = st.number_input("අවසාන මීටරය", min_value=0)
    fuel_type = st.selectbox("ඉන්ධන වර්ගය", ["Petrol 92", "Petrol 95"])
    fuel_liters = st.number_input("පිරවූ ලීටර් ගණන", min_value=0.0)
    trip_details = st.text_input("ට්‍රිප් එකේ විස්තර")
    
    submitted = st.form_submit_button("දත්ත සුරකින්න")

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
    st.sidebar.success("දත්ත ඇතුළත් කළා!")
    st.rerun()

# ගණනය කිරීම් සඳහා LIVE_FUEL_PRICE භාවිතා කිරීම
data['Total_Fuel_Cost'] = data['Difference'] / KM_PER_LITER * LIVE_FUEL_PRICE
data['Office_Fuel_Cost'] = OFFICE_DISTANCE / KM_PER_LITER * LIVE_FUEL_PRICE
data['Job_Fuel_Cost'] = data['Per_Job_KM'] / KM_PER_LITER * LIVE_FUEL_PRICE

# --- Dashboard Display ---
st.header("📊 ඉන්ධන සහ ට්‍රිප් විශ්ලේෂණය")
tab1, tab2, tab3 = st.tabs(["සතිපතා වාර්තාව", "මාසික වාර්තාව", "සම්පූර්ණ දත්ත"])

with tab1:
    last_week = data[data['Date'] > (pd.Timestamp.now() - pd.Timedelta(days=7))]
    col1, col2, col3 = st.columns(3)
    col1.metric("මුළු දුර (KM)", f"{last_week['Difference'].sum():.1f}")
    col2.metric("මුළු ඉන්ධන වියදම", f"Rs. {last_week['Total_Fuel_Cost'].sum():,.2f}")
    col3.metric("ට්‍රිප් ගණන", len(last_week))

with tab2:
    this_month = data[data['Date'].dt.month == datetime.date.today().month]
    col1, col2, col3 = st.columns(3)
    col1.metric("ට්‍රිප් වල වියදම (Net)", f"Rs. {this_month['Job_Fuel_Cost'].sum():,.2f}")
    col2.metric("කාර්යාල ගමන් වියදම", f"Rs. {this_month['Office_Fuel_Cost'].sum():,.2f}")
    col3.metric("මුළු පිරිවැය", f"Rs. {this_month['Total_Fuel_Cost'].sum():,.2f}")
