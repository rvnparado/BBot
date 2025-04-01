# Binance Futures Trading Bot

A Python-based trading bot for Binance Futures that executes trades based on webhook signals.

## Prerequisites

1. Python 3.x installed
2. Binance Futures Testnet account with API credentials
3. ngrok installed (for webhook testing)

## Setup

1. Install required Python packages:
```bash
pip install fastapi uvicorn python-binance requests
```

2. Create a `config.json` file in the root directory with your Binance API credentials:
```json
{
    "binance_api_key": "your_api_key",
    "binance_secret_key": "your_secret_key"
}
```

## Running the Bot

1. First, make sure you're in the project directory:
```bash
cd C:\Development\ReactProjects\binance
```

2. Start the FastAPI server (trading bot):
```bash
python main.py
```
This will start the server on `http://0.0.0.0:8000`

3. In a separate terminal window, start ngrok to create a public URL for your webhook:
```bash
ngrok http 8000
```
This will give you a public URL like `https://xxxx-xxx-xxx-xxx.ngrok-free.app`

4. To test the webhook, you can use the test script in another terminal window:
```bash
python test_webhook.py
```

## Troubleshooting

1. If you get a port error (10048), it means the port is already in use. You can either:
   - Find and close the existing process using the port
   - Or use a different port by modifying the last line in `main.py`:
     ```python
     uvicorn.run(app, host="0.0.0.0", port=8001)  # or any other available port
     ```

2. To monitor trades:
   - Check the console output where `main.py` is running
   - Check the `trades.log` file
   - Check your Binance Futures Testnet account

## Current Configuration

- Uses Binance Futures Testnet
- Fixed position size: $100
- Leverage: 50x
- Takes market price for entry
- Logs are saved to `trades.log`

## Webhook Signal Format

The webhook expects signals in the following format:
```json
{
    "side": "long",
    "symbol": "BTCUSDT",
    "tp": 84800,
    "sl": 82800,
    "time": "2025-4-1 14:38"
}
```

## Important Notes

1. Always make sure to kill any existing server processes before starting a new one
2. The bot uses market orders for entry and stop orders for take profit and stop loss
3. All trades are executed on the Binance Futures Testnet
4. Monitor the `trades.log` file for detailed trade execution information 