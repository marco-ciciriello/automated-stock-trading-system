# Accessing the polygon.io data will only work for those with an Alpaca live trading account.

import alpaca_trade_api as tradeapi
import config
import smtplib
import sqlite3
import ssl

from datetime import date, datetime
from helpers import calculate_stock_quantity
from timezone import is_dst

# Create secure SSL context
context = ssl.create_default_context()

connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

cursor.execute("""
    SELECT id
    FROM strategy
    WHERE name = 'opening_range_breakout'
""")

strategy_id = cursor.fetchone()['id']

cursor.execute("""
    SELECT symbol, name
    FROM stock JOIN stock_strategy ON stock_strategy.stock_id = stock_id
    WHERE stock_strategy.strategy_id = ?
""", (strategy_id,))

stocks = cursor.fetchall()
symbols = [stock['symbol'] for stock in stocks]
current_date = date.today().isoformat()
if is_dst():
    start_minute_bar = f'{current_date} 09:30:00-01:00'
    end_minute_bar = f'{current_date} 09:45:00-01:00'
else:
    start_minute_bar = f'{current_date} 09:30:00'
    end_minute_bar = f'{current_date} 09:45:00'

api = tradeapi.REST(config.API_KEY, config.API_SECRET, base_url=config.API_URL)
orders = api.list_orders(status='all', after=current_date)
existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']
messages = []

for symbol in symbols:
    minute_bars = api.polygon.historic_agg_v2(symbol, 1, 'minute', _from=current_date, to=current_date).df
    opening_range_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index < end_minute_bar)
    opening_range_bars = minute_bars.loc[opening_range_mask]
    opening_range_low = opening_range_bars['low'].min()
    opening_range_high = opening_range_bars['high'].max()
    opening_range = opening_range_high - opening_range_low

    after_opening_range_mask = minute_bars.index >= end_minute_bar
    after_opening_range_bars = minute_bars.loc[after_opening_range_mask]
    after_opening_range_breakout = after_opening_range_bars[after_opening_range_bars['close'] > opening_range_high]

    if not after_opening_range_breakout.empty:
        if not symbol in existing_order_symbols:
            limit_price = after_opening_range_breakout.iloc[0]['close']
            message = f'Selling short {symbol} at {limit_price}, closed above {opening_range_high}\n\n{after_opening_range_breakout.iloc[0]}\n\n'
            messages.append(message)
            print(message)
            try:
                api.submit_order(
                    symbol=symbol,
                    side='buy',
                    type='limit',
                    qty=calculate_stock_quantity(limit_price),
                    time_in_force='day',
                    order_class='bracket',
                    limit_price=limit_price,
                    take_profit=dict(
                        limit_price=limit_price + opening_range,
                    ),
                    stop_loss=dict(
                        stop_price=limit_price - opening_range,
                    )
                )
            except Exception as e:
                print(f'Could not submit order: {e}')
        else:
            print(f'An order for {symbol} already exists, skipping...')

with smtplib.SMTP_SSL(config.EMAIL_HOST, config.EMAIL_PORT, context=context) as server:
    email_message = f'Subject: Trade notifications for {current_date}\n\n'
    email_message += '\n\n'.join(messages)
    server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
    server.sendmail(config.EMAIL_ADDRESS, config.EMAIL_ADDRESS, email_message)
