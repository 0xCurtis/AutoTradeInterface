import json
import os
import pyfiglet
import pybit.inverse_futures
import pathlib

class ByBot:
    def __init__(self) -> None:
        try:
            with open('config.json', 'r') as cfg:
                cfg = json.load(cfg)
                self._api_key = cfg['creds']['api_key']
                self._api_secret = cfg['creds']['api_secret']
                self.endpoint = cfg['parameters']['endpoint']
                self.session = pybit.inverse_futures.HTTP(endpoint=self.endpoint, api_key=self._api_key, api_secret=self._api_secret)
                self.id = cfg['logging']['id']
                self.logpath = "./logs/{}".format(self.id)
                self.desc = cfg['logging']['desc']
                self.port = cfg['network']['port']
                pathlib.Path(self.logpath).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print("Error while initialising the bot - {}".format(e))
            exit(84)
    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        os.system('title ByBot V0.1')
        print(pyfiglet.figlet_format("ByBot V 0.1", font="slant"))
        app.run(debug=True, host="localhost", port=self.port)

    def __repr__(self) -> str:
        return("ByBot V0.1\n\tEndpoint : {}\n\tID : {}\n\tLogpath : {}\n\tDescription : {}".format(self.endpoint, self.id, self.logpath, self.desc))