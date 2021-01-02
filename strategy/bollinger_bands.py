# Accessing the polygon.io data will only work for those with an Alpaca live trading account

import alpaca_trade_api as tradeapi
import config
import sqlite3
import tulipy as ti

from datetime import date, datetime
from helpers import is_dst

connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

cursor.execute("""
    SELECT id
    FROM strategy
    WHERE name = 'bollinger_bands'
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

start_minute_bar = f'{current_date} 08:00:00-01:00'
end_minute_bar = f'{current_date} 16:30:00-01:00'

api = tradeapi.REST(config.API_KEY, config.API_SECRET, base_url=config.API_URL)
orders = api.list_orders(status='all', after=current_date)
existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']
messages = []

for symbol in symbols:
    minute_bars = api.polygon.historic_agg_v2(symbol, 1, 'minute', _from=current_date, to=current_date).df
    market_open_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index < end_minute_bar)
    market_open_bars = minute_bars.loc[market_open_mask]

    if len(market_open_bars) >= 20:
        closes = market_open_bars.close.values
        bbands_lower, bbands_middle, bbands_upper = ti.bbands(closes, 20, 2)
    
    current_candle = market_open_bars.iloc[-1]
    previous_candle = market_open_bars.iloc[-2]

    if current_candle.close > bbands_lower[-1] and previous_candle.close < bbands_lower[-2]:
        print(f'{symbol} closed above the lower Bollinger band')
        print(current_candle)

        if not symbol in existing_order_symbols:
            limit_price = current_candle.close
            candle_range = current_candle.high - current_candle.low
            print(f'Placing order for {symbol} at {limit_price}')

            try:
                api.submit_order(
                    symbol=symbol,
                    side='buy',
                    type='limit',
                    qty='100',
                    time_in_force='day',
                    order_class='bracket',
                    limit_price=limit_price,
                    take_profit=dict(
                        limit_price=limit_price + (candle_range * 3),
                    ),
                    stop_loss=dict(
                        stop_price=previous_candle.low,
                    )
                )
            except Exception as e:
                print(f'Could not submit order: {e}')
        else:
            print(f'An order for {symbol} already exists, skipping...')
