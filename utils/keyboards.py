from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def btn_atras(callback_data):
    return InlineKeyboardButton("🔙 Volver", callback_data=callback_data)

def menu_principal_kb():
    markup = InlineKeyboardMarkup(row_width=1)
    
    markup.add(InlineKeyboardButton("💰 REGISTRAR VENTA", callback_data="start_sale"))
    
    markup.row(
        InlineKeyboardButton("🎫 Stock", callback_data="admin_cats"),
        InlineKeyboardButton("📜 Historial", callback_data="ver_historial")
    )
    
    markup.row(
        InlineKeyboardButton("🛵 Nuevo Envío", callback_data="nuevo_envio"),
        InlineKeyboardButton("🔎 Tracker", callback_data="track_pedido")
    )
    
    # --- BOTÓN NUEVO ---
    markup.add(InlineKeyboardButton("🖨 Imprimir Últimas 8 (A4)", callback_data="imprimir_lote"))
    
    markup.add(InlineKeyboardButton("📊 Estadísticas", callback_data="ver_stats"))
    
    return markup