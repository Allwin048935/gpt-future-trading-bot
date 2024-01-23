import ccxt
import pandas as pd
import numpy as np
import asyncio
from telegram import Bot, ParseMode  # Corrected import statement

# Binance API credentials
api_key = 'BVhb32XgQmX17IGs3vVH2Hw1fiH9W84pg8K5JtLuQnRKHPy7YlyPTG0qChkxTnrL'
api_secret = 'xVM8dF8qIhTRtfaTShbHON7oJffooUbP2wp3oPqYUbFLJ1ZCHLN9dEmN9niAYzVF'


# Telegram API credentials
telegram_token = '6811110812:AAFNJp5kcSh0KZ71Yizf8Y3rPBarz-ywopM'
private_chat_id = '1385370555'  # Replace with your private chat ID

# Initialize Binance client
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

# Initialize Telegram bot
telegram_bot = Bot(token=telegram_token)

# Dictionary to store the last executed order type for each trading pair
last_order_type = {}

# Function to get historical OHLCV data
async def fetch_ohlcv(symbol, timeframe='1h', limit=100):
    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

# Function to calculate EMA
def calculate_ema(df, period):
    return df['close'].ewm(span=period, adjust=False).mean()

# EMA Crossover Trading Strategy
def ema_crossover_strategy(df, short_ema_period, long_ema_period):
    df['short_ema'] = calculate_ema(df, short_ema_period)
    df['long_ema'] = calculate_ema(df, long_ema_period)
    
    df['signal'] = 0  # 0: No action, 1: Buy, -1: Sell
    
    df.loc[df['short_ema'] > df['long_ema'], 'signal'] = 1  # Buy Signal
    df.loc[df['short_ema'] < df['long_ema'], 'signal'] = -1  # Sell Signal
    
    return df

# Function to get the current price of the asset
async def get_current_price(symbol):
    ticker = await exchange.fetch_ticker(symbol)
    return ticker['last']

# Function to send message to Telegram
def send_telegram_message(message):
    telegram_bot.send_message(chat_id=private_chat_id, text=message, parse_mode=ParseMode.MARKDOWN)

# Main function to run the trading bot
async def run_trading_bot(symbol, short_ema_period, long_ema_period, trade_quantity_usdt):
    while True:
        try:
            # Fetch historical data
            historical_data = await fetch_ohlcv(symbol)
            
            # Apply EMA crossover strategy
            strategy_data = ema_crossover_strategy(historical_data, short_ema_period, long_ema_period)
            
            # Check for signals
            current_signal = strategy_data['signal'].iloc[-1]
            
            # Check if the current signal is different from the last executed order type
            if last_order_type.get(symbol) != current_signal:
                # Get the current price of the asset
                current_price = await get_current_price(symbol)
                
                # Calculate the equivalent quantity in the base asset
                trade_quantity = trade_quantity_usdt / current_price
                
                # Execute order based on the current signal
                if current_signal == 1:
                    # Execute Buy order
                    order = await exchange.create_market_buy_order(symbol, trade_quantity)
                    message = f"**Buy Signal** for {symbol} detected. Placing order...\nOrder ID: {order['id']}"
                    send_telegram_message(message)
                elif current_signal == -1:
                    # Execute Sell order
                    order = await exchange.create_market_sell_order(symbol, trade_quantity)
                    message = f"**Sell Signal** for {symbol} detected. Placing order...\nOrder ID: {order['id']}"
                    send_telegram_message(message)
                
                # Update the last executed order type
                last_order_type[symbol] = current_signal
            
            # Sleep for some time before checking again
            await asyncio.sleep(300)  # Sleep for 5 minutes
            
        except Exception as e:
            error_message = f"An error occurred for {symbol}: {e}"
            send_telegram_message(error_message)
            await asyncio.sleep(60)  # Sleep for 1 minute before retrying

async def main():
    # Define parameters
    short_ema_period = 12
    long_ema_period = 26
    trade_quantity_usdt = 100  # Change this to the USDT quantity you want to trade

    # Get all USDT pairs
    usdt_pairs = [symbol for symbol in exchange.symbols if symbol.endswith('USDT')]
    
    # Run trading bot for each USDT pair
    tasks = [run_trading_bot(symbol, short_ema_period, long_ema_period, trade_quantity_usdt) for symbol in usdt_pairs]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())

