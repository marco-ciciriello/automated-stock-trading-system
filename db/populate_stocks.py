import alpaca_trade_api as tradeapi
import config
import sqlite3

connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

cursor.execute("""
    SELECT symbol, name 
    FROM stock
""")

rows = cursor.fetchall()
symbols = [row['symbol'] for row in rows]

api = tradeapi.REST(config.API_KEY, config.API_SECRET, base_url=config.API_URL)
assets = api.list_assets()
for asset in assets:
    try:
        if asset.status == 'active' and asset.tradable and asset.symbol not in symbols:
            print(f'Added a new stock {asset.symbol} {asset.name}')
            cursor.execute("""
                INSERT INTO stock (symbol, name, exchange, shortable)
                VALUES (?, ?, ?, ?)
            """, (asset.symbol, asset.name, asset.exchange, asset.shortable))
    except Exception as e:
        print(asset.symbol)
        print(e)

connection.commit()
