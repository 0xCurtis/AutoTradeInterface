#%%
from pybit import usdt_perpetual
import json
from rich.traceback import install

install()

with open('config.json', 'r') as cfg:
    cfg = json.load(cfg)
    _api_key = cfg['creds']['api_key']
    _api_secret = cfg['creds']['api_secret']

session = usdt_perpetual.HTTP(endpoint="https://api-testnet.bybit.com", api_key=_api_key, api_secret=_api_secret)

#%%
a = session.my_position(symbol="BTCUSDT")['result']
