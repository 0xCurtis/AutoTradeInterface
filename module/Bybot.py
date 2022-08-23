import json
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from threading import Thread

import pybit.usdt_perpetual
from rich.logging import RichHandler
from rich.traceback import install

install()

logger = logging.getLogger('syslog')
logger.setLevel(logging.DEBUG)

console = RichHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)


def log(msg):
    logger.log(11, msg)


def error(msg, e_info=True):
    logger.error(msg, exc_info=e_info)


def info(msg):
    logger.info(msg)


class ByBot:
    def __init__(self) -> None:
        try:
            with open('config.json', 'r') as cfg:
                cfg = json.load(cfg)
                self._api_key = cfg['creds']['api_key']
                self._api_secret = cfg['creds']['api_secret']
                self.endpoint = cfg['parameters']['endpoint']
                # TODO check session state
                self.session = pybit.usdt_perpetual.HTTP(endpoint=self.endpoint, api_key=self._api_key,
                                                         api_secret=self._api_secret)
                self.id = cfg['logging']['id']
                self.desc = cfg['logging']['desc']
                self.port = cfg['network']['port']
                self.leverage = cfg['parameters']['leverage']
                self.max_size = cfg['parameters']['size']['max']
                self.flat = cfg['parameters']['size']['flat']
                self.size = cfg['parameters']['size']['size']
                self.sl = cfg['parameters']['stoploss']
                self.tp = cfg['parameters']['takeprofit']
                self.in_trade = False
                self.thread = Thread(target=self.order_manager, daemon=True)
                self.log_path = f"./logs/{self.id}.log"
                self.balance = self.get_balance()
                self.last_price = -1
        except Exception as e:
            error(f"Could not get config", False)
            raise
        self.add_log_handle()
        info(f"ByBot initialized - {self.id}")
        log('-' * 30)
        log(f"ByBot initialized - {self.id}")
        log(f"Purpose: {self.desc}")
        log(f"Endpoint: {self.endpoint}")
        log(f"Launch date: {datetime.now()}")
        log(f"Balance: {self.get_balance()}")
        log('-' * 30)

    def add_log_handle(self):
        logging.addLevelName(11, 'RUN')
        fh = TimedRotatingFileHandler(self.log_path, when='midnight', interval=1, backupCount=4)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'))
        fh.suffix = "%Y-%m-%d.log"
        logger.addHandler(fh)

    def order_manager(self):
        # TODO implementer le order manager
        log(f"Order manager started")

    def get_balance(self):
        # TODO add fallback
        try:
            self.balance = self.session.get_wallet_balance(coin="USDT")['result']['USDT']['available_balance']
        except Exception as e:
            error(f"Couldn't get balance, check API key", False)
            raise
        return self.balance

    def get_last_price(self, pair):
        # TODO check request (add try)
        self.last_price = self.session.public_trading_records(
            symbol=pair,
            limit=1)['result']['records'][0]['price']
        return self.last_price

    def set_margin(self, buy=1, sell=1, pair=""):
        if pair == "":
            return
        try:
            log(f"Setting leverage for {pair} to {buy}x{sell}")
            self.session.set_leverage(
                symbol=pair,
                buy_leverage=buy,
                sell_leverage=sell)
        except Exception as e:
            # TODO add fallback
            error(f"Could not set leverage - {e}")
            pass

    def parse_order_data(self, data):
        log(f"Parsing order data")
        log(f"{data['side']} request on {data['pair']}")
        if not self.flat:
            balance = self.get_balance()
            # TODO qty_in_usd must be set (unsolved reference)
            qty_in_usd = balance * (qty_in_usd / 100)
        qty_in_usd = min(self.size, self.max_size)
        # TODO check request (add try)
        self.open_perp_order(
            pair=data['pair'],
            side=data['side'],
            qty_in_usd=qty_in_usd,
            lever=self.leverage,
            flat=True,
            sl=self.sl,
            tp=self.tp)

    def open_perp_order(self, pair="", side="", qty_in_usd=0, lever=1, flat=True, sl=None, tp=None):
        log(f"Opening order")
        log(f"{pair} {side} {qty_in_usd} {lever} {flat} {sl} {tp}")
        if pair == "" or side == "" or qty_in_usd == 0 or lever == 0:
            logger.warning('Wrong order parameters')
            return
        try:
            l_price = self.get_last_price(pair)
            quantity = round((qty_in_usd / l_price) * lever, 5)
            # TODO add default values for stop and take
            # TODO opti if else
            if sl is not None:
                stop = l_price * (1 - sl / 100) if side == "Buy" else l_price * (1 + sl / 100)
            if tp is not None:
                take = l_price * 1 + (tp / 100) if side == "Buy" else l_price * 1 - (tp / 100)
            self.set_margin(buy=lever, sell=lever, pair=pair)

            res = self.session.place_active_order(
                symbol=pair,
                side=side,
                order_type="Market",
                qty=quantity,
                time_in_force="GoodTillCancel",
                reduce_only=False,
                close_on_trigger=False,
                take_profit=take,
                stop_loss=stop)
            self.in_trade = True
            return res
        except Exception as e:
            error(f"Could not open order - {e}")
            return

    def __repr__(self) -> str:
        return '-' * 30 + '\n' \
                          f"ByBot v0.1\n" \
                          f"Endpoint: {self.endpoint}\n" \
                          f"ID: {self.id}\n" \
                          f"Log-path: {self.log_path}\n" \
                          f"Description: {self.desc}\n" \
               + '-' * 30
