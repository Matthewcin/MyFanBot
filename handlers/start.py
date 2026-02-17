from telebot import types
from database.db import get_connection
from utils.keyboards import menu_principal_kb

def register(bot):
    # ¡IMPORTANTE! Todo el código debe estar identado dentro de esta función
    
    @bot.message_handler(commands=['start'])
    def command_start(message):
        uid = message.from_user.id
        nombre = message.from_user.first_name
        # Manejo seguro de username por si el usuario no tiene
        username = message.from_user.username if message.from_user.username else "SinUser"
        
        # Guardar o actualizar usuario en DB
        conn = get_connection()
        es_admin = False
        
        if conn:
            try:
                with conn.cursor() as cur:
                    # Insertar usuario si no existe
                    cur.execute("""
                        INSERT INTO usuarios (user_id, nombre, username) 
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id) DO NOTHING
                    """, (uid, nombre, username))
                    
                    # Chequear si es admin
                    cur.execute("SELECT rol FROM usuarios WHERE user_id = %s", (uid,))
                    res = cur.fetchone()
                    if res:
                        es_admin = res['rol'] == 'admin'
                conn.commit()
            except Exception as e:
                print(f"Error en start DB: {e}")
            finally:
                conn.close()

        bot.send_message(
            message.chat.id, 
            f"👋 Hola **{nombre}**, bienvenido a **MyFanBox**!\nTu tienda de ropa personalizada.",
            reply_markup=menu_principal_kb(es_admin),
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data == "main_menu")
    def back_main(call):
        # Re-verificar admin rápido
        conn = get_connection()
        es_admin = False
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT rol FROM usuarios WHERE user_id = %s", (call.from_user.id,))
                    res = cur.fetchone()
                    if res:
                        es_admin = res['rol'] == 'admin'
                conn.close()
            except:
                pass

        bot.edit_message_text(
            "🏠 **Menú Principal**",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=menu_principal_kb(es_admin),
            parse_mode="Markdown"
        )