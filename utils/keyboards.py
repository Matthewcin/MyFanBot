from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def btn_atras(callback_data):
    return InlineKeyboardButton("🔙 Volver", callback_data=callback_data)

def menu_principal_kb():
    markup = InlineKeyboardMarkup(row_width=1)
    
    # ACCIÓN PRINCIPAL: VENDER
    markup.add(InlineKeyboardButton("💰 REGISTRAR VENTA", callback_data="start_sale"))
    
    # Gestión
    markup.row(
        InlineKeyboardButton("🎫 Eventos/Stock", callback_data="admin_events"),
        InlineKeyboardButton("📜 Historial Ventas", callback_data="ver_historial")
    )
    
    # Logística
    markup.row(
        InlineKeyboardButton("🛵 Nuevo Envío", callback_data="nuevo_envio"),
        InlineKeyboardButton("🔎 Tracker", callback_data="track_pedido")
    )
    
    # Stats
    markup.add(InlineKeyboardButton("📊 Estadísticas", callback_data="ver_stats"))
    
    return markup