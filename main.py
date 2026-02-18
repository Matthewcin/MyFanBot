import os
import time
import telebot
from database.db import init_db

# Imports handlers
from utils.keep_alive import start_server
from handlers import start, catalogs, products, shipping, statistics, sales 

# Carga variables
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
sales.register(bot)

# 3. Servidor Web (Keep Alive)
print("🌍 Iniciando servidor web...")
start_server()

# 4. Loop Principal (BLINDADO)
def main_loop():
    print("🤖 MyFanBox Bot Iniciado...")
    
    # TRUCO: Borrar webhook previo para evitar conflictos fantasma
    try:
        bot.delete_webhook()
        time.sleep(1)
    except Exception as e:
        print(f"⚠️ Webhook cleanup: {e}")

    while True:
        try:
            # timeout=60 reduce la cantidad de peticiones por minuto, bajando probabilidad de conflicto
            print("🔄 Conectando a Telegram...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60, allowed_updates=["message", "callback_query"])
            
        except Exception as e:
            print(f"⚠️ Error en polling: {e}")
            # Si el error es 409 (Conflict), esperamos más tiempo para que el otro proceso muera
            if "409" in str(e):
                print("🛑 Conflicto detectado (Doble instancia). Esperando 10 segundos...")
                time.sleep(10)
            else:
                time.sleep(5)

if __name__ == "__main__":
    main_loop()