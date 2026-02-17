from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def btn_atras(callback_data):
    """Crea un botón de 'Volver' estándar."""
    return InlineKeyboardButton("🔙 Volver", callback_data=callback_data)

def menu_principal_kb(es_admin=False):
    markup = InlineKeyboardMarkup(row_width=2)
    # Botones para clientes
    markup.add(InlineKeyboardButton("🛍 Ver Catálogo", callback_data="ver_catalogo_cliente"))
    markup.add(InlineKeyboardButton("🚚 Rastrear Pedido", callback_data="track_pedido"))
    
    if es_admin:
        # Botones exclusivos admin
        markup.add(InlineKeyboardButton("🔧 Admin Catálogos", callback_data="admin_cats"),
                   InlineKeyboardButton("📦 Admin Productos", callback_data="admin_prods"))
        markup.add(InlineKeyboardButton("🛵 Generar Envío", callback_data="nuevo_envio"),
                   InlineKeyboardButton("📊 Estadísticas", callback_data="ver_stats"))
        
    return markup