from database.db import get_connection
from utils.keyboards import btn_atras
from telebot import types

def register(bot):
    
    @bot.callback_query_handler(func=lambda call: call.data == "ver_stats")
    def show_stats(call):
        conn = get_connection()
        cur = conn.cursor()
        
        # Consultas
        cur.execute("SELECT COUNT(*) as total FROM usuarios")
        total_users = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM envios")
        total_envios = cur.fetchone()['total']
        
        cur.execute("SELECT SUM(stock) as total FROM inventario")
        total_items = cur.fetchone()['total'] or 0
        
        conn.close()
        
        txt = (
            f"📊 **Estadísticas MyFanBox**\n\n"
            f"👥 Usuarios en Bot: {total_users}\n"
            f"🚚 Envíos Totales: {total_envios}\n"
            f"👕 Prendas en Stock: {total_items}"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(btn_atras("main_menu"))
        
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")                