import os
import time
import telebot
from utils.keep_alive import start_server
from database.db import init_db
from handlers import start, catalogs, products, shipping, statistics

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("❌ ERROR: FALTA BOT_TOKEN")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# Inicia DB (Borra todo si RESET_DB=True)
init_db()

# Cargar módulos
start.register(bot)
catalogs.register(bot)
products.register(bot)
shipping.register(bot)
statistics.register(bot)

# Servidor Web
start_server()

# Polling
def main():
    print("🤖 BOT INICIADO")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(e)
            time.sleep(5)

if __name__ == "__main__":
    main()