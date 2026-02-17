from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "<h1>MyFanBox Bot está VIVO 🤖</h1>"

def run():
    # 0.0.0.0 es necesario para Docker/Render
    app.run(host='0.0.0.0', port=8080)

def start_server():
    t = Thread(target=run)
    t.start()