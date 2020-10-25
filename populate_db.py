import alpaca_trade_api as tradeapi
import config
import sqlite3

connection = sqlite3.connect('/Users/marco/Documents/Documents/Projects/automated-stock-trading-system/app.db')
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

cursor.execute("""
    SELECT symbol, company FROM stock
""")

rows = cursor.fetchall()
symbols = [row['symbol'] for row in rows]

api = tradeapi.REST(config.api_key, config.api_secret, base_url='https://paper-api.alpaca.markets')
assets = api.list_assets()

for asset in assets:
    try:
        if asset.status == 'active' and asset.tradable and asset.symbol not in symbols:
            print(f'Added a new stock {asset.symbol} {asset.name}')
            cursor.execute("INSERT INTO stock (symbol, company) VALUES (?, ?)", (asset.symbol, asset.name))
    except Exception as e:
        print(asset.symbol)
        print(e)

connection.commit()
