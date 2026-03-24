import streamlit as st
import requests

API_URL = "http://127.0.0.1:8001"

st.title("💹 ForexGPT")
st.subheader("AI-Powered Forex Analysis")

st.divider()

pair = st.text_input("Enter currency pair (e.g. EURUSD, GBPUSD)", value="EURUSD")

if st.button("Analyze"):
    with st.spinner("Fetching live data and analyzing..."):
        response = requests.post(f"{API_URL}/analyze", json={"pair": pair})
        if response.status_code == 200:
            data = response.json()
            st.success(f"**{data['pair']}** — Last updated: {data['last_refreshed']}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Exchange Rate", data["exchange_rate"])
            col2.metric("Bid Price", data["bid_price"])
            col3.metric("Ask Price", data["ask_price"])
            st.divider()
            st.markdown("### 🤖 AI Analysis")
            st.write(data["analysis"])
        else:
            st.error("Something went wrong. Check your pair format.")