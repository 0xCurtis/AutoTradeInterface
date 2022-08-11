import json
import logging
import pathlib
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from threading import Thread

import pybit.usdt_perpetual
from rich.traceback import install

install()
logging.basicConfig(
    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%d-%d-%Y %H:%M:%S')
logger = logging.getLogger()

class ByBot:
    def __init__(self) -> None:
        self.get_config()
        self.set_logger()
        self.log(f"ByBot initialized - {self.id}")
        self.log(f"Purpose: {self.desc}\n"
            f"Endpoint: {self.endpoint}\n"
            f"Launch date: {datetime.now()}\n"
            f"Balance: {self.get_balance()} USDT\n"
            f"{'-'*30}\n")

    def get_config(self):
        try:
            with open('config.json', 'r') as cfg:
                cfg = json.load(cfg)
                self._api_key = cfg['creds']['api_key']
                self._api_secret = cfg['creds']['api_secret']
                self.endpoint = cfg['parameters']['endpoint']
                self.session = pybit.usdt_perpetual.HTTP(endpoint=self.endpoint, api_key=self._api_key, api_secret=self._api_secret)

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
        except Exception as e:
            logger.error(f"Could not get config - {e}")
            exit(84)

    def set_logger(self):
        self.logger = logging.getLogger(self.id)
        self.log_path = f"./logs/{self.id}"
        self.log_handle = TimedRotatingFileHandler(self.log_path, when='midnight', interval=1, backupCount=4)
        self.log_handle.suffix = "%Y-%m-%d.log"
        self.log_handle.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'))
        self.log_handle.setLevel(logging.INFO)
        self.logger.addHandler(self.log_handle)

    def log(self, msg):
        self.logger.info(msg)

    def order_manager(self):
        self.log(f"Order manager started")

    def get_balance(self):
        return self.session.get_wallet_balance(coin="USDT")['result']['USDT']['available_balance']
