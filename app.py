from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = FastAPI()

ALPHAVANTAGE_KEY = os.getenv("ALPHAVANTAGE_KEY")
groq_client = Groq(api_key=os.getenv("GROQ_KEY"))

account = {
    "balance": 10000.00,
    "trades": []
}

class Trade(BaseModel):
    pair: str
    action: str
    amount: float

class AnalyzeRequest(BaseModel):
    pair: str

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
        "bid_price":     float(rate["8. Bid Price"]),
        "ask_price":     float(rate["9. Ask Price"]),
        "last_refreshed": rate["6. Last Refreshed"]
    }

@app.get("/")
def home():
    return {"message": "ForexGPT backend is running!"}

@app.get("/account")
def get_account():
    return account

@app.post("/trade")
def place_trade(trade: Trade):
    price_data = get_price(trade.pair)
    price = price_data["exchange_rate"]
    if trade.amount > account["balance"]:
        return {"error": "Not enough balance!"}
    account["balance"] -= trade.amount
    new_trade = {
        "pair": trade.pair,
        "action": trade.action,
        "amount": trade.amount,
        "open_price": price,
        "profit_loss": 0.0
    }
    account["trades"].append(new_trade)
    return {
        "message": f"{trade.action.upper()} trade placed!",
        "pair": trade.pair,
        "amount": trade.amount,
        "price": price,
        "remaining_balance": account["balance"]
    }

@app.get("/positions")
def get_positions():
    results = []
    for trade in account["trades"]:
        price_data = get_price(trade["pair"])
        current_price = price_data["exchange_rate"]
        if trade["action"] == "buy":
            pl = (current_price - trade["open_price"]) * trade["amount"]
        else:
            pl = (trade["open_price"] - current_price) * trade["amount"]
        results.append({
            "pair": trade["pair"],
            "action": trade["action"],
            "amount": trade["amount"],
            "open_price": trade["open_price"],
            "current_price": current_price,
            "profit_loss": round(pl, 2)
        })
    return results

@app.post("/analyze")
def analyze_pair(request: AnalyzeRequest):
    pair = request.pair.upper()
    try:
        price_data = get_price(pair)
    except Exception:
        return {"error": f"Could not fetch price for {pair}. Use format like EURUSD"}
    prompt = f"""
You are ForexGPT, a friendly forex analysis assistant.

Currency pair: {pair}
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
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return {
        "pair": pair,
        "exchange_rate": price_data["exchange_rate"],
        "bid_price": price_data["bid_price"],
        "ask_price": price_data["ask_price"],
        "last_refreshed": price_data["last_refreshed"],
        "analysis": response.choices[0].message.content
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
    