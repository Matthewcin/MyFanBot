from database.db import get_connection
from utils.keyboards import btn_atras
from telebot import types

def register(bot):
    @bot.callback_query_handler(func=lambda call: call.data == "ver_stats")
    def stats(call):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM eventos")
        evs = cur.fetchone()['c']
        cur.execute("SELECT SUM(stock) as c FROM inventario")
        stk = cur.fetchone()['c'] or 0
        conn.close()
        
        markup = types.InlineKeyboardMarkup()
        markup.add(btn_atras("main_menu"))
        bot.edit_message_text(f"📊 **Stats Globales**\nEventos Activos: {evs}\nPrendas en Stock: {stk}", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")