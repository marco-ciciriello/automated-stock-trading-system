import math
import pytz

from datetime import datetime


def calculate_stock_quantity(price):
    """Calculate number of stocks to purchase, given a starting balance and a stock price."""
    quantity = math.floor(10000 / price)  # 10000 is 10% of Alpaca paper trading starting balance
    return quantity


def is_dst():
    """Determine whether Daylight Savings Time is currently in effect."""

    x = datetime(datetime.now().year, 1, 1, 0, 0, 0, tzinfo=pytz.timezone('Europe/London'))  # Timezone as of Jan 1st of this year
    y = datetime.now(pytz.timezone('Europe/London'))  # Timezone as of now

    # If DST is in effect, x and y offsets will be different
    return not(y.utcoffset() == x.utcoffset())
