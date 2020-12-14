import math


def calculate_stock_quantity(price):
    quantity = math.floor(10000 / price)  # 10000 is 10% of Alpaca paper trading starting balance
    return quantity