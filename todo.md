# Binance Trading Bot Build To-Do List

## Prerequisites
- Updated Pine Script with webhook alerts (e.g., `{"action": "long", "symbol": "BTCUSDT", "price": 60000}`).
- Python 3.9+ installed on your local machine.
- Binance Futures API keys generated (API Key and Secret Key).
- Git installed (optional, for version control).

## Phase 1: Setup Environment

### Create Project Directory
- Create a folder (e.g., `binance_trading_bot`).
- Navigate to it in your terminal: `cd binance_trading_bot`.

### Set Up Virtual Environment
- Run: `python -m venv venv`.
- Activate it:
  - Windows: `venv\Scripts\activate`
  - Mac/Linux: `source venv/bin/activate`

### Install Dependencies
- Install required libraries: `pip install python-binance fastapi uvicorn pandas`.
- Save dependencies: `pip freeze > requirements.txt`.

### Initialize Git (Optional)
- Run: `git init`.
- Create `.gitignore` and add `venv/`, `__pycache__/`, `*.log`, `config.json`.

## Phase 2: Core Functionality

### Create Configuration File
Create `config.json` with:
```json
{
  "binance_api_key": "your_api_key",
  "binance_secret_key": "your_secret_key",
  "webhook_port": 5000,
  "fixed_amount_usd": 100,
  "leverage": 10,
  "sl_tp_percent": 0.15,
  "default_symbol": "BTCUSDT"
}
```
Replace `your_api_key` and `your_secret_key` with your Binance Futures API credentials.

### Set Up Webhook Server
Create `main.py` and add:
```python
import json
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()
    print(f"Received signal: {data}")
    return {"status": "received"}
```
Test it locally: `uvicorn main:app --port 5000`.
Verify TradingView webhook hits it (use ngrok or local tunneling if needed).

### Connect to Binance Futures API
Update `main.py` to include Binance client:
```python
from binance.client import Client
import json
from fastapi import FastAPI, Request

app = FastAPI()

with open("config.json", "r") as f:
    config = json.load(f)

client = Client(config["binance_api_key"], config["binance_secret_key"])
client.API_URL = "https://fapi.binance.com"  # Futures API

@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()
    print(f"Received signal: {data}")
    return {"status": "received"}
```
Test API connection: Add `print(client.get_account())` and run.

## Phase 3: Trade Execution

### Implement Trade Logic
Add trade execution function in `main.py`:
```python
def execute_trade(signal):
    action = signal["action"]
    symbol = signal["symbol"]
    price = float(signal["price"])
    leverage = config["leverage"]
    amount_usd = config["fixed_amount_usd"]
    sl_tp_percent = config["sl_tp_percent"]

    # Set leverage
    client.futures_change_leverage(symbol=symbol, leverage=leverage)

    # Calculate quantity
    quantity = (amount_usd * leverage) / price

    # Place market order
    if action == "long":
        order = client.futures_create_order(
            symbol=symbol, side="BUY", type="MARKET", quantity=quantity
        )
        print(f"Long order placed: {order}")
    elif action == "short":
        order = client.futures_create_order(
            symbol=symbol, side="SELL", type="MARKET", quantity=quantity
        )
        print(f"Short order placed: {order}")
```
Integrate with webhook: Call `execute_trade(data)` in the `@app.post` function.

