# keep_alive.py
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "<h1>MyFanBox Bot is Alive! 🤖</h1>"

def run():
    # En Render, el puerto 0.0.0.0 es necesario para acceso externo
    app.run(host='0.0.0.0', port=8080)

def start_server():
    t = Thread(target=run)
    t.start()