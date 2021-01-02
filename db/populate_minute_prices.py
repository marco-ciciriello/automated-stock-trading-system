# Accessing the polygon.io data will only work for those with an Alpaca live trading account
 
import alpaca_trade_api as tradeapi
import config
import csv
import pandas as pd
import sqlite3

from datetime import datetime, timedelta

pd.set_option('display.max_rows', -1)

connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

symbols, stock_ids = [], {}

with open('qqq.csv') as f:
    reader = csv.reader(f)
    for line in reader:
        symbols.append(line[1])

cursor.execute("""
    SELECT *
    FROM stocks
""")

stocks = cursor.fetchall()
for stock in stocks:
    symbol = stock['symbol']
    stock_ids[symbol] = stock['id']

for symbol in symbols:
    start_date = datetime(2020, 1, 6).date()
    end_date = datetime(2020, 12, 31).date()
    while start_date <= end_date:
        end_date = start_date + timedelta(days=4)
        print(f'Fetching minute bars {start_date}-{end_date} for {symbol}')
        api = tradeapi.REST(config.API_KEY, config.API_SECRET, base_url=config.API_URL)
        minutes = api.polygon.historic_agg_v2(symbol, 1, 'minute', _from=start_date, to=end_date).df
        minutes = minutes.resample('1min').ffil()  # Forward fill gaps - investigate if this is best choice

        for index, row in minutes.iterrows():
            cursor.execute("""
                INSERT INTO stock_price_minute (stock_id, datetime, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (stock_ids[symbol], index.tz_localize(None).isoformat(), row['open'], row['high'], row['low'], row['close'], row['volume']))

        start_date = start_date + timedelta(days=7)

connection.commit()
