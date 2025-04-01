from binance.client import Client
import json
import requests


def test_futures_connection():
    # Load configuration
    with open("config.json", "r") as f:
        config = json.load(f)

    print("Testing Binance Futures Testnet Connection...")
    print(f"API Key: {config['binance_api_key'][:8]}...")

    # Initialize Binance client with testnet
    client = Client(
        api_key=config["binance_api_key"],
        api_secret=config["binance_secret_key"],
        testnet=True  # This automatically sets the correct testnet URL
    )

    try:
        # Test basic connection
        print("\n1. Testing basic connection...")
        status = client.futures_ping()
        print("✓ Basic connection successful!")

        # Get account information
        print("\n2. Getting account information...")
        account = client.futures_account()
        print("✓ Account information retrieved successfully!")
        print(f"   Total Balance: {account['totalWalletBalance']} USDT")
        print(f"   Available Balance: {account['availableBalance']} USDT")

        # Get exchange information
        print("\n3. Getting exchange information...")
        exchange_info = client.futures_exchange_info()
        print("✓ Exchange information retrieved successfully!")
        print(f"   Number of trading pairs: {len(exchange_info['symbols'])}")

        # Print BTCUSDT filters
        print("\n4. BTCUSDT Filters:")
        btc_info = next(
            s for s in exchange_info['symbols'] if s['symbol'] == 'BTCUSDT')
        for f in btc_info['filters']:
            print(f"   {f['filterType']}: {f}")

        print("\nAll tests completed successfully! ✓")
        return True

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

        if "API-key format invalid" in str(e):
            print("\nTroubleshooting tips:")
            print("1. Verify that the API key and secret are copied correctly")
            print("2. Make sure there are no extra spaces or characters")
            print("3. Try generating a new API key on the testnet")
        elif "Invalid API-key" in str(e):
            print("\nTroubleshooting tips:")
            print("1. Make sure you're using testnet API keys (not main network)")
            print("2. Check if the API key has the correct permissions")
            print("3. Verify if IP restrictions are properly set")

        return False


if __name__ == "__main__":
    test_futures_connection()
