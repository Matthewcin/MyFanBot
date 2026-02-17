import random, string
from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras
from utils.image_gen import generar_ticket_imagen

def register(bot):
    
    @bot.callback_query_handler(func=lambda call: call.data == "nuevo_envio")
    def new_ship(call):
        msg = bot.send_message(call.message.chat.id, "Escribe: `Cliente - Prenda - Dirección`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_ship)

    def process_ship(message):
        try:
            p = message.text.split('-')
            cli = p[0].strip()
            item = p[1].strip()
            addr = p[2].strip()
            
            tid = "MFB-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("INSERT INTO envios (tracking_id, cliente_nombre, direccion, producto_info) VALUES (%s, %s, %s, %s)", (tid, cli, addr, item))
            conn.commit()
            conn.close()
            
            img = generar_ticket_imagen(tid, cli, item, "Pendiente")
            bot.send_photo(message.chat.id, img, caption=f"✅ Ticket: `{tid}`", parse_mode="Markdown")
            
        except:
            bot.send_message(message.chat.id, "❌ Error formato.")

    @bot.callback_query_handler(func=lambda call: call.data == "track_pedido")
    def track(call):
        msg = bot.send_message(call.message.chat.id, "ID de Tracking:")
        bot.register_next_step_handler(msg, show_track)

    def show_track(message):
        tid = message.text.strip().upper()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM envios WHERE tracking_id = %s", (tid,))
        res = cur.fetchone()
        conn.close()
        
        if res:
            bot.send_message(message.chat.id, f"📦 Estado: {res['estado']}\nCliente: {res['cliente_nombre']}")
        else:
            bot.send_message(message.chat.id, "❌ No encontrado.")