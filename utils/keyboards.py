from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def btn_atras(callback_data):
    return InlineKeyboardButton("🔙 Volver", callback_data=callback_data)

def menu_principal_kb():
    """Panel de Control UNIFICADO (Solo Admins)"""
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Fila 1: El núcleo del inventario
    markup.add(
        InlineKeyboardButton("📂 Catálogos", callback_data="admin_cats"),
        InlineKeyboardButton("👕 Productos / Stock", callback_data="admin_prods")
    )
    
    # Fila 2: Logística (Motomandado)
    markup.add(
        InlineKeyboardButton("🛵 Nuevo Envío", callback_data="nuevo_envio"),
        InlineKeyboardButton("🔎 Buscar Tracker", callback_data="track_pedido")
    )
    
    # Fila 3: Datos
    markup.add(
        InlineKeyboardButton("📊 Estadísticas Globales", callback_data="ver_stats")
    )
        
    return markup