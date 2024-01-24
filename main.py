from binance.client import Client
import numpy as np
import pandas as pd
import time

# Replace YOUR_API_KEY and YOUR_API_SECRET with your Binance API key and secret
api_key = ''
api_secret = ''

client = Client(api_key, api_secret)

symbols = [symbol['symbol'] for symbol in client.get_exchange_info()['symbols'] if symbol['quoteAsset'] == 'USDT']
quantity = 100
interval = "1h"  # 1-hour candlestick data
last_order_side = {}  # To keep track of the last order side for each symbol

def calculate_ema(data, period):
    alpha = 2 / (period + 1)
    ema = np.zeros_like(data)
    ema[0] = data[0]

    for i in range(1, len(data)):
        ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]

    return ema

while True:
    for symbol in symbols:
        # Get historical klines data
        klines = client.get_klines(symbol=symbol, interval=interval, limit=1000)

        # Extract the closing prices from klines
        closing_prices = np.array([float(kline[4]) for kline in klines])

        # Calculate short-term EMA
        short_ema_period = 9
        short_ema = calculate_ema(closing_prices, short_ema_period)

        # Calculate long-term EMA
        long_ema_period = 21
        long_ema = calculate_ema(closing_prices, long_ema_period)

        # Get current price
        current_price = closing_prices[-1]

        # Determine order side and limit price based on EMA positions
        if short_ema[-1] > long_ema[-1] and short_ema[-2] <= long_ema[-2]:
            # Crossover: Short-term EMA crosses above Long-term EMA
            side = "BUY"  # Place a long position
            limit_price = current_price * 1.002  # 0.2% above current price
        elif short_ema[-1] < long_ema[-1] and short_ema[-2] >= long_ema[-2]:
            # Crossunder: Short-term EMA crosses below Long-term EMA
            side = "SELL"  # Place a short position
            limit_price = current_price * 0.998  # 0.2% below current price
        else:
            continue  # No action if conditions are not met

        # Check if the same order side was placed in the last iteration for the symbol
        if symbol in last_order_side and last_order_side[symbol] == side:
            continue  # Skip placing the same type of order consecutively

        # Place a limit order on the Binance Futures market
        order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type="LIMIT",
            timeInForce="GTC",  # Good 'til Cancelled
            quantity=quantity,
            price=limit_price,
        )

        print(f"Placed {side} limit order for {quantity} USDT on {symbol} at {pd.Timestamp.now()} with limit price {limit_price}")

        # Update the last order side for the symbol
        last_order_side[symbol] = side

    # Sleep for a short period before the next iteration
    time.sleep(60)  # Sleep for 60 seconds before the next iteration

