from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras

def register(bot):
    
    # ==========================================
    # 1. SELECCIONAR EVENTO PARA VENDER
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data == "start_sale")
    def sale_select_event(call):
        conn = get_connection()
        cur = conn.cursor()
        # Solo eventos activos
        cur.execute("SELECT id, nombre FROM eventos WHERE activo = TRUE")
        eventos = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for e in eventos:
            markup.add(types.InlineKeyboardButton(f"🎫 {e['nombre']}", callback_data=f"sell_evt_{e['id']}"))
        markup.add(btn_atras("main_menu"))
        
        bot.edit_message_text(
            "💰 **Nueva Venta**\nSelecciona el Evento:", 
            call.message.chat.id, call.message.message_id, 
            reply_markup=markup, parse_mode="Markdown"
        )

    # ==========================================
    # 2. SELECCIONAR CATÁLOGO
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("sell_evt_"))
    def sale_select_cat(call):
        eid = call.data.split("_")[2]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM catalogos WHERE evento_id = %s AND activo = TRUE", (eid,))
        cats = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for c in cats:
            markup.add(types.InlineKeyboardButton(f"📂 {c['nombre']}", callback_data=f"sell_cat_{c['id']}"))
        markup.add(btn_atras("start_sale"))
        
        bot.edit_message_text(
            "💰 Selecciona la Colección:", 
            call.message.chat.id, call.message.message_id, 
            reply_markup=markup, parse_mode="Markdown"
        )

    # ==========================================
    # 3. SELECCIONAR PRENDA
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("sell_cat_"))
    def sale_select_prod(call):
        cid = call.data.split("_")[2]
        conn = get_connection()
        cur = conn.cursor()
        # Necesitamos el ID del evento para el botón "Atrás"
        cur.execute("SELECT evento_id FROM catalogos WHERE id = %s", (cid,))
        eid = cur.fetchone()['evento_id']
        
        cur.execute("SELECT id, nombre, precio FROM productos WHERE catalogo_id = %s", (cid,))
        prods = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p in prods:
            markup.add(types.InlineKeyboardButton(f"👕 {p['nombre']} (${p['precio']})", callback_data=f"sell_prod_{p['id']}"))
        markup.add(btn_atras(f"sell_evt_{eid}"))
        
        bot.edit_message_text(
            "💰 Selecciona la Prenda a vender:", 
            call.message.chat.id, call.message.message_id, 
            reply_markup=markup, parse_mode="Markdown"
        )

    # ==========================================
    # 4. SELECCIONAR TALLE (SOLO CON STOCK)
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("sell_prod_"))
    def sale_select_size(call):
        pid = call.data.split("_")[2]
        conn = get_connection()
        cur = conn.cursor()
        
        # Info producto
        cur.execute("SELECT nombre, precio, catalogo_id FROM productos WHERE id = %s", (pid,))
        prod = cur.fetchone()
        
        # Stock disponible
        cur.execute("SELECT talla, stock FROM inventario WHERE producto_id = %s ORDER BY id", (pid,))
        stock = cur.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=3)
        btns = []
        for s in stock:
            # Texto del botón: "L (5)" o "L (AGOTADO)"
            if s['stock'] > 0:
                txt = f"{s['talla']} ({s['stock']})"
                # El callback guarda: sell_confirm_PRODID_TALLE
                btns.append(types.InlineKeyboardButton(txt, callback_data=f"sell_conf_{pid}_{s['talla']}"))
            else:
                # Botón deshabilitado visualmente (aunque clickeable, no hará nada o dará error)
                btns.append(types.InlineKeyboardButton(f"🚫 {s['talla']}", callback_data="ignore"))
        
        markup.add(*btns)
        markup.add(btn_atras(f"sell_cat_{prod['catalogo_id']}"))
        
        bot.edit_message_text(
            f"💰 Vendiendo: **{prod['nombre']}**\nPrecio: **${prod['precio']}**\n\nSelecciona el talle vendido:", 
            call.message.chat.id, call.message.message_id, 
            reply_markup=markup, parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data == "ignore")
    def ignore_click(call):
        bot.answer_callback_query(call.id, "❌ Sin stock de este talle.")

    # ==========================================
    # 5. CONFIRMAR Y EJECUTAR VENTA
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("sell_conf_"))
    def execute_sale(call):
        parts = call.data.split("_")
        pid = parts[2]
        talla = parts[3]
        
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # 1. Verificar stock una última vez
                cur.execute("SELECT stock FROM inventario WHERE producto_id = %s AND talla = %s", (pid, talla))
                res = cur.fetchone()
                
                if not res or res['stock'] < 1:
                    bot.answer_callback_query(call.id, "❌ ¡Error! Alguien acaba de llevarse el último.")
                    return

                # 2. Obtener datos para el historial
                cur.execute("SELECT nombre, precio FROM productos WHERE id = %s", (pid,))
                prod = cur.fetchone()
                
                # 3. RESTAR STOCK
                cur.execute("UPDATE inventario SET stock = stock - 1 WHERE producto_id = %s AND talla = %s", (pid, talla))
                
                # 4. GUARDAR VENTA
                cur.execute("""
                    INSERT INTO ventas (producto_id, nombre_producto, talla, precio_venta)
                    VALUES (%s, %s, %s, %s)
                """, (pid, prod['nombre'], talla, prod['precio']))
                
            conn.commit()
            
            # Mensaje de éxito
            bot.edit_message_text(
                f"✅ **¡VENTA REGISTRADA!**\n\n"
                f"👕 {prod['nombre']} ({talla})\n"
                f"💵 Recaudado: ${prod['precio']}\n"
                f"📉 Stock descontado.",
                call.message.chat.id, call.message.message_id,
                parse_mode="Markdown"
            )
            
            # Volver al menú después de unos segundos o mostrar botón
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("💰 Vender Otro", callback_data="start_sale"))
            markup.add(btn_atras("main_menu"))
            bot.send_message(call.message.chat.id, "¿Qué hacemos ahora?", reply_markup=markup)

        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Error procesando venta: {e}")
        finally:
            conn.close()

    # ==========================================
    # 📜 HISTORIAL DE VENTAS
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data == "ver_historial")
    def show_history(call):
        conn = get_connection()
        cur = conn.cursor()
        
        # Últimas 10 ventas
        cur.execute("""
            SELECT nombre_producto, talla, precio_venta, TO_CHAR(fecha, 'DD/MM HH24:MI') as fecha_fmt 
            FROM ventas 
            ORDER BY id DESC LIMIT 10
        """)
        ventas = cur.fetchall()
        
        # Total recaudado histórico
        cur.execute("SELECT SUM(precio_venta) as total FROM ventas")
        total_plata = cur.fetchone()['total'] or 0
        
        conn.close()
        
        if not ventas:
            txt = "📜 **Historial de Ventas**\n\nAún no hay ventas registradas."
        else:
            txt = f"📜 **Últimas 10 Ventas**\nTotal Histórico: **${total_plata:,.2f}**\n\n"
            for v in ventas:
                txt += f"• `{v['fecha_fmt']}`: **{v['nombre_producto']}** ({v['talla']}) - ${v['precio_venta']}\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(btn_atras("main_menu"))
        
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")