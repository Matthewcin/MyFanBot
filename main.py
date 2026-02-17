# main.py
import os
import telebot
from keep_alive import start_server
from database.db import init_db

# Importamos los handlers desde la carpeta
from handlers import start, catalogs, products, shipping

# 1. Obtener Token desde Variables de Entorno de Render
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ El BOT_TOKEN no está configurado en las variables de entorno.")

bot = telebot.TeleBot(TOKEN)

# 2. Inicializar Base de Datos
init_db()

# 3. Registrar los Handlers (Pasamos el objeto 'bot' a cada archivo)
# Cada archivo debe tener una función 'register(bot)'
start.register(bot)
catalogs.register(bot)
products.register(bot)
shipping.register(bot)

# 4. Arrancar el servidor Keep Alive (Antes del polling)
start_server()

# 5. Iniciar el Bot
print("🤖 MyFanBox Bot Iniciado y escuchando...")
bot.infinity_polling()