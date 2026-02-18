from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def btn_atras(callback_data):
    return InlineKeyboardButton("🔙 Volver", callback_data=callback_data)

def menu_principal_kb():
    markup = InlineKeyboardMarkup(row_width=1)
    
    # 1. Ventas
    markup.add(InlineKeyboardButton("💰 REGISTRAR VENTA", callback_data="start_sale"))
    
    # 2. Gestión
    markup.row(
        InlineKeyboardButton("🎫 Stock", callback_data="admin_cats"),
        InlineKeyboardButton("📜 Historial", callback_data="ver_historial")
    )
    
    # 3. Logística y Envíos
    markup.row(
        InlineKeyboardButton("🛵 Nuevo Envío", callback_data="nuevo_envio"),
        InlineKeyboardButton("🔎 Tracker", callback_data="track_pedido")
    )
    
    # --- CAMBIO AQUÍ: UN SOLO BOTÓN PARA IMPRIMIR ---
    markup.add(InlineKeyboardButton("🖨 CENTRO DE IMPRESIÓN", callback_data="menu_impresion"))
    
    # 4. Stats
    markup.add(InlineKeyboardButton("📊 Estadísticas", callback_data="ver_stats"))
    
    return markup