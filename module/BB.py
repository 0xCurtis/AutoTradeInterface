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
            self.order_id = None
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
        info(f"Bot {self.name} ready")

    def add_log_handle(self):
        logging.addLevelName(11, 'RUN')
        fh = TimedRotatingFileHandler(self.log_path, when='midnight', interval=1, backupCount=4)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'))
        fh.suffix = "%Y-%m-%d.log"
        logger.addHandler(fh)

    def open_order(self, side, symbol):
        if symbol != self.symbol:
            raise "Wrong symbol"
        price = self.session.public_trading_records(symbol=symbol, limit=1)['result'][0]['price']
        exposure = self.size * self.balance
        qty = round((exposure / price) * self.leverage, 5)
        qty = min(self.max, qty)
        sl = price * 0.995 if side == "Buy" else price * 1.005
        sl = round(sl, 4)
        tp = price * 1.002 if side == "Buy" else price * 0.998
        tp = round(tp, 4)
        # trailing_stop = round(price * self.margin, 2)
        order = self.session.place_active_order(
            symbol=symbol,
            side=side,
            order_type="Market",
            qty=qty,
            time_in_force="GoodTillCancel",
            reduce_only=False,
            close_on_trigger=False,
            stop_loss=sl,
            take_profit=tp
        )
        req_check(order)
        # limit = self.session.set_trading_stop(
        #     symbol=symbol,
        #     side=side,
        #     trailing_stop=trailing_stop
        # )
        # req_check(limit)
        self.trading = True
        self.order_id = order['result']['order_id']
        info(f'{side} order placed\n'
             f'At: {price} with {qty} {symbol} for {exposure} USDT\n'
             f'SL: {sl} TP: {tp}\n'
             f'Order ID: {self.order_id}')

    def replace_order(self, side, symbol):
        if symbol != self.symbol:
            raise "Wrong symbol"
        price = self.session.public_trading_records(symbol=symbol, limit=1)['result'][0]['price']
        exposure = self.size * self.balance
        sl = price * 0.995 if side == "Buy" else price * 1.005
        sl = round(sl, 4)
        tp = price * 1.002 if side == "Buy" else price * 0.998
        tp = round(tp, 4)
        order = self.session.replace_active_order(
            symbol=symbol,
            order_id=self.order_id,
            take_profit=tp,
            stop_loss=sl
        )
        req_check(order)
        self.order_id = order['result']['order_id']
        info(f'{side} order replaced\n'
             f'At: {price} with {qty} {symbol} for {exposure} USDT\n'
             f'SL: {sl} TP: {tp}\n'
             f'Order ID: {self.order_id}')


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
                log("Bot ready for a new trade")
        except Exception:
            self.updating = False
            raise
