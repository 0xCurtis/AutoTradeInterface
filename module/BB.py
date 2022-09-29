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


def req_check(r, t="Open order"):
    if r['ret_code'] != 0:
        raise f"{t} failed {r['ret_msg']}"


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
            self.order = None
            self.name = cfg['name']
            self.network = cfg['network']
            self.leverage = order['leverage']
            self.margin = order['margin'] / 100
            self.max = order['max']
            self.size = order['size']
            self.symbol = order['symbol']
            self.session = usdt_perpetual.HTTP(endpoint=self.network['endpoint'], api_secret=api['secret'],
                                               api_key=api['key'])
            self.log_path = f"./logs/{cfg['name']}.log"
            self.updater = Thread(target=self.update_engine, daemon=True)
            self.updater.start()
        except NameError as e:
            error(f"Config file error: {e}")
            raise
        self.add_log_handle()
        self.update_balance()
        info(f"Bot {self.name} ready, {self.balance}$ available")

    def add_log_handle(self):
        logging.addLevelName(11, 'RUN')
        fh = TimedRotatingFileHandler(self.log_path, when='midnight', interval=1, backupCount=4)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'))
        fh.suffix = "%Y-%m-%d.log"
        logger.addHandler(fh)

    def place_order(self, side, qty, exposure):
        self.order = self.session.place_active_order(
            symbol=self.symbol,
            side=side,
            order_type='Market',
            qty=qty,
            time_in_force='GoodTillCancel',
            reduce_only=False,
            close_on_trigger=False
        )
        req_check(self.order)
        self.trading = True
        position = self.session.my_position(symbol=self.symbol)['result']
        price = position[side == "Sell"]["entry_price"]

        stop_loss = price * 0.995 if side == "Buy" else price * 1.005
        stop_loss = round(stop_loss, 4)
        take_profit = price * 1.002 if side == "Buy" else price * 0.998
        take_profit = round(take_profit, 4)

        info(f"{price} tp: {take_profit} sl: {stop_loss}")
        trading_stop = self.session.set_trading_stop(
            symbol=self.symbol,
            side=side,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        req_check(trading_stop, "Trading stop")
        info(f'{side} order placed\n'
             f'At: {price} with {qty} {self.symbol} for {exposure} USDT\n'
             f'SL: {stop_loss} TP: {take_profit}\n'
             f'Order ID: {self.order["result"]["order_id"]}')


    def open_order(self, side):
        price = self.session.public_trading_records(symbol=self.symbol, limit=1)['result'][0]['price']
        exposure = min(self.size * self.balance, self.max)
        qty = round((exposure / price) * self.leverage, 5)
        self.place_order(side, qty, exposure)


    def update_engine(self):
        self.updating = True
        info('Update engine started')
        while True:
            self.update()
            sleep(1 * 10)

    def update_balance(self):
        self.balance = self.session.get_wallet_balance()['result']['USDT']['available_balance']

    def update(self):
        try:
            self.update_balance()
            position = self.session.my_position(symbol=self.symbol)['result']
            leverage = self.leverage
            if position[0]['leverage'] != leverage or position[1]['leverage'] != leverage:
                self.session.set_leverage(symbol=self.symbol, buy_leverage=leverage, sell_leverage=leverage)
            if self.trading and position[0]['size'] + position[1]['size'] <= 0:
                self.trading = False
                log(f"Bot ready for a new trade, {self.balance}$ available")
        except Exception:
            self.updating = False
            raise
