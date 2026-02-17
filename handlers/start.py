from telebot import types
from database.db import get_connection
from utils.keyboards import menu_principal_kb

def register(bot):
    
    @bot.message_handler(commands=['start'])
    def command_start(message):
        uid = message.from_user.id
        nombre = message.from_user.first_name
        username = message.from_user.username or "SinUser"
        
        # Registrar usuario AUTOMÁTICAMENTE como ADMIN
        conn = get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO usuarios (user_id, nombre, username, rol) 
                        VALUES (%s, %s, %s, 'admin')
                        ON CONFLICT (user_id) DO NOTHING
                    """, (uid, nombre, username))
                conn.commit()
            except Exception as e:
                print(f"Error DB Start: {e}")
            finally:
                conn.close()

        # Mensaje directo de herramienta de trabajo
        bot.send_message(
            message.chat.id, 
            f"🛠 **Panel de Control - MyFanBox**\n\nHola {nombre}, sistema de inventario listo.\nSelecciona una operación:",
            reply_markup=menu_principal_kb(),
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data == "main_menu")
    def back_main(call):
        bot.edit_message_text(
            "🛠 **Panel de Control - MyFanBox**\nSelecciona una operación:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=menu_principal_kb(),
            parse_mode="Markdown"
        )