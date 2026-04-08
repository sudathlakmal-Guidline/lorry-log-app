import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import plotly.express as px

# Dashboard settings - Sidebar එක සැමවිටම විවෘතව තැබීමට (Expanded)
st.set_page_config(
    page_title="Lorry Logistics Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Toolbar එක සැඟවීමට CSS
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# පරාමිතීන්
LIVE_FUEL_PRICE = 310.0 
KM_PER_LITER = 8.0   
OFFICE_DISTANCE = 50 

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    df = conn.read(worksheet="Sheet1")
    df = df.dropna(how="all")
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
    return df

data = load_data()

st.title("🚚 Lorry Log Dashboard - DAF 7171")
st.write(f"**වත්මන් ඉන්ධන මිල / Current Fuel Price:** Rs. {LIVE_FUEL_PRICE:.2f}")

# --- Sidebar Input (දැන් මෙය විවෘතව පවතිනු ඇත) ---
with st.sidebar.form("input_form"):
    st.header("නව දත්ත ඇතුළත් කරන්න (Add Data)")
    new_date = st.date_input("දිනය (Date)", datetime.date.today())
    start_km = st.number_input("ආරම්භක මීටරය (Start KM)", min_value=0)
    end_km = st.number_input("අවසාන මීටරය (End KM)", min_value=0)
    fuel_type = st.selectbox("ඉන්ධන වර්ගය (Fuel Type)", ["Petrol 92", "Petrol 95"])
    fuel_liters = st.number_input("පිරවූ ලීටර් ගණන (Liters Filled)", min_value=0.0)
    trip_details = st.text_input("ට්‍රිප් එකේ විස්තර (Trip Details)")
    
    submitted = st.form_submit_button("දත්ත සුරකින්න (Save Data)")

if submitted:
    diff = end_km - start_km
    per_job_km = max(0, diff - OFFICE_DISTANCE)
    new_row = pd.DataFrame([{"Date": new_date.strftime("%Y-%m-%d"), "Start_KM": start_km, "End_KM": end_km, "Difference": diff, "Per_Job_KM": per_job_km, "Fuel_Type": fuel_type, "Fuel_Liters": fuel_liters, "Trip_Details": trip_details}])
    updated_df = pd.concat([data, new_row], ignore_index=True)
    conn.update(worksheet="Sheet1", data=updated_df)
    st.sidebar.success("දත්ත සුරැකුණා! (Saved!)")
    st.rerun()

# --- Calculations & Charts ---
if not data.empty:
    data['Total_Fuel_Cost'] = data['Difference'] / KM_PER_LITER * LIVE_FUEL_PRICE
    data['Office_Fuel_Cost'] = (data['Difference'] > 0).astype(int) * (OFFICE_DISTANCE / KM_PER_LITER * LIVE_FUEL_PRICE)
    data['Job_Fuel_Cost'] = data['Per_Job_KM'] / KM_PER_LITER * LIVE_FUEL_PRICE

    st.header("📊 විශ්ලේෂණය (Analytics & Insights)")
    tab1, tab2, tab3 = st.tabs(["සතිපතා (Weekly)", "මාසික (Monthly)", "දත්ත ගොනුව (Full Log)"])

    with tab1:
        last_7 = data[data['Date'] > (pd.Timestamp.now() - pd.Timedelta(days=7))]
        c1, c2, c3 = st.columns(3)
        c1.metric("සතිපතා දුර (Weekly KM)", f"{last_7['Difference'].sum():.1f} KM")
        c2.metric("සතිපතා වියදම (Weekly Cost)", f"Rs. {last_7['Total_Fuel_Cost'].sum():,.2f}")
        c3.metric("ට්‍රිප් ගණන (Trips)", len(last_7))
        
        fig_week = px.pie(values=[last_7['Job_Fuel_Cost'].sum(), last_7['Office_Fuel_Cost'].sum()], 
                          names=['Job Cost', 'Office Commute'], title="සතිපතා වියදම් බෙදීම (Weekly Cost Breakdown)")
        st.plotly_chart(fig_week)

    with tab2:
        this_month = data[data['Date'].dt.month == datetime.date.today().month]
        c1, c2, c3 = st.columns(3)
        c1.metric("මාසික Job Cost", f"Rs. {this_month['Job_Fuel_Cost'].sum():,.2f}")
        c2.metric("මාසික Office Cost", f"Rs. {this_month['Office_Fuel_Cost'].sum():,.2f}")
        c3.metric("මුළු පිරිවැය (Total)", f"Rs. {this_month['Total_Fuel_Cost'].sum():,.2f}")
        
        fig_month = px.pie(values=[this_month['Job_Fuel_Cost'].sum(), this_month['Office_Fuel_Cost'].sum()], 
                           names=['Net Job Cost', 'Office Commute'], title="මාසික වියදම් බෙදීම (Monthly Cost Breakdown)")
        st.plotly_chart(fig_month)

    with tab3:
        st.dataframe(data)
