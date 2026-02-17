from database.db import get_connection
from utils.keyboards import menu_principal_kb

def register(bot):
    
    @bot.message_handler(commands=['start'])
    def command_start(message):
        uid = message.from_user.id
        nombre = message.from_user.first_name
        
        # Registrar Admin Automático
        conn = get_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO usuarios (user_id, nombre, username, rol) 
                    VALUES (%s, %s, %s, 'admin')
                    ON CONFLICT (user_id) DO NOTHING
                """, (uid, nombre, message.from_user.username or "Anon"))
            conn.commit()
            conn.close()

        bot.send_message(
            message.chat.id, 
            f"🛠 **Sistema MyFanBox**\nHola {nombre}, panel de inventario listo.",
            reply_markup=menu_principal_kb(),
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data == "main_menu")
    def back_main(call):
        bot.edit_message_text(
            "🛠 **Sistema MyFanBox**\nSelecciona opción:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=menu_principal_kb(),
            parse_mode="Markdown"
        )