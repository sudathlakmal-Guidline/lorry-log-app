import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import plotly.express as px

# Dashboard settings
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

# Google Sheets Connection (TTL=0 මගින් Cache එක නැති කරයි)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # ttl=0 මගින් සෑම විටම අලුත්ම දත්ත Google Sheet එකෙන් ලබා ගනී
    df = conn.read(worksheet="Sheet1", ttl=0)
    # සියලුම පේළි හිස් නම් හෝ දත්ත නැතිනම් පිරිසිදු කරයි
    df = df.dropna(how="all")
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
    return df

data = load_data()

st.title("🚚 Lorry Log Dashboard - DAF 7171")
st.write(f"**වත්මන් ඉන්ධන මිල / Current Fuel Price:** Rs. {LIVE_FUEL_PRICE:.2f}")

# --- Sidebar Input ---
with st.sidebar.form("input_form", clear_on_submit=True):
    st.header("නව දත්ත ඇතුළත් කරන්න (Add Data)")
    new_date = st.date_input("දිනය (Date)", datetime.date.today())
    start_km = st.number_input("ආරම්භක මීටරය (Start KM)", min_value=0)
    end_km = st.number_input("අවසාන මීටරය (End KM)", min_value=0)
    fuel_type = st.selectbox("ඉන්ධන වර්ගය (Fuel Type)", ["Petrol 92", "Petrol 95"])
    fuel_liters = st.number_input("පිරවූ ලීටර් ගණන (Liters Filled)", min_value=0.0)
    trip_details = st.text_input("ට්‍රිප් එකේ විස්තර (Trip Details)")
    
    submitted = st.form_submit_button("දත්ත සුරකින්න (Save Data)")

if submitted:
    if end_km > start_km:
        diff = end_km - start_km
        per_job_km = max(0, diff - OFFICE_DISTANCE)
        
        # අලුත් දත්ත පේළිය
        new_row = {
            "Date": new_date.strftime("%Y-%m-%d"),
            "Start_KM": int(start_km),
            "End_KM": int(end_km),
            "Difference": int(diff),
            "Per_Job_KM": int(per_job_km),
            "Fuel_Type": fuel_type,
            "Fuel_Liters": float(fuel_liters),
            "Trip_Details": str(trip_details)
        }
        
        # දැනට පවතින දත්ත සමඟ එකතු කිරීම
        updated_df = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
        
        # Google Sheet එකට Update කිරීම
        conn.update(worksheet="Sheet1", data=updated_df)
        st.sidebar.success("✅ දත්ත සාර්ථකව සුරැකුණා! (Data Saved Successfully!)")
        st.rerun()
    else:
        st.sidebar.error("❌ අවසාන මීටරය ආරම්භක මීටරයට වඩා වැඩි විය යුතුය!")

# --- Calculations & Charts ---
if not data.empty:
    # ගණනය කිරීම්
    data['Total_Fuel_Cost'] = data['Difference'] / KM_PER_LITER * LIVE_FUEL_PRICE
    data['Office_Fuel_Cost'] = (data['Difference'] > 0).astype(int) * (OFFICE_DISTANCE / KM_PER_LITER * LIVE_FUEL_PRICE)
    data['Job_Fuel_Cost'] = data['Per_Job_KM'] / KM_PER_LITER * LIVE_FUEL_PRICE

    st.header("📊 විශ්ලේෂණය (Analytics & Insights)")
    tab1, tab2, tab3 = st.tabs(["සතිපතා (Weekly)", "මාසික (Monthly)", "දත්ත ගොනුව (Full Log)"])

    with tab1:
        # අද දින සිට පසුගිය දින 7
        last_7 = data[data['Date'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
        if not last_7.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("සතිපතා දුර (Weekly KM)", f"{last_7['Difference'].sum():.1f} KM")
            c2.metric("සතිපතා වියදම (Weekly Cost)", f"Rs. {last_7['Total_Fuel_Cost'].sum():,.2f}")
            c3.metric("ට්‍රිප් ගණන (Trips)", len(last_7))
            
            fig_week = px.pie(values=[last_7['Job_Fuel_Cost'].sum(), last_7['Office_Fuel_Cost'].sum()], 
                              names=['Net Job Cost', 'Office Commute'], title="සතිපතා වියදම් බෙදීම")
            st.plotly_chart(fig_week)
        else:
            st.info("පසුගිය දින 7 තුළ දත්ත කිසිවක් නැත.")

    with tab2:
        # මෙම මාසයට අදාළ දත්ත
        this_month = data[data['Date'].dt.month == datetime.date.today().month]
        if not this_month.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("මාසික Job Cost", f"Rs. {this_month['Job_Fuel_Cost'].sum():,.2f}")
            c2.metric("මාසික Office Cost", f"Rs. {this_month['Office_Fuel_Cost'].sum():,.2f}")
            c3.metric("මුළු පිරිවැය (Total)", f"Rs. {this_month['Total_Fuel_Cost'].sum():,.2f}")
            
            fig_month = px.pie(values=[this_month['Job_Fuel_Cost'].sum(), this_month['Office_Fuel_Cost'].sum()], 
                               names=['Net Job Cost', 'Office Commute'], title="මාසික වියදම් බෙදීම")
            st.plotly_chart(fig_month)
        else:
            st.info("මෙම මාසය සඳහා දත්ත කිසිවක් නැත.")

    with tab3:
        # සියලුම දත්ත පෙන්වීම
        st.dataframe(data.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.warning("පද්ධතියේ තවමත් දත්ත කිසිවක් නොමැත. කරුණාකර අලුත් දත්ත පේළියක් ඇතුළත් කරන්න.")
