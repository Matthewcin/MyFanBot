from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras

def register(bot):
    
    # --- ADMIN PRODUCTOS (Seleccionar Catálogo primero) ---
    @bot.callback_query_handler(func=lambda call: call.data == "admin_prods")
    def select_cat_for_prod(call):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM catalogos WHERE activo = TRUE")
        cats = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        for c in cats:
            markup.add(types.InlineKeyboardButton(f"📂 {c['nombre']}", callback_data=f"list_prod_{c['id']}"))
        markup.add(btn_atras("main_menu"))
        
        bot.edit_message_text("Selecciona el catálogo para gestionar productos:", 
                              call.message.chat.id, call.message.message_id, reply_markup=markup)

    # --- LISTAR PRODUCTOS DE UN CATÁLOGO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("list_prod_"))
    def list_products(call):
        cat_id = call.data.split("_")[2]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, precio FROM productos WHERE catalogo_id = %s", (cat_id,))
        prods = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p in prods:
            markup.add(types.InlineKeyboardButton(f"👕 {p['nombre']} (${p['precio']})", callback_data=f"edit_prod_{p['id']}"))
        
        markup.add(types.InlineKeyboardButton("➕ Nuevo Producto Aquí", callback_data=f"new_prod_ask_{cat_id}"))
        markup.add(btn_atras("admin_prods"))
        
        bot.edit_message_text(f"Productos en Catálogo ID {cat_id}:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # --- AGREGAR PRODUCTO (Paso 1: Nombre) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("new_prod_ask_"))
    def ask_prod_name(call):
        cat_id = call.data.split("_")[3]
        msg = bot.send_message(call.message.chat.id, "Escribe el **Nombre** del producto y el **Precio** separados por guion.\nEjemplo: `Remera Bad Bunny - 15000`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: save_product(m, cat_id))
        
    def save_product(message, cat_id):
        try:
            texto = message.text.split('-')
            nombre = texto[0].strip()
            precio = float(texto[1].strip())
            
            conn = get_connection()
            with conn.cursor() as cur:
                # Insertar producto
                cur.execute("INSERT INTO productos (catalogo_id, nombre, precio) VALUES (%s, %s, %s) RETURNING id", (cat_id, nombre, precio))
                prod_id = cur.fetchone()['id']
                # Crear stock inicial en 0 para tallas comunes
                tallas = ['S', 'M', 'L', 'XL']
                for t in tallas:
                    cur.execute("INSERT INTO inventario (producto_id, talla, stock) VALUES (%s, %s, 0)", (prod_id, t))
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, f"✅ Producto **{nombre}** creado con stock en 0.")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error formato incorrecto. Usa: Nombre - Precio. Error: {e}")

    # --- EDITAR STOCK (Ver tallas) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_prod_"))
    def edit_prod_stock(call):
        prod_id = call.data.split("_")[2]
        conn = get_connection()
        cur = conn.cursor()
        
        # Obtener info prod
        cur.execute("SELECT nombre FROM productos WHERE id = %s", (prod_id,))
        p_nombre = cur.fetchone()['nombre']
        
        # Obtener stock
        cur.execute("SELECT id, talla, stock FROM inventario WHERE producto_id = %s ORDER BY talla", (prod_id,))
        stock_data = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=3)
        botones = []
        for s in stock_data:
            # Botón para sumar stock: "S: 5 (+)"
            btn_text = f"{s['talla']}: {s['stock']}"
            botones.append(types.InlineKeyboardButton(btn_text, callback_data=f"add_stock_{s['id']}"))
        
        markup.add(*botones)
        markup.add(types.InlineKeyboardButton("❌ Borrar Producto", callback_data=f"del_prod_{prod_id}"))
        markup.add(btn_atras("admin_prods"))
        
        bot.edit_message_text(f"Gestionar Stock: **{p_nombre}**\nToca una talla para sumar 1 unidad.", 
                              call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # --- SUMAR STOCK RÁPIDO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("add_stock_"))
    def sumar_stock(call):
        inv_id = call.data.split("_")[2]
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE inventario SET stock = stock + 1 WHERE id = %s", (inv_id,))
            # Obtener prod_id para refrescar menu
            cur.execute("SELECT producto_id FROM inventario WHERE id = %s", (inv_id,))
            prod_id = cur.fetchone()['producto_id']
        conn.commit()
        conn.close()
        
        # Truco para refrescar el menú llamando a la función anterior
        call.data = f"edit_prod_{prod_id}"
        edit_prod_stock(call)