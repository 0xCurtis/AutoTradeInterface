import json
import logging
from datetime import datetime
from distutils.debug import DEBUG
from logging.handlers import TimedRotatingFileHandler
from threading import Thread

import pybit.usdt_perpetual
from rich.logging import RichHandler
from rich.traceback import install

install()

logging.addLevelName(11, 'RUN')
log = logging.getLogger('syslog')
log.setLevel(logging.DEBUG)

console = RichHandler()
console.setLevel(logging.INFO)
log.addHandler(console)

a = 0/0
class ByBot:
    def __init__(self) -> None:
        self.get_config()
        self.set_logger()
        log.info(f"ByBot initialized - {self.id}")
        log.log(11, '-'*30)
        log.log(11, f"ByBot initialized - {self.id}")
        log.log(11, f"Purpose: {self.desc}")
        log.log(11, f"Endpoint: {self.endpoint}")
        log.log(11, f"Launch date: {datetime.now()}")
        log.log(11, f"Balance: {self.get_balance()}")
        log.log(11, '-'*30)

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
            log.error(f"Could not get config - {e}")
            exit(84)

    def set_logger(self):
        log_path = f"./logs/{self.id}.log"
        fh = TimedRotatingFileHandler(log_path, when='midnight', interval=1, backupCount=4)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'))
        fh.rotation_filename = '{self.id}'
        fh.suffix = "%Y-%m-%d.log"
        log.addHandler(fh)

    def order_manager(self):
        log.debug(f"Order manager started")

    def get_balance(self):
        return self.session.get_wallet_balance(coin="USDT")['result']['USDT']['available_balance']
