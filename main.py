import os
import time
import telebot
from utils.keep_alive import start_server
from database.db import init_db
# Importamos el nuevo módulo 'sales'
from handlers import start, catalogs, products, shipping, statistics, sales

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("❌ ERROR: FALTA BOT_TOKEN")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# Iniciar DB (RESET_DB=True la primera vez)
init_db()

# Registrar Handlers
start.register(bot)
catalogs.register(bot)
products.register(bot)
shipping.register(bot)
statistics.register(bot)
sales.register(bot) # <-- REGISTRAMOS VENTAS

# Servidor Web
start_server()

# Polling
def main():
    print("🤖 MYFANBOX BOT ONLINE")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(e)
            time.sleep(5)

if __name__ == "__main__":
    main()