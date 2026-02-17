# handlers/catalogs.py
from telebot import types
from database.db import get_connection

def register_handlers(bot):
    
    # --- CALLBACKS ---
    @bot.callback_query_handler(func=lambda call: call.data == "admin_cats")
    def handle_ver_catalogos(call):
        # 1. Conectar a DB y traer catálogos
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM catalogos WHERE activo = TRUE")
        datos = cur.fetchall()
        conn.close()

        # 2. Armar teclado
        markup = types.InlineKeyboardMarkup(row_width=1)
        for cat_id, nombre in datos:
            markup.add(types.InlineKeyboardButton(f"📂 {nombre}", callback_data=f"open_cat_{cat_id}"))
        
        markup.add(types.InlineKeyboardButton("➕ Nuevo Catálogo", callback_data="new_cat_step"))
        markup.add(types.InlineKeyboardButton("🔙 Volver", callback_data="main_menu"))

        # 3. Editar mensaje
        bot.edit_message_text("📂 **Gestión de Catálogos**\nSelecciona una colección:", 
                              call.message.chat.id, 
                              call.message.message_id, 
                              reply_markup=markup,
                              parse_mode="Markdown")

    # --- LÓGICA DE CREACIÓN (STEPS) ---
    @bot.callback_query_handler(func=lambda call: call.data == "new_cat_step")
    def request_cat_name(call):
        msg = bot.send_message(call.message.chat.id, "Escribe el nombre del **Nuevo Catálogo**:")
        bot.register_next_step_handler(msg, save_new_catalog)

    def save_new_catalog(message):
        nombre = message.text
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO catalogos (nombre) VALUES (%s)", (nombre,))
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, f"✅ Catálogo **{nombre}** creado.")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: {e}")