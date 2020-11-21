import alpaca_trade_api as tradeapi
import config
import numpy as np
import sqlite3
import tulipy as ti

from datetime import date

connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

cursor.execute("""
    SELECT id, symbol, name FROM stock
""")

rows = cursor.fetchall()
symbols = []
stock_dict = {}

for row in rows:
    symbol = row['symbol']
    symbols.append(symbol)
    stock_dict[symbol] = row['id']

api = tradeapi.REST(config.API_KEY, config.API_SECRET, base_url=config.API_URL)

batch_size = 200
for i in range(0, len(symbols), batch_size):
    symbol_batch = symbols[i: i+batch_size]
    barsets = api.get_barset(symbol_batch, 'day')
    for symbol in barsets:
        print(f'Processing symbol {symbol}')
        recent_closes = [bar.c for bar in barsets[symbol]]
        for bar in barsets[symbol]:
            stock_id = stock_dict[symbol]

            # Calculate technical indicators
            if len(recent_closes) >= 50 and date.today().isoformat() == bar.t.date().isoformat():
                sma_20 = ti.sma(np.array(recent_closes), period=20)[-1]
                sma_50 = ti.sma(np.array(recent_closes), period=50)[-1]
                rsi_14 = ti.rsi(np.array(recent_closes), period=14)[-1]
            else:
                sma_20, sma_50, rsi_14 = None, None, None

            cursor.execute("""
                INSERT INTO stock_price (stock_id, date, open, high, low, close, volume, sma_20, sma_50, rsi_14)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (stock_id, bar.t.date(), bar.o, bar.h, bar.l, bar.c, bar.v, sma_20, sma_50, rsi_14))

connection.commit()
