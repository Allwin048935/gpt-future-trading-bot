import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException
import time
import talib
import numpy as np

# Constants
FEE = 0.001  # 0.1%

# Binance API keys Test Net
ENABLE_TESTNET = True  # False for Main Net
API_KEY = 'BVhb32XgQmX17IGs3vVH2Hw1fiH9W84pg8K5JtLuQnRKHPy7YlyPTG0qChkxTnrL'
API_SECRET = 'xVM8dF8qIhTRtfaTShbHON7oJffooUbP2wp3oPqYUbFLJ1ZCHLN9dEmN9niAYzVF'

# Telegram settings
ENABLE_TELEGRAM = False
TELEGRAM_API = '6811110812:AAFNJp5kcSh0KZ71Yizf8Y3rPBarz-ywopM'
TELEGRAM_CHAT_ID = '1385370555'

client = Client(api_key=API_KEY, api_secret=API_SECRET, testnet=ENABLE_TESTNET)

def send_telegram_message(message):
    if ENABLE_TELEGRAM:
        url = f"https://api.telegram.org/bot{TELEGRAM_API}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={message}"
        requests.get(url)

    # console output
    print(f"{message}")

def get_historical_data(symbol, interval):
    klines = client.futures_klines(symbol=symbol, interval=interval)
    close_prices = [float(entry[4]) for entry in klines]
    return close_prices

def get_latest_price(symbol):
    ticker = client.futures_ticker(symbol=symbol)
    return float(ticker['lastPrice'])

def adjust_precision(value, precision):
    format_string = "{:0.0" + str(precision) + "f}"
    return format_string.format(value)

def get_balance(asset):
    account_info = client.futures_account()
    for asset_balance in account_info['assets']:
        if asset_balance['asset'] == asset:
            return float(asset_balance['walletBalance'])
    return 0.0

def calculate_quantity_fixed_usdt(symbol, fixed_usdt_amount):
    # Fetch account information
    account_info = client.futures_account()
    exchange_info = client.get_exchange_info()

    pair_info = next((item for item in exchange_info['symbols'] if item['symbol'] == symbol), None)

    if pair_info:
        # Extracting precision for quantity (lot size)
        lot_size_filter = next(filter for filter in pair_info['filters'] if filter['filterType'] == 'LOT_SIZE')
        quantity_precision = len(str(lot_size_filter['stepSize']).rstrip('0').split('.')[1]) if '.' in str(
            lot_size_filter['stepSize']) else 0

        # Extracting precision for price
        price_filter = next(filter for filter in pair_info['filters'] if filter['filterType'] == 'PRICE_FILTER')
        price_precision = len(str(price_filter['tickSize']).rstrip('0').split('.')[1]) if '.' in str(
            price_filter['tickSize']) else 0

    else:
        print(f"Information for {symbol} not found")

    # Fetch the latest price for the symbol
    latest_price = get_latest_price(symbol)

    # Calculate the base asset quantity using the fixed USDT amount
    base_asset_quantity = fixed_usdt_amount / latest_price

    qty = adjust_precision(base_asset_quantity, quantity_precision)

    print(f"Fixed USDT Amount: {fixed_usdt_amount}, Calculated Quantity: {qty}")

    return qty

def place_order(symbol, side, leverage, fixed_usdt_amount):
    try:
        # Set leverage
        client.futures_change_leverage(symbol=symbol, leverage=leverage)

        # Calculate the quantity based on the fixed USDT amount
        quantity = calculate_quantity_fixed_usdt(symbol, fixed_usdt_amount)

        timestamp = int(time.time() * 1000)

        # Place order
        order = client.futures_create_order(symbol=symbol, side=side, type=client.ORDER_TYPE_MARKET, quantity=quantity,
                                            timestamp=timestamp)  # Adjust quantity as needed
        return order
    except BinanceAPIException as e:
        send_telegram_message(f"Error placing {side} order: {e.message}")
        return None

# Rest of the code remains unchanged

# ...

# ...

# Rest of the code remains unchanged

# ...

# ...

if __name__ == "__main__":
    import sys

    short_ema_period = int(sys.argv[1])
    long_ema_period = int(sys.argv[2])
    interval = sys.argv[3]
    leverage = int(sys.argv[4])

    # Set the fixed USDT amount to $100
    fixed_usdt_amount = 100.0

    main(short_ema_period, long_ema_period, interval, leverage, fixed_usdt_amount)

