import requests
import json
import time
from datetime import datetime, timedelta


def test_webhook(side="long", tp_offset=100, sl_offset=50):
    # Ngrok URL
    webhook_url = "https://92e1-103-183-193-140.ngrok-free.app/webhook"

    # Get current BTC price (this is just an example, you might want to get real price)
    current_price = 84583.8  # Example price from your logs

    # Calculate TP and SL based on side
    if side == "long":
        tp = current_price + tp_offset
        sl = current_price - sl_offset
    else:
        tp = current_price - tp_offset
        sl = current_price + sl_offset

    # Test data
    test_data = {
        "side": side,
        "symbol": "BTCUSDT",
        "tp": tp,
        "sl": sl
    }

    try:
        print(f"\nSending {side} signal with TP: {tp}, SL: {sl}")
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    # Test long position
    test_webhook("long")

    # Wait 5 seconds before sending another signal
    time.sleep(5)

    # Test short position
    test_webhook("short")
