# Create a crontab event to run this file once per day, usually towards the end

import alpaca_trade_api as tradeapi
import config

api = tradeapi.REST(config.API_KEY, config.API_SECRET, base_url=config.API_URL)

response = api.close_all_positions()
print(response)
