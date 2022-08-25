from datetime import date
from module import Bybot as bb
from flask import Flask, request, json, g
import os
import pyfiglet

app = Flask(__name__)


# curl -i -X POST -H "Content-Type:application/json" -d "{\"pair\": \"BTCUSDT\", \"side\": \"Buy\"}" http://localhost:6670/open_order
@app.route('/open_order', methods=['POST'])
def new_order():
    auth_ip = ["REDACTED", "REDACTED", "REDACTED"]
    ip = request.remote_addr
    g.last_request = request.json
    bb.log(f"request by {ip}")
    if ip not in auth_ip:
        bb.error("Request not made by TradingView authorized ip list", False)
        # return "Not Authorized"
    if not bot.in_trade:
        bot.parse_order_data(g.last_request)
        return "Bien bouffon t'as fait ta requete"
    else:
        bb.log("Already in trade")
        return "Deja en trade"


if __name__ == "__main__":
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        bb.info('\n' + pyfiglet.figlet_format("ATM V0.1", font="slant"))
        bot = bb.ByBot()
        app.run(debug=False, host="localhost", port=bot.port)
        bb.info('\n' + repr(bot))
        bb.info("Bot stopped")
        exit(0)
    except KeyboardInterrupt:
        bb.info("Bot stopped during setup")
        exit(0)
