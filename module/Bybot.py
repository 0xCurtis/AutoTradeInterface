from email.policy import HTTP
import json
import os
import pybit.usdt_perpetual
import pathlib
from datetime import datetime
from threading import Thread, Event
import time

class ByBot:
    def __init__(self) -> None:
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

                self.logpath = "./logs/{}".format(self.id)
                self.logfile = self.logpath + "/logging.txt"
                self.make_log_header()
                pathlib.Path(self.logpath).mkdir(parents=True, exist_ok=True)
                self.in_trade = False

                self.thread = Thread(target=self.order_manager, daemon=True)
        except Exception as e:
            print("Error while initialising the bot - {}".format(e))
            exit(84)
    
    def order_manager(self):
        for a in range(500):
            time.sleep(0.1)
            print(a)
    
    def make_log_header(self):
        balance = self.get_balance()
        with open(self.logfile, 'a') as log:
            log.writelines("Purpose : {}\nID : {}\nEndpoint : {}\nLaunched on : {}\nBalance : {} USDT\n{}\n\n".format(self.desc, self.id, self.endpoint, datetime.now(), balance,'-'*30)) 
    
    def log(self, str):
        date_time = datetime.now()
        date_str = date_time.strftime("- %d/%m/%Y, %H:%M:%S:%f")
        with open(self.logfile, 'a') as log:
            log.writelines(date_str + " : " + str + '\n')

    def get_last_price(self, pair):
        price = self.session.public_trading_records(
            symbol=pair,
            limit=1
        )['result'][0]['price']
        return price
    
    def set_margin(self, buy=1, sell=1, pair=""):
        try:
            self.session.set_leverage(
                symbol=pair,
                buy_leverage=buy,
                sell_leverage=sell)
        except Exception as e:
            pass

    def get_balance(self):
        return self.session.get_wallet_balance(coin="USDT")['result']['USDT']['available_balance']

    def open_from_data(self, data):
        self.log("Request of {} on {} pair".format(data['side'], data['pair']))
        if self.flat == False:
            balance = self.get_balance()
            qty_in_usd = balance*(qty_in_usd/100)
        qty_in_usd = min(self.size, self.max_size)
        self.open_perp_order(pair=data['pair'], side=data['side'], qty_in_usd=qty_in_usd, lever=self.leverage, flat=True, sl=self.sl, tp=self.tp)

    def open_perp_order(self, pair="", side="", qty_in_usd=0, lever=1, flat=True, sl=None, tp=None):
        l_price = self.get_last_price(pair)
        quantity = round((qty_in_usd / l_price) * lever, 5)
        if sl != None:
            stop = l_price * (1 - sl/100) if side == "Buy" else l_price * (1 + sl/100)
        if tp != None:
            take = l_price * 1 + (tp/100) if side == "Buy" else l_price * 1 - (tp/100)
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
            stop_loss=stop
            )
        self.in_trade = True
        return res

    def __repr__(self) -> str:
        return("ByBot V0.1\n\tEndpoint : {}\n\tID : {}\n\tLogpath : {}\n\tDescription : {}".format(self.endpoint, self.id, self.logpath, self.desc))

if __name__ == "__main__":
    bot = ByBot()
    bot.thread.start()
    print("Yes")
    time.sleep(10)
    print("No")
    bot.thread.join()