from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras

# Memoria temporal para la carga de stock: { user_id: { 'S': 0, 'M': 5 ... } }
DRAFT_STOCK = {}
CURRENT_PROD_EDIT = {} # { user_id: prod_id }

def register(bot):
    
    # --- LISTAR PRODUCTOS ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("list_prod_"))
    def list_products(call):
        cat_id = call.data.split("_")[2]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, precio FROM productos WHERE catalogo_id = %s", (cat_id,))
        prods = cur.fetchall()
        
        # Necesitamos saber el evento_id para el botón volver
        cur.execute("SELECT evento_id FROM catalogos WHERE id = %s", (cat_id,))
        evento_id = cur.fetchone()['evento_id']
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p in prods:
            markup.add(types.InlineKeyboardButton(f"👕 {p['nombre']}", callback_data=f"view_prod_{p['id']}"))
        
        markup.add(types.InlineKeyboardButton("➕ Nuevo Producto", callback_data=f"new_prod_ask_{cat_id}"))
        markup.add(btn_atras(f"open_event_{evento_id}")) # Volver al Evento
        
        bot.edit_message_text(f"Productos en este Catálogo:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # --- CREAR PRODUCTO (Simplificado) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("new_prod_ask_"))
    def ask_prod_name(call):
        cat_id = call.data.split("_")[3]
        msg = bot.send_message(call.message.chat.id, "Nombre - Precio (Ej: 'Baby Tee - 25000'):")
        bot.register_next_step_handler(msg, lambda m: save_product(m, cat_id))

    def save_product(message, cat_id):
        try:
            datos = message.text.split('-')
            nombre = datos[0].strip()
            precio = float(datos[1].strip())
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("INSERT INTO productos (catalogo_id, nombre, precio) VALUES (%s, %s, %s) RETURNING id", (cat_id, nombre, precio))
                prod_id = cur.fetchone()['id']
                # Crear talles base en 0
                for t in ['XS', 'S', 'M', 'L', 'XL', 'XXL']:
                    cur.execute("INSERT INTO inventario (producto_id, talla, stock) VALUES (%s, %s, 0)", (prod_id, t))
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, f"✅ Producto **{nombre}** creado.")
        except:
            bot.send_message(message.chat.id, "❌ Error formato.")

    # --- VER PRODUCTO Y STOCK ACTUAL ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("view_prod_"))
    def view_product(call):
        prod_id = call.data.split("_")[2]
        conn = get_connection()
        cur = conn.cursor()
        
        # Info producto
        cur.execute("SELECT nombre, catalogo_id FROM productos WHERE id = %s", (prod_id,))
        p_data = cur.fetchone()
        
        # Info Stock
        cur.execute("SELECT talla, stock FROM inventario WHERE producto_id = %s ORDER BY id", (prod_id,))
        stock_lines = cur.fetchall()
        conn.close()
        
        txt_stock = "\n".join([f"• **{s['talla']}**: {s['stock']}" for s in stock_lines])
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📦 CARGAR STOCK (Asistente)", callback_data=f"wizard_stock_{prod_id}"))
        markup.add(types.InlineKeyboardButton("❌ Borrar Producto", callback_data=f"del_prod_{prod_id}"))
        markup.add(btn_atras(f"list_prod_{p_data['catalogo_id']}"))
        
        bot.edit_message_text(f"👕 **{p_data['nombre']}**\n\nStock Actual:\n{txt_stock}", 
                              call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # ==========================================
    # 🧙‍♂️ ASISTENTE DE CARGA DE STOCK (WIZARD)
    # ==========================================

    @bot.callback_query_handler(func=lambda call: call.data.startswith("wizard_stock_"))
    def start_stock_wizard(call):
        prod_id = call.data.split("_")[2]
        uid = call.from_user.id
        
        # Inicializamos el borrador en 0 para todos los talles
        CURRENT_PROD_EDIT[uid] = prod_id
        DRAFT_STOCK[uid] = {'XS': 0, 'S': 0, 'M': 0, 'L': 0, 'XL': 0, 'XXL': 0}
        
        # Empezamos preguntando por el primer talle: XS
        msg = bot.send_message(call.message.chat.id, "📦 **Carga de Stock**\n\n¿Cuántas **XS** vas a agregar? (Escribe 0 si ninguna)")
        bot.register_next_step_handler(msg, lambda m: ask_next_size(m, 'XS'))

    def ask_next_size(message, current_size):
        uid = message.from_user.id
        
        # Validar que sea numero
        try:
            qty = int(message.text)
        except:
            bot.send_message(message.chat.id, "❌ Debe ser un número entero. Intenta de nuevo:")
            bot.register_next_step_handler(message, lambda m: ask_next_size(m, current_size))
            return

        # Guardar en borrador
        DRAFT_STOCK[uid][current_size] = qty
        
        # Definir el orden de talles
        talles_orden = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        idx_actual = talles_orden.index(current_size)
        
        if idx_actual < len(talles_orden) - 1:
            # Preguntar por el siguiente talle
            next_size = talles_orden[idx_actual + 1]
            msg = bot.send_message(message.chat.id, f"¿Cuántas **{next_size}** vas a agregar?")
            bot.register_next_step_handler(msg, lambda m: ask_next_size(m, next_size))
        else:
            # Terminamos de preguntar todos, mostramos RESUMEN
            show_confirmation(message.chat.id, uid)

    def show_confirmation(chat_id, uid):
        draft = DRAFT_STOCK[uid]
        # Filtrar solo los que suman algo para el mensaje
        resumen = "\n".join([f"{t}: +{q}" for t, q in draft.items() if q > 0])
        
        if not resumen: resumen = "No se agregará nada."
        
        txt = f"📝 **Confirmación de Carga**\n\nVas a sumar al stock:\n{resumen}\n\n¿Es correcto?"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ SÍ, Guardar", callback_data="confirm_stock_yes"))
        markup.add(types.InlineKeyboardButton("❌ NO, corregir talle", callback_data="confirm_stock_no"))
        
        bot.send_message(chat_id, txt, reply_markup=markup, parse_mode="Markdown")

    # --- CONFIRMACIÓN: SI ---
    @bot.callback_query_handler(func=lambda call: call.data == "confirm_stock_yes")
    def save_stock_db(call):
        uid = call.from_user.id
        prod_id = CURRENT_PROD_EDIT.get(uid)
        draft = DRAFT_STOCK.get(uid)
        
        if not prod_id or not draft:
            bot.send_message(call.message.chat.id, "❌ Error de sesión. Empieza de nuevo.")
            return

        conn = get_connection()
        with conn.cursor() as cur:
            for talla, cantidad in draft.items():
                if cantidad > 0:
                    # Sumamos al stock existente
                    cur.execute("""
                        UPDATE inventario 
                        SET stock = stock + %s 
                        WHERE producto_id = %s AND talla = %s
                    """, (cantidad, prod_id, talla))
        conn.commit()
        conn.close()
        
        bot.edit_message_text("✅ **Stock Actualizado Exitosamente**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        
        # Volver a ver el producto
        # Simulamos un callback para recargar la vista del producto
        call.data = f"view_prod_{prod_id}"
        view_product(call)

    # --- CONFIRMACIÓN: NO (CORREGIR) ---
    @bot.callback_query_handler(func=lambda call: call.data == "confirm_stock_no")
    def ask_which_fix(call):
        markup = types.InlineKeyboardMarkup(row_width=3)
        talles = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        btns = [types.InlineKeyboardButton(t, callback_data=f"fix_size_{t}") for t in talles]
        markup.add(*btns)
        
        bot.edit_message_text("¿Qué talle quieres corregir?", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("fix_size_"))
    def fix_specific_size(call):
        talla = call.data.split("_")[2]
        msg = bot.send_message(call.message.chat.id, f"Entendido. ¿Cuántas **{talla}** deberían ser realmente?")
        bot.register_next_step_handler(msg, lambda m: update_draft_and_show(m, talla))

    def update_draft_and_show(message, talla):
        uid = message.from_user.id
        try:
            qty = int(message.text)
            DRAFT_STOCK[uid][talla] = qty
            show_confirmation(message.chat.id, uid)
        except:
            bot.send_message(message.chat.id, "❌ Número inválido.")