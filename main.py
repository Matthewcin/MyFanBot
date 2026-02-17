import os
import time
import telebot
from database.db import init_db

# 1. Importar el keep_alive desde la carpeta utils
from utils.keep_alive import start_server

# 2. Importar los handlers
from handlers import start, catalogs, products, shipping, statistics

# Intentar cargar .env solo si existe (para local), en Render no fallará si no está
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ERROR FATAL: No se encontró BOT_TOKEN en las variables de entorno.")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# 3. Inicializar DB
print("🛠 Inicializando base de datos...")
init_db()

# 4. Registrar Handlers
# Aquí es donde fallaba antes. Ahora start.register ya existe.
print("🔗 Conectando cerebros (handlers)...")
try:
    start.register(bot)
    catalogs.register(bot)
    products.register(bot)
    shipping.register(bot)
    statistics.register(bot)
    print("✅ Handlers cargados correctamente.")
except AttributeError as e:
    print(f"❌ ERROR CRÍTICO cargando handlers: {e}")
    exit(1)

# 5. Iniciar Servidor Web (Para que Render no mate el bot)
print("🌍 Iniciando servidor web de respaldo...")
start_server()

# 6. Loop principal
def main_loop():
    print("🤖 MyFanBox Bot Iniciado y escuchando...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ Error en polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main_loop()