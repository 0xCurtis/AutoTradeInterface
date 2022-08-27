# %%
from pybit import usdt_perpetual
import json
from rich.traceback import install

install()

with open('config.json', 'r') as cfg:
    cfg = json.load(cfg)
    _api_key = cfg['api']['key']
    _api_secret = cfg['api']['secret']
session = usdt_perpetual.HTTP(endpoint="https://api-testnet.bybit.com", api_key=_api_key, api_secret=_api_secret)

# %%
a = session.my_position(symbol="BTCUSDT")['result']
# %%
b = session.place_active_order(
    symbol="BTCUSDT",
    side="Sell",
    order_type="Market",
    qty=0.05,
    time_in_force="GoodTillCancel",
    reduce_only=False,
    close_on_trigger=False)
# %%
c = session.set_trading_stop(symbol="BTCUSDT", side="Sell", trailing_stop=300)
# %%
d = session.public_trading_records(
    symbol="BTCUSDT",
    limit=1)['result']
