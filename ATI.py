import os

import pyfiglet
from flask import Flask, request

from module import BB

app = Flask(__name__)
authorized_ips = ["52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7"]


# curl -i -X POST -H "Content-Type:application/json" -d "{\"pair\": \"BTCUSDT\", \"symbol\": \"Buy\"}" http://localhost:6670/open_order
@app.route('/open_order', methods=['POST'])
def open_order():
    order_ip = request.remote_addr
    BB.info(f"Incoming request from {order_ip}")
    if order_ip not in authorized_ips:
        BB.error("Unauthorized ip", False)
        # return "Not Authorized"
    if bot.trading:
        BB.log("Request rejected  (already in trade)")
        return "Request rejected (already in trade)"
    else:
        r = request.json
        try:
            bot.open_order(r['side'], r['symbol'])
        except NameError as e:
            BB.error(f"Missing request parameter: {e}")
            return f"Missing request parameter: {e}"
        return "Request received"


if __name__ == "__main__":
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        BB.info('\n' + pyfiglet.figlet_format("ATI V0.1", font="slant"))
        bot = BB.ByBot()
        app.run(host=bot.network['host'], port=bot.network['port'])
        BB.info("Bot stopped")
        exit(0)
    except KeyboardInterrupt:
        BB.info("Bot stopped during setup")
        exit(0)
    except BB.FailedRequestError:
        BB.error("Request error")
        raise
