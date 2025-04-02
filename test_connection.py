from binance.client import Client
import os
from dotenv import load_dotenv


def test_connection():
    # Load environment variables
    load_dotenv()

    # Initialize Binance client
    client = Client(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_SECRET_KEY'),
        testnet=True
    )

    try:
        # Test connection by getting account information
        account = client.futures_account_balance()
        print("Connection successful!")
        print("Account balance:")
        for balance in account:
            if float(balance['balance']) > 0:
                print(f"{balance['asset']}: {balance['balance']}")

    except Exception as e:
        print(f"Connection failed: {str(e)}")


if __name__ == "__main__":
    test_connection()
