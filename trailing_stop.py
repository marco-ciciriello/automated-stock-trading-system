import alpaca_trade_api as tradeapi
import config
import tulipy

from helpers import calculate_stock_quantity

api = tradeapi.REST(config.API_KEY, config.API_SECRET, base_url=config.API_URL)

# symbols = ['SPY', 'IWM', 'DIA']

# for symbol in symbols:
#     quote = api.get_last_quote(symbol)
#     api.submit_order(
#         symbol=symbol,
#         side='buy',
#         type='market',
#         qty=calculate_stock_quantity(quote.bidprice),
#         time_in_force='day',
#     )

# api.submit_order(
#     symbol='SPY',
#     side='sell',
#     type='trailing_stop',
#     trail_percent='0.70',
#     qty=5,
#     time_in_force='day',
# )