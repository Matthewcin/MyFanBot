from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras

def register(bot):
    
    # ==========================================
    # NIVEL 1: LISTAR EVENTOS
    # ==========================================
    # CORRECCIÓN: Ahora escucha 'admin_cats' que es lo que envía el botón del menú
    @bot.callback_query_handler(func=lambda call: call.data == "admin_cats")
    def listar_eventos(call):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nombre FROM eventos WHERE activo = TRUE ORDER BY id DESC")
                eventos = cur.fetchall()
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            for e in eventos:
                # Al tocar un evento, vamos a listar sus catálogos
                markup.add(types.InlineKeyboardButton(f"🎫 {e['nombre']}", callback_data=f"open_event_{e['id']}"))
                
            markup.add(types.InlineKeyboardButton("➕ Nuevo Evento", callback_data="new_event_ask"))
            markup.add(btn_atras("main_menu"))
            
            bot.edit_message_text(
                "📂 **Gestión de Stock**\nSelecciona el Evento:", 
                call.message.chat.id, call.message.message_id, 
                reply_markup=markup, parse_mode="Markdown"
            )
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Error DB: {e}")
        finally:
            if conn: conn.close()

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
            
            markup = types.InlineKeyboardMarkup()
            # OJO: Aquí debe volver a 'admin_cats'
            markup.add(types.InlineKeyboardButton("🔙 Volver a Eventos", callback_data="admin_cats"))
            bot.send_message(message.chat.id, f"✅ Evento **{nombre}** creado!", reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: {e}")
        finally:
            if conn: conn.close()

    # ==========================================
    # NIVEL 2: LISTAR CATÁLOGOS DEL EVENTO
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_event_"))
    def listar_catalogos(call):
        evento_id = call.data.split("_")[2]
        
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Nombre del evento
                cur.execute("SELECT nombre FROM eventos WHERE id = %s", (evento_id,))
                res = cur.fetchone()
                if not res:
                    bot.answer_callback_query(call.id, "Evento no encontrado")
                    return
                evt_nombre = res['nombre']
                
                # Catálogos
                cur.execute("SELECT id, nombre FROM catalogos WHERE evento_id = %s AND activo = TRUE ORDER BY id DESC", (evento_id,))
                cats = cur.fetchall()
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            for c in cats:
                # Ir a productos
                markup.add(types.InlineKeyboardButton(f"📂 {c['nombre']}", callback_data=f"list_prod_{c['id']}"))
                
            markup.add(types.InlineKeyboardButton("➕ Nueva Colección", callback_data=f"new_cat_ask_{evento_id}"))
            markup.add(types.InlineKeyboardButton("🗑 Borrar Evento", callback_data=f"del_event_{evento_id}"))
            # Volver a la lista de eventos (admin_cats)
            markup.add(btn_atras("admin_cats"))
            
            bot.edit_message_text(
                f"🎫 Evento: **{evt_nombre}**\nSelecciona una colección:", 
                call.message.chat.id, call.message.message_id, 
                reply_markup=markup, parse_mode="Markdown"
            )
        except Exception as e:
            bot.send_message(call.message.chat.id, f"Error: {e}")
        finally:
            if conn: conn.close()

    # --- CREAR CATÁLOGO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("new_cat_ask_"))
    def ask_cat_name(call):
        evento_id = call.data.split("_")[3]
        msg = bot.send_message(call.message.chat.id, "Escribe el nombre de la **Colección** (Ej: 'Blue Dream'):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: save_catalog(m, evento_id))
        
    def save_catalog(message, evento_id):
        nombre = message.text
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO catalogos (nombre, evento_id) VALUES (%s, %s)", (nombre, evento_id))
            conn.commit()
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Volver al Evento", callback_data=f"open_event_{evento_id}"))
            bot.send_message(message.chat.id, f"✅ Colección **{nombre}** creada!", reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: {e}")
        finally:
            if conn: conn.close()

    # --- BORRAR EVENTO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("del_event_"))
    def delete_event(call):
        eid = call.data.split("_")[2]
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM eventos WHERE id = %s", (eid,))
            conn.commit()
            bot.answer_callback_query(call.id, "Evento eliminado")
            
            # Truco: Cambiamos el 'call.data' para que la función listar_eventos crea que se tocó el botón principal
            call.data = "admin_cats"
            listar_eventos(call)
        except Exception as e:
            bot.answer_callback_query(call.id, "No se pudo borrar.")
        finally:
            if conn: conn.close()