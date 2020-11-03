import alpaca_trade_api as tradeapi
import config
import sqlite3

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
        for bar in barsets[symbol]:
            stock_id = stock_dict[symbol]
            cursor.execute("""
                INSERT INTO stock_price (stock_id, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (stock_id, bar.t.date(), bar.o, bar.h, bar.l, bar.c, bar.v))

connection.commit()
