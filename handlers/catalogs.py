from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras

def register(bot):
    
    # --- NIVEL 1: LISTAR EVENTOS ---
    @bot.callback_query_handler(func=lambda call: call.data == "admin_events")
    def listar_eventos(call):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM eventos WHERE activo = TRUE ORDER BY id DESC")
        eventos = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for e in eventos:
            markup.add(types.InlineKeyboardButton(f"🎫 {e['nombre']}", callback_data=f"open_event_{e['id']}"))
            
        markup.add(types.InlineKeyboardButton("➕ Nuevo Evento", callback_data="new_event_ask"))
        markup.add(btn_atras("main_menu"))
        
        bot.edit_message_text(
            "📂 **Mis Eventos**\nSelecciona el evento para ver sus catálogos:", 
            call.message.chat.id, call.message.message_id, 
            reply_markup=markup, parse_mode="Markdown"
        )

    # --- CREAR EVENTO ---
    @bot.callback_query_handler(func=lambda call: call.data == "new_event_ask")
    def ask_event(call):
        msg = bot.send_message(call.message.chat.id, "Escribe el nombre del **Nuevo Evento**:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_event)
        
    def save_event(message):
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("INSERT INTO eventos (nombre) VALUES (%s)", (message.text,))
            conn.commit()
            conn.close()
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Volver a Lista", callback_data="admin_events"))
            bot.send_message(message.chat.id, f"✅ Evento **{message.text}** creado.", reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: {e}")

    # --- NIVEL 2: CATÁLOGOS DEL EVENTO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_event_"))
    def listar_catalogos(call):
        eid = call.data.split("_")[2]
        conn = get_connection()
        cur = conn.cursor()
        
        # Nombre Evento
        cur.execute("SELECT nombre FROM eventos WHERE id = %s", (eid,))
        ename = cur.fetchone()['nombre']
        
        # Catálogos
        cur.execute("SELECT id, nombre FROM catalogos WHERE evento_id = %s AND activo = TRUE ORDER BY id DESC", (eid,))
        cats = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for c in cats:
            markup.add(types.InlineKeyboardButton(f"📂 {c['nombre']}", callback_data=f"list_prod_{c['id']}"))
            
        markup.add(types.InlineKeyboardButton("➕ Nuevo Catálogo", callback_data=f"new_cat_ask_{eid}"))
        markup.add(types.InlineKeyboardButton("🗑 Eliminar Evento", callback_data=f"del_event_{eid}"))
        markup.add(btn_atras("admin_events"))
        
        bot.edit_message_text(
            f"🎫 Evento: **{ename}**\nSelecciona Colección:",
            call.message.chat.id, call.message.message_id,
            reply_markup=markup, parse_mode="Markdown"
        )

    # --- CREAR CATÁLOGO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("new_cat_ask_"))
    def ask_cat(call):
        eid = call.data.split("_")[3]
        msg = bot.send_message(call.message.chat.id, "Nombre de la **Colección**:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: save_cat(m, eid))

    def save_cat(message, eid):
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("INSERT INTO catalogos (nombre, evento_id) VALUES (%s, %s)", (message.text, eid))
            conn.commit()
            conn.close()
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Volver al Evento", callback_data=f"open_event_{eid}"))
            bot.send_message(message.chat.id, f"✅ Colección **{message.text}** creada.", reply_markup=markup, parse_mode="Markdown")
        except:
            bot.send_message(message.chat.id, "❌ Error.")

    # --- BORRAR EVENTO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("del_event_"))
    def del_event(call):
        eid = call.data.split("_")[2]
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM eventos WHERE id = %s", (eid,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Evento Eliminado")
        call.data = "admin_events"
        listar_eventos(call)