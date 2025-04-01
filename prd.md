# Binance Trading Bot Specification (Updated)

## Overview
The Binance Trading Bot will integrate with TradingView to execute futures trades on Binance based on signals from your "EMA-RSI-MACD Crossover Strategy" (Pine Script v6.0). It will use market orders, support multiple leverage levels (1x, 5x, 10x, 20x, 50x), and include fixed position sizing with stop-loss (SL) and take-profit (TP) levels set at 0.1% to 0.2% price changes. The bot will run locally, log to the console, and include a basic backtesting feature for safety.

## Functional Requirements

### 1. Integration with TradingView
- **Signal Source**: Receive Buy (Long) and Sell (Short) signals from your TradingView strategy via webhooks.
- **Webhook Payload**: Expect JSON data with at least:
  ```json
  {"action": "long", "symbol": "BTCUSDT", "price": 60000}
  {"action": "short", "symbol": "BTCUSDT", "price": 60000}
  ```
- **Strategy Modifications**: Update your Pine Script to send webhook alerts (ignoring visualization elements). Example:
  ```pinescript
  if (longSignal)
      alert("{\"action\": \"long\", \"symbol\": \"" + syminfo.ticker + "\", \"price\": " + str.tostring(close) + "}", alert.freq_once_per_bar)
  if (shortSignal)
      alert("{\"action\": \"short\", \"symbol\": \"" + syminfo.ticker + "\", \"price\": " + str.tostring(close) + "}", alert.freq_once_per_bar)
  ```

### 2. Binance API Integration (Futures)
- **Authentication**: Use Binance Futures API keys (API Key and Secret Key).
- **Market Data**: Fetch real-time price for signal validation and SL/TP calculation.
- **Trade Execution**:
  - Futures trading only (perpetual contracts).
  - Support leverage levels: 1x, 5x, 10x, 20x, 50x (configurable).
  - Place market orders immediately upon signal receipt.
- **Position Management**:
  - Track open positions per symbol to avoid duplicate entries.
  - Close positions when SL/TP is hit or an opposite signal is received (e.g., Short signal closes Long position).
- **Leverage Setting**: Set leverage via API before each trade based on user selection.

### 3. Signal Processing
- **Signal Validation**: Ensure signal contains action, symbol, and price; verify sufficient funds for the trade.
- **Trade Mapping**:
  - "long" → Open a Long position.
  - "short" → Open a Short position.
  - Opposite signal closes the existing position (e.g., Short closes Long).
- **SL/TP Execution**:
  - Set SL and TP as separate stop-market orders after entry:
    - Long: TP = entry * (1 + 0.001 to 0.002), SL = entry * (1 - 0.001 to 0.002).
    - Short: TP = entry * (1 - 0.001 to 0.002), SL = entry * (1 + 0.001 to 0.002).

### 4. Risk Management
- **Position Sizing**: Fixed USD amount (e.g., $100 per trade, configurable).
  - Calculate quantity: (fixed_amount * leverage) / entry_price.
- **SL/TP Range**: Configurable between 0.1% and 0.2% (e.g., default 0.15%).
- **Leverage**: User selects from 1x, 5x, 10x, 20x, 50x via config file.
- **Funds Check**: Verify account balance supports the trade size with leverage.

### 5. Logging and Monitoring
- **Console Logging**: Log all actions to the console:
  ```
  Signal received: [2025-04-01 12:00:00] Received: {"action": "long", "symbol": "BTCUSDT", "price": 60000}
  Trade executed: [2025-04-01 12:00:01] Executed: Long BTCUSDT, Qty: 0.001, Price: 60050, Leverage: 10x
  Errors: [2025-04-01 12:00:02] Error: Insufficient funds
  ```
- **File Backup**: Optionally save logs to a file (e.g., trades.log).

### 6. Configuration
Config File (e.g., config.json):
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

### 7. Backtesting (Safety Feature)
- **Data Source**: Use Binance historical futures data (e.g., via API or CSV export).
- **Simulation**:
  - Replay signals against historical data to estimate performance.
  - Simulate trades with leverage, SL/TP, and fixed sizing.
- **Output**: Report profit/loss, win rate, and max drawdown in the console.

## Technical Requirements

### 1. Programming Language and Libraries
- **Language**: Python.
- **Libraries**:
  - python-binance: For Binance Futures API.
  - FastAPI: For webhook server.
  - pandas: For backtesting data handling.
  - logging: For console/file logging.

### 2. Architecture
- **Components**:
  - Webhook Server: Listens for TradingView signals.
  - Signal Processor: Validates and maps signals to trades.
  - Trade Executor: Manages Binance API calls (leverage, orders, SL/TP).
  - Risk Manager: Enforces sizing and SL/TP.
  - Backtester: Simulates trades on historical data.
- **Flow**:
  - TradingView sends webhook → Bot processes signal.
  - Bot sets leverage → Places market order → Sets SL/TP.
  - Logs result to console.

### 3. Deployment
- **Environment**: Local machine (Windows/Mac/Linux).
- **Requirements**: Python 3.9+, internet connection, Binance API keys.

### 4. Backtesting Setup
- **Data**: Fetch 1-hour or 15-minute candle data for your symbol(s) via Binance API.
- **Logic**: Replay your strategy's signal conditions (EMA, RSI, MACD, BB, etc.) on historical data.
- **Output**: Console summary (e.g., Total Trades: 50, Win Rate: 60%, Profit: $120).

## Development Plan

### Phase 1: Setup
- Install Python and dependencies.
- Generate Binance Futures API keys and test connectivity.
- Set up TradingView webhook with modified Pine Script.

### Phase 2: Core Functionality
- Build webhook server to receive signals.
- Implement futures trade execution (market orders, leverage).
- Add SL/TP logic and console logging.

### Phase 3: Risk and Position Management
- Implement fixed position sizing with leverage.
- Add funds check and position tracking.
- Test with small trades on Binance Futures Testnet.

### Phase 4: Backtesting
- Fetch historical data via Binance API.
- Simulate trades based on strategy signals.
- Output results to console.

### Phase 5: Polish and Deploy
- Add error handling and logging enhancements.
- Document setup and usage.
- Run locally with live signals. 