from module import Bybot
from flask import Flask,request,json

app = Flask(__name__)

# To test curl -i -X POST -H "Content-Type:application/json" -d "{\"pair\": \"BTCUSDT\", \"side\": \"BUY\"}" http://localhost:5000/develinput
@app.route('/develinput',methods=['POST'])
def develinput():
    auth_ip = ["REDACTED","REDACTED","REDACTED"]
    data = request.json
    ip = request.remote_addr
    if (ip not in auth_ip):
        print("\nRequest not made by REDACTED auth ip list\n")
    print(data)
    print(ip)
    return data

@app.before_first_request
def info():
    print(repr(bot))


bot = Bybot.ByBot()
bot.run()