from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras

def register(bot):
    
    # --- NIVEL 1: LISTAR EVENTOS ---
    @bot.callback_query_handler(func=lambda call: call.data == "admin_cats")
    def listar_eventos(call):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM eventos WHERE activo = TRUE")
        eventos = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for e in eventos:
            # Al tocar un evento, vamos a listar sus catálogos
            markup.add(types.InlineKeyboardButton(f"🎫 {e['nombre']}", callback_data=f"open_event_{e['id']}"))
            
        markup.add(types.InlineKeyboardButton("➕ Nuevo Evento", callback_data="new_event_ask"))
        markup.add(btn_atras("main_menu"))
        
        bot.edit_message_text("📂 **Selecciona un Evento:**", 
                              call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # --- CREAR EVENTO ---
    @bot.callback_query_handler(func=lambda call: call.data == "new_event_ask")
    def ask_event_name(call):
        msg = bot.send_message(call.message.chat.id, "Escribe el nombre del **Nuevo Evento** (Ej: 'Sabrina Carpenter 2026'):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_event)
        
    def save_event(message):
        nombre = message.text
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO eventos (nombre) VALUES (%s)", (nombre,))
            conn.commit()
            bot.send_message(message.chat.id, f"✅ Evento **{nombre}** creado!")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: {e}")
        finally:
            conn.close()

    # --- NIVEL 2: LISTAR CATÁLOGOS DEL EVENTO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_event_"))
    def listar_catalogos(call):
        evento_id = call.data.split("_")[2]
        
        conn = get_connection()
        cur = conn.cursor()
        # Traer nombre del evento para el titulo
        cur.execute("SELECT nombre FROM eventos WHERE id = %s", (evento_id,))
        evt_nombre = cur.fetchone()['nombre']
        
        # Traer catálogos de ese evento
        cur.execute("SELECT id, nombre FROM catalogos WHERE evento_id = %s AND activo = TRUE", (evento_id,))
        cats = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for c in cats:
            # Al tocar catalogo, vamos a productos (ver handlers/products.py)
            markup.add(types.InlineKeyboardButton(f"📂 {c['nombre']}", callback_data=f"list_prod_{c['id']}"))
            
        markup.add(types.InlineKeyboardButton("➕ Nuevo Catálogo Aquí", callback_data=f"new_cat_ask_{evento_id}"))
        markup.add(types.InlineKeyboardButton("🗑 Borrar Evento", callback_data=f"del_event_{evento_id}"))
        markup.add(btn_atras("admin_cats"))
        
        bot.edit_message_text(f"🎫 Evento: **{evt_nombre}**\nSelecciona una colección:", 
                              call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # --- CREAR CATÁLOGO EN EVENTO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("new_cat_ask_"))
    def ask_cat_name(call):
        evento_id = call.data.split("_")[3]
        msg = bot.send_message(call.message.chat.id, "Escribe el nombre de la **Colección/Catálogo** (Ej: 'Blue Dream'):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: save_catalog(m, evento_id))
        
    def save_catalog(message, evento_id):
        nombre = message.text
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO catalogos (nombre, evento_id) VALUES (%s, %s)", (nombre, evento_id))
            conn.commit()
            bot.send_message(message.chat.id, f"✅ Colección **{nombre}** creada!")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: {e}")
        finally:
            conn.close()

    # --- BORRAR EVENTO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("del_event_"))
    def delete_event(call):
        eid = call.data.split("_")[2]
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM eventos WHERE id = %s", (eid,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Evento eliminado")
        listar_eventos(call)