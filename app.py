import config
import sqlite3

from datetime import date
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory='templates')


@app.get('/')
def index(request: Request):
    stock_filter = request.query_params.get('filter', False)
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if stock_filter == 'new_intraday_highs':
        cursor.execute("""
            SELECT * FROM (
                SELECT symbol, name, stock_id, max(close), date
                FROM stock_price JOIN stock ON stock.id = stock_price.stock_id
                GROUP BY stock_id
                ORDER BY symbol
            ) WHERE date = ?
        """, (date.today().isoformat(),))
    elif stock_filter == 'new_closing_highs':
        cursor.execute("""
            SELECT * FROM (
                SELECT symbol, name, stock_id, max(close), date
                FROM stock_price JOIN stock ON stock.id = stock_price.stock_id
                GROUP BY stock_id
                ORDER BY symbol
            ) WHERE date = ?
        """, (date.today().isoformat(),))
    elif stock_filter == 'new_intraday_lows':
        cursor.execute("""
            SELECT * FROM (
                SELECT symbol, name, stock_id, min(close), date
                FROM stock_price JOIN stock ON stock.id = stock_price.stock_id
                GROUP BY stock_id
                ORDER BY symbol
            ) WHERE date = ?
        """, (date.today().isoformat(),))
    elif stock_filter == 'new_closing_lows':
        cursor.execute("""
            SELECT * FROM (
                SELECT symbol, name, stock_id, min(close), date
                FROM stock_price JOIN stock ON stock.id = stock_price.stock_id
                GROUP BY stock_id
                ORDER BY symbol
            ) WHERE date = ?
        """, (date.today().isoformat(),))
    else:
        cursor.execute("""
            SELECT id, symbol, name FROM stock ORDER BY symbol
        """)

    rows = cursor.fetchall()

    return templates.TemplateResponse('index.html', {'request': request, 'stocks': rows})


@app.get('/stock/{symbol}')
def stock_info(request: Request, symbol):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM strategy
    """)

    strategies = cursor.fetchall()

    cursor.execute("""
        SELECT id, symbol, name FROM stock WHERE symbol = ?
    """, (symbol,))

    row = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM stock_price WHERE stock_id = ?
    """, (row['id'],))

    candles = cursor.fetchall()

    return templates.TemplateResponse('stock_info.html', {'request': request, 'stock': row, 'candles': candles, 'strategies': strategies})


@app.post('/apply_strategy')
def apply_strategy(strategy_id: int = Form(...), stock_id: int = Form(...)):
    connection = sqlite3.connect(config.DB_FILE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO stock_strategy (stock_id, strategy_id) VALUES (?, ?)
    """, (stock_id, strategy_id))

    connection.commit()

    return RedirectResponse(url=f'/strategy/{strategy_id}', status_code=303)


@app.get('strategy/{strategy_id}')
def strategy(request: Request, strategy_id):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name
        FROM strategy
        WHERE id = ?
    """, (strategy_id,))

    strategy = cursor.fetchone()

    cursor.execute("""
        SELECT symbol, name
        FROM stock JOIN stock_strategy ON stock_strategy.stock_id = stock_id
        WHERE strategy_id = ?
    """, (strategy_id,))

    stocks = cursor.fetchall()

    return templates.TemplateResponse('strategy.html', {'request': request, 'stocks': stocks, 'strategy': strategy})