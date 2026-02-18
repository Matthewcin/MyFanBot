import os
import time
import telebot
from database.db import init_db

# Imports handlers
from utils.keep_alive import start_server
from handlers import start, catalogs, products, shipping, statistics, sales 

# Carga variables (en Render no es necesario dotenv, pero por compatibilidad local se deja try)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ERROR FATAL: No se encontró BOT_TOKEN")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# 1. Inicializar DB
print("🛠 Inicializando base de datos...")
init_db()

# 2. Registrar Handlers
print("🔗 Conectando módulos...")
start.register(bot)
catalogs.register(bot)
products.register(bot)
shipping.register(bot)
statistics.register(bot)
sales.register(bot) # <-- REGISTRAR VENTAS

# 3. Servidor Web (Keep Alive)
print("🌍 Iniciando servidor web...")
start_server()

# 4. Loop
def main_loop():
    print("🤖 MyFanBox Bot Iniciado...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ Error en polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main_loop()