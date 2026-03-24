import streamlit as st
import requests
import os
from groq import Groq

ALPHAVANTAGE_KEY = st.secrets["ALPHAVANTAGE_KEY"]
groq_client = Groq(api_key=st.secrets["GROQ_KEY"])

def get_price(pair):
    from_currency = pair[:3]
    to_currency = pair[3:]
    url = (
        f"https://www.alphavantage.co/query"
        f"?function=CURRENCY_EXCHANGE_RATE"
        f"&from_currency={from_currency}"
        f"&to_currency={to_currency}"
        f"&apikey={ALPHAVANTAGE_KEY}"
    )
    response = requests.get(url)
    data = response.json()
    rate = data["Realtime Currency Exchange Rate"]
    return {
        "exchange_rate": float(rate["5. Exchange Rate"]),
        "bid_price": float(rate["8. Bid Price"]),
        "ask_price": float(rate["9. Ask Price"]),
        "last_refreshed": rate["6. Last Refreshed"]
    }

st.title("💹 ForexGPT")
st.subheader("AI-Powered Forex Analysis")
st.divider()

pair = st.text_input("Enter currency pair (e.g. EURUSD, GBPUSD)", value="EURUSD")

if st.button("Analyze"):
    with st.spinner("Fetching live data and analyzing..."):
        try:
            price_data = get_price(pair.upper())

            prompt = f"""
You are ForexGPT, a friendly forex analysis assistant.

Currency pair: {pair.upper()}
Current exchange rate: {price_data["exchange_rate"]}
Bid (buy) price: {price_data["bid_price"]}
Ask (sell) price: {price_data["ask_price"]}
Last updated: {price_data["last_refreshed"]}

Please provide:
1. What this currency pair means in plain English
2. What the current rate tells us
3. What the difference between bid and ask price means for a trader
4. One simple beginner tip for this pair

Keep it friendly, clear, and jargon-free. Around 150-200 words.
"""
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = response.choices[0].message.content

            st.success(f"**{pair.upper()}** — Last updated: {price_data['last_refreshed']}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Exchange Rate", price_data["exchange_rate"])
            col2.metric("Bid Price", price_data["bid_price"])
            col3.metric("Ask Price", price_data["ask_price"])
            st.divider()
            st.markdown("### 🤖 AI Analysis")
            st.write(analysis)

        except Exception as e:
            st.error("Something went wrong. Check your pair format e.g. EURUSD")