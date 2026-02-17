import random, string
from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras
from utils.image_gen import generar_ticket_imagen

def register(bot):
    
    # --- MENÚ ENVÍOS ---
    @bot.callback_query_handler(func=lambda call: call.data == "nuevo_envio")
    def menu_envios(call):
        msg = bot.send_message(call.message.chat.id, "Escribe los datos del envío en este formato:\n\n`Cliente - Producto - Dirección`\n\nEj: Juan Perez - Hoodie Bad Bunny M - Calle Falsa 123", parse_mode="Markdown")
        bot.register_next_step_handler(msg, procesar_envio)

    def procesar_envio(message):
        try:
            datos = message.text.split('-')
            cliente = datos[0].strip()
            prod_info = datos[1].strip()
            direccion = datos[2].strip()
            
            # Generar Tracking ID (MFB-XXXX)
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            track_id = f"MFB-{suffix}"
            
            # Guardar en DB
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO envios (tracking_id, cliente_nombre, direccion, producto_info, estado)
                    VALUES (%s, %s, %s, %s, 'Pendiente')
                """, (track_id, cliente, direccion, prod_info))
            conn.commit()
            conn.close()
            
            # Generar Imagen
            img_bio = generar_ticket_imagen(track_id, cliente, prod_info, "Pendiente")
            
            bot.send_photo(message.chat.id, img_bio, caption=f"✅ **Envío Generado**\nTracking: `{track_id}`\nEstado: Pendiente de Moto", parse_mode="Markdown")
            
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error en formato. Asegurate de usar guiones separadores.\nError: {e}")

    # --- TRACKING (Cliente) ---
    @bot.callback_query_handler(func=lambda call: call.data == "track_pedido")
    def ask_tracking(call):
        msg = bot.send_message(call.message.chat.id, "🔍 Envía tu código de seguimiento (Ej: MFB-A1B2):")
        bot.register_next_step_handler(msg, buscar_tracking)

    def buscar_tracking(message):
        track_id = message.text.strip().upper()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM envios WHERE tracking_id = %s", (track_id,))
        envio = cur.fetchone()
        conn.close()
        
        if envio:
            txt = f"📦 **Estado del Pedido**\n\n🆔 ID: `{envio['tracking_id']}`\n👤 Cliente: {envio['cliente_nombre']}\n👕 Item: {envio['producto_info']}\n📍 Destino: {envio['direccion']}\n\n🚀 **ESTADO ACTUAL: {envio['estado']}**"
            bot.send_message(message.chat.id, txt, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ No encontré ese código de seguimiento.")