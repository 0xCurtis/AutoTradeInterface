import json
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from threading import Thread
from time import sleep

from pybit import usdt_perpetual, FailedRequestError
from rich.logging import RichHandler
from rich.traceback import install

install()

logger = logging.getLogger('syslog')
logger.setLevel(logging.DEBUG)

console = RichHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)


def info(msg):
    logger.info(msg)


def log(msg):
    logger.log(11, msg)


def error(msg, e_info=False):
    logger.error(msg, exc_info=e_info)


def req_check(r):
    if r['ret_code'] != 0:
        raise f"Request failed {r['ret_msg']}"


class ByBot:
    def __init__(self, file='config.json'):
        info("Setting up bot")
        try:
            with open(file, 'r') as cfg:
                cfg = json.load(cfg)
        except FileNotFoundError:
            error(f"{file} not found")
            raise
        try:
            order = cfg['order']
            api = cfg['api']

            self.updating = False
            self.trading = False
            self.balance = 0
            self.name = cfg['name']
            self.network = cfg['network']
            self.leverage = order['leverage']
            self.margin = order['margin'] / 100
            self.max = order['max']
            self.size = order['size']
            self.symbol = order['symbol']
            self.session = usdt_perpetual.HTTP(endpoint=self.network['endpoint'], api_secret=api['secret'],
                                               api_key=api['key'])
            self.updater = Thread(target=self.update_engine, daemon=True)
            self.updater.start()
        except NameError as e:
            error(f"Config file error: {e}")
            raise
        info(f"Bot {self.name} ready")

    def open_order(self, side, symbol):
        if symbol != self.symbol:
            raise "Wrong symbol"
        price = self.session.public_trading_records(symbol=symbol, limit=1)['result'][0]['price']
        qty = round((self.size / price) * self.leverage, 5)
        qty = min(self.max, qty)
        trailing_stop = price * self.margin
        order = self.session.place_active_order(
            symbol=symbol,
            side=side,
            order_type="Market",
            qty=qty,
            time_in_force="GoodTillCancel",
            reduce_only=False,
            close_on_trigger=False
        )
        req_check(order)
        limit = self.session.set_trading_stop(
            symbol=symbol,
            side=side,
            trailing_stop=trailing_stop
        )
        req_check(limit)
        self.trading = True
        info('New order placed')

    def update_engine(self):
        self.updating = True
        info('Update engine started')
        while True:
            self.update()
            sleep(1 * 60)

    def update(self):
        try:
            self.balance = self.session.get_wallet_balance()['result']['USDT']['available_balance']
            self.max = min(self.balance, self.max)
            position = self.session.my_position(symbol=self.symbol)['result']
            leverage = self.leverage
            if position[0]['leverage'] != leverage or position[1]['leverage'] != leverage:
                self.session.set_leverage(symbol=self.symbol, buy_leverage=leverage, sell_leverage=leverage)
            self.trading = position[0]['size'] + position[1]['size'] > 0
        except Exception:
            self.updating = False
            raise
