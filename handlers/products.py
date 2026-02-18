from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras

# Memoria temporal
DRAFT_STOCK = {}     # { user_id: {'XS': 0, 'S': 5...} }
CURRENT_PROD = {}    # { user_id: prod_id }

def register(bot):
    
    # --- NIVEL 3: LISTAR PRODUCTOS ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("list_prod_"))
    def list_products(call):
        cat_id = call.data.split("_")[2]
        conn = get_connection()
        cur = conn.cursor()
        
        # Datos para volver atrás (al evento)
        cur.execute("SELECT nombre, evento_id FROM catalogos WHERE id = %s", (cat_id,))
        cat_data = cur.fetchone()
        
        cur.execute("SELECT id, nombre FROM productos WHERE catalogo_id = %s ORDER BY id DESC", (cat_id,))
        prods = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p in prods:
            markup.add(types.InlineKeyboardButton(f"👕 {p['nombre']}", callback_data=f"view_prod_{p['id']}"))
        
        markup.add(types.InlineKeyboardButton("➕ Nuevo Producto", callback_data=f"new_prod_ask_{cat_id}"))
        markup.add(btn_atras(f"open_event_{cat_data['evento_id']}")) 
        
        bot.edit_message_text(
            f"📂 Colección: **{cat_data['nombre']}**\nPrendas disponibles:",
            call.message.chat.id, call.message.message_id,
            reply_markup=markup, parse_mode="Markdown"
        )

    # --- VISTA DE PRODUCTO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("view_prod_"))
    def view_prod(call):
        pid = call.data.split("_")[2]
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT nombre, catalogo_id, precio FROM productos WHERE id = %s", (pid,))
        p = cur.fetchone()
        
        cur.execute("SELECT talla, stock FROM inventario WHERE producto_id = %s ORDER BY id", (pid,))
        stock = cur.fetchall()
        conn.close()
        
        txt = ""
        for s in stock:
            txt += f"• **{s['talla']}**: {s['stock']}\n"
            
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📦 CARGAR STOCK (WIZARD)", callback_data=f"wizard_start_{pid}"))
        markup.add(types.InlineKeyboardButton("🗑 Borrar Producto", callback_data=f"del_prod_{pid}"))
        markup.add(btn_atras(f"list_prod_{p['catalogo_id']}"))
        
        bot.edit_message_text(
            f"👕 **{p['nombre']}** (${p['precio']})\n\nStock Actual:\n{txt}",
            call.message.chat.id, call.message.message_id,
            reply_markup=markup, parse_mode="Markdown"
        )

    # --- NUEVO PRODUCTO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("new_prod_ask_"))
    def ask_prod(call):
        cat_id = call.data.split("_")[3]
        msg = bot.send_message(call.message.chat.id, "Escribe: `Nombre - Precio`\nEj: Remera - 25000", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: save_prod(m, cat_id))

    def save_prod(message, cat_id):
        try:
            parts = message.text.split('-')
            nom = parts[0].strip()
            pre = float(parts[1].strip())
            
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("INSERT INTO productos (catalogo_id, nombre, precio) VALUES (%s, %s, %s) RETURNING id", (cat_id, nom, pre))
                pid = cur.fetchone()['id']
                # Talles vacíos por defecto
                for t in ['XS', 'S', 'M', 'L', 'XL', 'XXL']:
                    cur.execute("INSERT INTO inventario (producto_id, talla, stock) VALUES (%s, %s, 0)", (pid, t))
            conn.commit()
            conn.close()
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Volver a Lista", callback_data=f"list_prod_{cat_id}"))
            bot.send_message(message.chat.id, f"✅ **{nom}** creado.", reply_markup=markup, parse_mode="Markdown")
        except:
            bot.send_message(message.chat.id, "❌ Error formato. Intenta de nuevo.")

    # ====================================================
    # 🧙‍♂️ WIZARD DE STOCK COMPLETO
    # ====================================================
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("wizard_start_"))
    def wizard_start(call):
        pid = call.data.split("_")[2]
        uid = call.from_user.id
        
        CURRENT_PROD[uid] = pid
        DRAFT_STOCK[uid] = {} # Limpio
        
        # Empezar por el primer talle
        ask_size_step(call.message, uid, 'XS')

    def ask_size_step(message, uid, talla):
        msg = bot.send_message(message.chat.id, f"📦 ¿Cuántas **{talla}** agregamos? (Escribe 0 si ninguna)", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: process_size_input(m, uid, talla))

    def process_size_input(message, uid, talla):
        if not message.text.strip().isdigit():
            bot.send_message(message.chat.id, "❌ Solo números enteros.")
            ask_size_step(message, uid, talla)
            return

        qty = int(message.text)
        DRAFT_STOCK[uid][talla] = qty
        
        # Siguiente talle
        talles = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        idx = talles.index(talla)
        
        if idx < len(talles) - 1:
            next_t = talles[idx + 1]
            ask_size_step(message, uid, next_t)
        else:
            show_confirmation(message.chat.id, uid)

    def show_confirmation(chat_id, uid):
        draft = DRAFT_STOCK[uid]
        lines = [f"• {t}: +{q}" for t, q in draft.items() if q > 0]
        summary = "\n".join(lines) if lines else "Nada (0)"
        
        txt = f"📝 **Confirmación de Carga**\n\nVas a sumar:\n{summary}\n\n¿Es correcto?"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ SÍ, Guardar", callback_data="stock_YES"))
        markup.add(types.InlineKeyboardButton("❌ NO, Corregir", callback_data="stock_NO"))
        
        bot.send_message(chat_id, txt, reply_markup=markup, parse_mode="Markdown")

    # --- CASO SI: GUARDAR ---
    @bot.callback_query_handler(func=lambda call: call.data == "stock_YES")
    def save_stock_db(call):
        uid = call.from_user.id
        pid = CURRENT_PROD.get(uid)
        draft = DRAFT_STOCK.get(uid)
        
        conn = get_connection()
        with conn.cursor() as cur:
            for t, q in draft.items():
                if q > 0:
                    cur.execute("UPDATE inventario SET stock = stock + %s WHERE producto_id = %s AND talla = %s", (q, pid, t))
        conn.commit()
        conn.close()
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ **Stock Actualizado.**", parse_mode="Markdown")
        
        # Volver al producto
        call.data = f"view_prod_{pid}"
        view_prod(call)

    # --- CASO NO: CORREGIR TALLE ESPECÍFICO ---
    @bot.callback_query_handler(func=lambda call: call.data == "stock_NO")
    def ask_fix_which(call):
        markup = types.InlineKeyboardMarkup(row_width=3)
        talles = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        btns = [types.InlineKeyboardButton(t, callback_data=f"fix_sz_{t}") for t in talles]
        markup.add(*btns)
        
        bot.edit_message_text("¿Qué talle quieres corregir?", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("fix_sz_"))
    def fix_specific_size(call):
        talla = call.data.split("_")[2]
        msg = bot.send_message(call.message.chat.id, f"Ok, ¿cuántas **{talla}** deberían ser realmente?", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: update_draft_single(m, talla))

    def update_draft_single(message, talla):
        uid = message.from_user.id
        if message.text.isdigit():
            DRAFT_STOCK[uid][talla] = int(message.text)
            show_confirmation(message.chat.id, uid)
        else:
            bot.send_message(message.chat.id, "❌ Error, ingresa número.")
            # Reiniciar flujo para este talle si falla
            fix_specific_size(message)