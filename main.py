import os
import time
import telebot
from dotenv import load_dotenv
from utils.keep_alive import start_server
from database.db import init_db

# Handlers
from handlers import start, catalogs, products, shipping, statistics

# Cargar .env si estás en local (en Render no hace falta si configuras las variables)
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ERROR: No se encontró BOT_TOKEN")
    exit()

bot = telebot.TeleBot(TOKEN)

# 1. Iniciar DB
init_db()

# 2. Registrar Handlers
start.register(bot)
catalogs.register(bot)
products.register(bot)
shipping.register(bot)
statistics.register(bot)

# 3. Iniciar Servidor Keep Alive (Para UptimeRobot)
start_server()

# 4. Loop principal con reconexión automática
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