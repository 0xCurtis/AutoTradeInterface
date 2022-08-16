import os
from time import sleep
from module import Bybot_copy
from flask import Flask,request,g

app = Flask(__name__)

@app.route('/atmnewtrade',methods=['POST'])
def develinput():
    auth_ip = ["REDACTED","REDACTED","REDACTED"]
    ip = request.remote_addr
    g.last_request = request.json
    bot.log("request by {}".format(ip))
    if (ip not in auth_ip):
        bot.log("Request not made by TradingView authorized ip list")
        #return "Not Authorized"
    if(bot.in_trade == False):
        return "Bien bouffon t'as fait ta requete"
    else:
        return "Deja en trade"
    
@app.after_request
def after_req_process(response):
    if(bot.in_trade == False):
        bot.in_trade == True
        bot.parse_order_data(g.last_request)
    else:
        bot.log("Already in trade")
    return

if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')
    if not os.path.exists("logs"):
        os.makedirs("logs")
    bot = Bybot_copy.ByBot()
    sleep(1)
    Bybot_copy.logger.info(repr(bot))
    app.run(debug=False, host="localhost", port=bot.port)
    exit(0)