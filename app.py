import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

st.set_page_config(page_title="Lorry Logistics Dashboard", layout="wide")

st.title("🚚 Lorry Log Dashboard - DAF 7171")

# පරාමිතීන් (Settings)
FUEL_PRICE = 310.0  # වත්මන් පෙට්‍රල් මිල (Rs.)
KM_PER_LITER = 8.0   # වාහනයේ සාමාන්‍ය පරිභෝජනය (LKM)
OFFICE_DISTANCE = 50 # දිනපතා අඩු කළ යුතු දුර (KM)

# Google Sheets සම්බන්ධතාවය
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    df = conn.read(worksheet="Sheet1")
    df = df.dropna(how="all")
    df['Date'] = pd.to_datetime(df['Date'])
    return df

data = load_data()

# දත්ත ඇතුළත් කිරීමේ කොටස (Sidebar)
with st.sidebar.form("input_form"):
    st.header("නව දත්ත ඇතුළත් කරන්න")
    new_date = st.date_input("දිනය", datetime.date.today())
    start_km = st.number_input("ආරම්භක මීටරය (Start KM)", min_value=0)
    end_km = st.number_input("අවසාන මීටරය (End KM)", min_value=0)
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

# --- ගණනය කිරීම් සහ Summary ---
st.header("📊 ඉන්ධන සහ ට්‍රිප් විශ්ලේෂණය")

# ගණනය කිරීම් (Calculations)
data['Total_Fuel_Cost'] = data['Difference'] / KM_PER_LITER * FUEL_PRICE
data['Office_Fuel_Cost'] = OFFICE_DISTANCE / KM_PER_LITER * FUEL_PRICE
data['Job_Fuel_Cost'] = data['Per_Job_KM'] / KM_PER_LITER * FUEL_PRICE

# ටැබ් මගින් Summary පෙන්වීම
tab1, tab2, tab3 = st.tabs(["සතිපතා වාර්තාව", "මාසික වාර්තාව", "සම්පූර්ණ දත්ත"])

with tab1:
    st.subheader("පසුගිය දින 7")
    last_week = data[data['Date'] > (pd.Timestamp.now() - pd.Timedelta(days=7))]
    col1, col2, col3 = st.columns(3)
    col1.metric("මුළු දුර (KM)", f"{last_week['Difference'].sum():.1f}")
    col2.metric("මුළු ඉන්ධන වියදම", f"Rs. {last_week['Total_Fuel_Cost'].sum():,.2f}")
    col3.metric("ට්‍රිප් ගණන", len(last_week))

with tab2:
    st.subheader("මේ මාසයේ වාර්තාව")
    this_month = data[data['Date'].dt.month == datetime.date.today().month]
    col1, col2, col3 = st.columns(3)
    col1.metric("ට්‍රිප් වල වියදම (Net)", f"Rs. {this_month['Job_Fuel_Cost'].sum():,.2f}")
    col2.metric("කාර්යාල ගමන් වියදම", f"Rs. {this_month['Office_Fuel_Cost'].sum():,.2f}")
    col3.metric("මුළු පිරිවැය", f"Rs. {this_month['Total_Fuel_Cost'].sum():,.2f}")

with tab3:
    st.dataframe(data)
    # Download Button
    csv = data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Summary Report එක Download කරන්න (CSV)",
        data=csv,
        file_name=f"Lorry_Report_{datetime.date.today()}.csv",
        mime="text/csv",
    )
