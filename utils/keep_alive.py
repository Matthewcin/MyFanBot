from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "<h1>MyFanBox Bot está VIVO 🤖</h1>"

def run():
    # Render asigna un puerto en la variable de entorno PORT
    # Si no existe (local), usa el 8080
    port = int(os.environ.get("PORT", 8080))
    # host='0.0.0.0' es OBLIGATORIO para Render
    app.run(host='0.0.0.0', port=port)

def start_server():
    t = Thread(target=run)
    t.start()