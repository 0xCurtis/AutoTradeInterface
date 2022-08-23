from datetime import date
from module import Bybot
from flask import Flask, request, json, g
import os
import pyfiglet

app = Flask(__name__)


# To test curl -i -X POST -H "Content-Type:application/json" -d
# "{\"pair\": \"BTCUSDT\", \"side\": \"Buy\"}" http://localhost:6670/atmnewtrade
@app.route('/atmnewtrade', methods=['POST'])
def develinput():
    auth_ip = ["REDACTED", "REDACTED", "REDACTED"]
    ip = request.remote_addr
    g.last_request = request.json
    bb.log("request by {}".format(ip))
    if ip not in auth_ip:
        bb.error("Request not made by TradingView authorized ip list")
        # return "Not Authorized"
    if not bot.in_trade:
        return "Bien bouffon t'as fait ta requete"
    else:
        return "Deja en trade"


@app.after_request
def after_req_process(response):
    bb.info("after_request executing! BEDORE")
    if not bot.in_trade:
        bot.parse_order_data(g.last_request)
    else:
        bb.log("Already in trade")
    bb.info("after_request executing!")
    return


if __name__ == "__main__":
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        # os.system('title ATM V0.1')
        bb = Bybot
        bb.info('\n'+pyfiglet.figlet_format("ATM V0.1", font="slant"))
        bot = bb.ByBot()
        app.run(debug=False, host="localhost", port=bot.port)
        bb.info('\n'+repr(bot))
        bb.info("Bot stopped")
        exit(0)
    except KeyboardInterrupt:
        Bybot.info("Bot stopped during setup")
        exit(0)
