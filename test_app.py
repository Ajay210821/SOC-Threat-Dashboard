import streamlit as st

st.set_page_config(page_title="SOC Dashboard Test", layout="wide")

st.title("SOC THREAT DASHBOARD")
st.success("Dashboard rendering works!")
st.metric("Total Alerts", 4)
st.write("If you can see this, Streamlit is working.")
