from datetime import date
from module import Bybot
from flask import Flask,request,json,g
import os
import pyfiglet

app = Flask(__name__)


# To test curl -i -X POST -H "Content-Type:application/json" -d "{\"pair\": \"BTCUSDT\", \"side\": \"Buy\"}" http://localhost:6670/atmnewtrade 
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
    print("after_request executing! BEDORE")
    if(bot.in_trade == False):
        bot.in_trade == True
        bot.open_from_data(g.last_request)
    else:
        bot.log("Already in trade")
    print("after_request executing!")
    return;

@app.before_first_request
def info():
    print(repr(bot))

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    os.system('title ATM V0.1')
    bot = Bybot.ByBot()
    print(pyfiglet.figlet_format("ATM V0.1", font="slant"))
    app.run(debug=False, host="localhost", port=bot.port)