### Add SL/TP Logic
Extend `execute_trade` to set SL/TP:
```python
def execute_trade(signal):
    action = signal["action"]
    symbol = signal["symbol"]
    price = float(signal["price"])
    leverage = config["leverage"]
    amount_usd = config["fixed_amount_usd"]
    sl_tp_percent = config["sl_tp_percent"]

    client.futures_change_leverage(symbol=symbol, leverage=leverage)
    quantity = (amount_usd * leverage) / price

    if action == "long":
        order = client.futures_create_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantity)
        tp_price = price * (1 + sl_tp_percent / 100)
        sl_price = price * (1 - sl_tp_percent / 100)
        client.futures_create_order(symbol=symbol, side="SELL", type="TAKE_PROFIT_MARKET", stopPrice=tp_price, quantity=quantity)
        client.futures_create_order(symbol=symbol, side="SELL", type="STOP_MARKET", stopPrice=sl_price, quantity=quantity)
        print(f"Long: Entry={price}, TP={tp_price}, SL={sl_price}")
    elif action == "short":
        order = client.futures_create_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantity)
        tp_price = price * (1 - sl_tp_percent / 100)
        sl_price = price * (1 + sl_tp_percent / 100)
        client.futures_create_order(symbol=symbol, side="BUY", type="TAKE_PROFIT_MARKET", stopPrice=tp_price, quantity=quantity)
        client.futures_create_order(symbol=symbol, side="BUY", type="STOP_MARKET", stopPrice=sl_price, quantity=quantity)
        print(f"Short: Entry={price}, TP={tp_price}, SL={sl_price}")
```

### Add Position Tracking
Add a simple dictionary to track positions:
```python
positions = {}

def execute_trade(signal):
    action = signal["action"]
    symbol = signal["symbol"]
    # ... (existing code) ...

    if symbol in positions and positions[symbol] != action:
        # Close opposite position
        client.futures_create_order(
            symbol=symbol, side="SELL" if positions[symbol] == "long" else "BUY",
            type="MARKET", quantity=quantity, reduceOnly=True
        )
        print(f"Closed opposite position for {symbol}")
    positions[symbol] = action
```

## Phase 4: Risk Management and Logging

### Add Funds Check
Before trade execution, verify funds:
```python
def execute_trade(signal):
    account = client.futures_account()
    available_balance = float(account["availableBalance"])
    if available_balance < config["fixed_amount_usd"]:
        print("Insufficient funds!")
        return
    # ... (existing code) ...
```

### Enhance Logging
Use Python's logging module:
```python
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# Replace print() with logger.info()
logger.info(f"Received signal: {data}")
```
Add file handler (optional): `logging.FileHandler("trades.log")`.

## Phase 5: Backtesting

### Fetch Historical Data
Add a backtesting script (`backtest.py`):
```python
from binance.client import Client
import pandas as pd

with open("config.json", "r") as f:
    config = json.load(f)

client = Client(config["binance_api_key"], config["binance_secret_key"])
klines = client.futures_historical_klines("BTCUSDT", "1h", "1 month ago UTC")
df = pd.DataFrame(klines, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignored"])
df["close"] = df["close"].astype(float)
df.to_csv("btc_data.csv", index=False)
```

### Simulate Trades
Add basic simulation logic:
```python
def simulate_trades(df):
    balance = 1000  # Starting balance
    leverage = config["leverage"]
    amount_usd = config["fixed_amount_usd"]
    sl_tp_percent = config["sl_tp_percent"]

    for i in range(1, len(df)):
        price = df["close"].iloc[i]
        # Simulate your strategy signals here (simplified)
        if i > 21 and df["close"].iloc[i-1] < df["close"].iloc[i]:  # Dummy signal
            qty = (amount_usd * leverage) / price
            tp = price * (1 + sl_tp_percent / 100)
            sl = price * (1 - sl_tp_percent / 100)
            next_price = df["close"].iloc[i+1]
            if next_price >= tp:
                balance += amount_usd * leverage * (sl_tp_percent / 100)
            elif next_price <= sl:
                balance -= amount_usd * leverage * (sl_tp_percent / 100)
    print(f"Final balance: ${balance}")
simulate_trades(df)
```
Refine by implementing your full strategy logic (EMA, RSI, MACD, etc.).

## Phase 6: Testing and Deployment

### Test on Binance Futures Testnet
- Switch to testnet: `client.API_URL = "https://testnet.binancefuture.com"`.
- Use testnet API keys.
- Send test signals from TradingView and verify trades.

### Run Locally
- Start bot: `uvicorn main:app --port 5000`.
- Monitor console output for trades and errors.

### Document Usage
- Create `README.md` with setup instructions, config details, and start command. 