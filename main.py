import json
import logging
from fastapi import FastAPI, Request
from binance import AsyncClient
from datetime import datetime
import math
import asyncio
import sys
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging with proper encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("trades.log", mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)
logger.info("Logging system initialized")

# Initialize Binance client with testnet
client = None


async def init_client():
    global client
    client = await AsyncClient.create(
        api_key=os.getenv('BINANCE_API_KEY'),
        api_secret=os.getenv('BINANCE_SECRET_KEY'),
        testnet=False  # SHOULD BE FALSE FOR LIVE TRADES AND TRUE FOR TESTNET TRADES
    )
    return client

# Track positions
positions = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global client
    client = await init_client()
    logger.info("Trading bot started successfully!")

    yield

    # Shutdown
    if client:
        await client.close_connection()
        logger.info("Trading bot stopped successfully!")

# Initialize FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Load configuration
with open("config.json", "r") as f:
    config = json.load(f)


@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        logger.info("=" * 50)
        logger.info("Received new trading signal:")
        logger.info(f"Side: {data.get('side', 'N/A')}")
        logger.info(f"Symbol: {data.get('symbol', 'N/A')}")
        logger.info("=" * 50)

        # Validate signal data
        # Removed tp and sl from required fields
        required_fields = ["side", "symbol"]
        if not all(key in data for key in required_fields):
            error_msg = f"Invalid signal format. Required fields: {required_fields}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        # Execute trade
        await execute_trade(client, data)

        return {"status": "success", "message": "Signal processed"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


def get_symbol_info(client, symbol):
    exchange_info = client.futures_exchange_info()
    for s in exchange_info['symbols']:
        if s['symbol'] == symbol:
            return s
    return None


def round_step_size(quantity, step_size):
    precision = int(round(-math.log10(step_size)))
    return round(quantity, precision)


def round_price(price, tick_size):
    precision = int(round(-math.log10(tick_size)))
    return round(price, precision)


async def execute_trade(client, signal_data):
    try:
        side = signal_data.get('side', '').lower()
        symbol = signal_data.get('symbol', '')

        logger.info(
            f"Processing trade - Side: {side}, Symbol: {symbol}")

        # Get current market price first
        ticker = await client.futures_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        logger.info(f"Current market price: {current_price} USDT")

        # Calculate TP and SL based on current price
        risk_reward_ratio = 1  # Risk:Reward ratio (adjust as needed)
        stop_loss_percentage = 0.001  # 1% stop loss (adjust as needed)

        if side == 'long':
            sl_price = current_price * (1 - stop_loss_percentage)
            price_distance = current_price - sl_price
            tp_price = current_price + (price_distance * risk_reward_ratio)
        else:  # short
            sl_price = current_price * (1 + stop_loss_percentage)
            price_distance = sl_price - current_price
            tp_price = current_price - (price_distance * risk_reward_ratio)

        logger.info(f"Calculated TP price: {tp_price}, SL price: {sl_price}")

        # Get account balance
        account = await client.futures_account()
        balance = float([asset for asset in account['assets']
                        if asset['asset'] == 'USDT'][0]['walletBalance'])
        logger.info(f"Account balance: {balance} USDT")

        # Get symbol info for precision
        exchange_info = await client.futures_exchange_info()
        symbol_info = next(
            (s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)
        if not symbol_info:
            raise ValueError(f"Symbol {symbol} not found")

        # Get price precision from PRICE_FILTER
        price_filter = next(
            f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER')
        price_precision = int(
            round(-math.log10(float(price_filter['tickSize']))))

        # Round TP and SL prices to correct precision
        tp_price = round(tp_price, price_precision)
        sl_price = round(sl_price, price_precision)

        logger.info(f"Rounded TP price: {tp_price}, SL price: {sl_price}")

        # Get quantity precision from LOT_SIZE filter
        lot_size_filter = next(
            f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
        step_size = float(lot_size_filter['stepSize'])
        min_qty = float(lot_size_filter['minQty'])
        max_qty = float(lot_size_filter['maxQty'])

        # Calculate quantity with margin buffer
        position_size = balance * 0.90  # Use 95% of balance to leave margin buffer
        if balance < position_size:
            position_size = balance * 0.90  # Use 95% of portfolio
            logger.info(
                f"Using 95% of portfolio ({position_size} USDT) to maintain margin buffer")

        # Calculate quantity with leverage
        leverage = 50
        raw_quantity = (position_size * leverage) / current_price

        # First ensure quantity is within min/max bounds
        quantity = max(min_qty, min(max_qty, raw_quantity))

        # Then round to the nearest step size
        quantity = round(quantity / step_size) * step_size

        # Finally, ensure we have exactly 3 decimal places as per stepSize
        quantity = round(quantity, 3)

        logger.info(f"Calculated quantity: {quantity} {symbol}")

        # Set leverage
        leverage_response = await client.futures_change_leverage(symbol=symbol, leverage=leverage)
        logger.info(f"Leverage set to {leverage}x: {leverage_response}")

        # Cancel all open orders first and wait for confirmation
        try:
            await client.futures_cancel_all_open_orders(symbol=symbol)
            logger.info(f"Cancelled all open orders for {symbol}")
            # Wait for orders to be cancelled
            await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"Error cancelling open orders: {str(e)}")

        # Close any existing position first and wait for confirmation
        positions = await client.futures_position_information(symbol=symbol)
        for position in positions:
            current_position_amt = float(position['positionAmt'])
            if current_position_amt != 0:
                close_side = 'BUY' if current_position_amt < 0 else 'SELL'
                close_order = await client.futures_create_order(
                    symbol=symbol,
                    side=close_side,
                    type='MARKET',
                    quantity=abs(current_position_amt)
                )
                logger.info(
                    f"Closed existing position: {current_position_amt} {symbol}")
                # Add delay to allow balance to settle
                await asyncio.sleep(2)  # 2-second delay

        # Get updated account balance after position close
        account = await client.futures_account()
        balance = float([asset for asset in account['assets']
                        if asset['asset'] == 'USDT'][0]['walletBalance'])
        logger.info(f"Updated balance after position close: {balance} USDT")

        # Verify position is closed
        positions = await client.futures_position_information(symbol=symbol)
        current_position = next(
            (p for p in positions if p['symbol'] == symbol and float(p['positionAmt']) != 0), None)
        if current_position:
            logger.error("Failed to close existing position")
            return False

        # Open new position
        entry_side = 'BUY' if side == 'long' else 'SELL'
        exit_side = 'SELL' if side == 'long' else 'BUY'

        # Place entry order at market price
        entry_order = await client.futures_create_order(
            symbol=symbol,
            side=entry_side,
            type='MARKET',
            quantity=quantity
        )
        logger.info(
            f"{'Long' if side == 'long' else 'Short'} position opened: {entry_order}")

        # Wait for position to be opened
        await asyncio.sleep(2)

        # Get the current position to verify it's opened
        positions = await client.futures_position_information(symbol=symbol)
        current_position = next(
            (p for p in positions if p['symbol'] == symbol and float(p['positionAmt']) != 0), None)

        if not current_position:
            logger.error("Position was not opened successfully")
            return False

        # Place TP and SL orders
        try:
            # Place Take Profit order
            tp_order = await client.futures_create_order(
                symbol=symbol,
                side='SELL' if side == 'long' else 'BUY',
                type='TAKE_PROFIT_MARKET',
                stopPrice=tp_price,
                closePosition=True,
                timeInForce='GTE_GTC',
                workingType='MARK_PRICE',
                priceProtect=True
            )
            logger.info(f"Take Profit order placed: {tp_order}")

            # Place Stop Loss order
            sl_order = await client.futures_create_order(
                symbol=symbol,
                side='SELL' if side == 'long' else 'BUY',
                type='STOP_MARKET',
                stopPrice=sl_price,
                closePosition=True,
                timeInForce='GTE_GTC',
                workingType='MARK_PRICE',
                priceProtect=True
            )
            logger.info(f"Stop Loss order placed: {sl_order}")

            # Store order IDs and position info
            positions[symbol] = {
                'tp_order_id': tp_order['orderId'],
                'sl_order_id': sl_order['orderId'],
                'position_side': side,
                'quantity': quantity
            }
            logger.info(f"Position and orders stored for {symbol}")

            # Add position monitor
            @client.futures_socket_manager.on_message
            async def handle_position_update(msg):
                if msg['e'] == 'ACCOUNT_UPDATE' and symbol in positions:
                    # Check if position is closed
                    position_data = next(
                        (p for p in msg['a']['P'] if p['s'] == symbol), None)
                    if position_data and float(position_data['pa']) == 0:
                        # Position is closed, cancel any remaining orders
                        try:
                            await client.futures_cancel_all_open_orders(symbol=symbol)
                            logger.info(
                                f"Cleaned up remaining orders after position close for {symbol}")
                            del positions[symbol]
                        except Exception as e:
                            logger.error(f"Error cleaning up orders: {str(e)}")

        except Exception as e:
            logger.error(f"Error setting TP/SL orders: {str(e)}")
            logger.info("Continuing with open position despite TP/SL error")

        return True
    except Exception as e:
        logger.error(f"Error executing trade: {str(e)}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
