from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras

def register(bot):
    
    # --- LISTAR CATÁLOGOS ---
    @bot.callback_query_handler(func=lambda call: call.data == "admin_cats")
    def listar_catalogos(call):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM catalogos WHERE activo = TRUE")
        cats = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for c in cats:
            # Botón para entrar al catálogo y ver opciones
            markup.add(types.InlineKeyboardButton(f"📂 {c['nombre']}", callback_data=f"gest_cat_{c['id']}"))
            
        markup.add(types.InlineKeyboardButton("➕ Nuevo Catálogo", callback_data="new_cat_ask"))
        markup.add(btn_atras("main_menu"))
        
        bot.edit_message_text("📂 **Gestión de Catálogos**\nSelecciona una colección para editarla:", 
                              call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # --- NUEVO CATÁLOGO ---
    @bot.callback_query_handler(func=lambda call: call.data == "new_cat_ask")
    def ask_cat_name(call):
        msg = bot.send_message(call.message.chat.id, "Escribe el nombre del **Nuevo Catálogo** (Ej: Taylor Swift):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_catalog)
        
    def save_catalog(message):
        nombre = message.text
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO catalogos (nombre) VALUES (%s)", (nombre,))
            conn.commit()
            bot.send_message(message.chat.id, f"✅ Catálogo **{nombre}** creado!")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: {e}")
        finally:
            conn.close()

    # --- OPCIONES DE CATÁLOGO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("gest_cat_"))
    def opciones_catalogo(call):
        cat_id = call.data.split("_")[2]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🗑 Eliminar Catálogo", callback_data=f"del_cat_{cat_id}"))
        markup.add(btn_atras("admin_cats"))
        
        bot.edit_message_text(f"Opciones para Catálogo ID: {cat_id}", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # --- BORRAR CATÁLOGO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("del_cat_"))
    def delete_catalogo(call):
        cat_id = call.data.split("_")[2]
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM catalogos WHERE id = %s", (cat_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Catálogo eliminado")
        listar_catalogos(call)