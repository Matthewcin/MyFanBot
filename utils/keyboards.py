from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def btn_atras(callback_data):
    return InlineKeyboardButton("🔙 Volver", callback_data=callback_data)

def menu_principal_kb():
    markup = InlineKeyboardMarkup(row_width=1)
    # Entrada Principal
    markup.add(InlineKeyboardButton("🎫 Gestionar Eventos", callback_data="admin_events"))
    
    # Logística
    markup.row(
        InlineKeyboardButton("🛵 Nuevo Envío", callback_data="nuevo_envio"),
        InlineKeyboardButton("🔎 Buscar Tracker", callback_data="track_pedido")
    )
    
    # Stats
    markup.add(InlineKeyboardButton("📊 Estadísticas", callback_data="ver_stats"))
    return markup