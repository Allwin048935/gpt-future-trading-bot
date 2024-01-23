from binance.client import Client
import pandas as pd
import time

# Replace YOUR_API_KEY and YOUR_API_SECRET with your Binance API key and secret
api_key = 'BVhb32XgQmX17IGs3vVH2Hw1fiH9W84pg8K5JtLuQnRKHPy7YlyPTG0qChkxTnrL'
api_secret = 'xVM8dF8qIhTRtfaTShbHON7oJffooUbP2wp3oPqYUbFLJ1ZCHLN9dEmN9niAYzVF'

client = Client(api_key, api_secret, testnet=False)  # Use the main Binance platform

symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # Add more symbols as needed
interval = "1h"  # 1-hour candlestick data

while True:
    for symbol in symbols:
        # Get historical klines data
        klines = client.get_historical_klines(symbol, interval, "1 day ago UTC")

        # Extract the closing prices from klines
        closing_prices = [float(kline[4]) for kline in klines]

        # Create a DataFrame with timestamp and closing prices
        df = pd.DataFrame(closing_prices, columns=["Close"], index=pd.to_datetime([kline[0] for kline in klines], unit="ms"))

        # Calculate short-term EMA
        short_ema_period = 9
        df['ShortEMA'] = df['Close'].ewm(span=short_ema_period, adjust=False).mean()

        # Calculate long-term EMA
        long_ema_period = 21
        df['LongEMA'] = df['Close'].ewm(span=long_ema_period, adjust=False).mean()

        # Get current price
        current_price = df['Close'].iloc[-1]

        # Determine order side and limit price based on EMA positions
        if df['ShortEMA'].iloc[-1] > current_price and df['LongEMA'].iloc[-1] > current_price:
            side = "BUY"
            limit_price = current_price * 0.998  # 0.2% below current price
        elif df['ShortEMA'].iloc[-1] < current_price and df['LongEMA'].iloc[-1] < current_price:
            side = "SELL"
            limit_price = current_price * 1.002  # 0.2% above current price
        else:
            continue  # No action if conditions are not met

        # Calculate the equivalent quantity in terms of USDT (fixed at 100 USDT)
        usdt_quantity = 100
        quantity = usdt_quantity / current_price

        # Place a market order
        order = client.create_order(
            symbol=symbol,
            side=side,
            type="LIMIT",
            timeInForce="GTC",  # Good 'til Cancelled
            quantity=quantity,
            price=limit_price,
        )

        print(f"Placed {side} limit order for {quantity} on {symbol} at {pd.Timestamp.now()} with limit price {limit_price}")

    # Sleep for a short period before the next iteration
    time.sleep(60)  # Sleep for 60 seconds before the next iteration

