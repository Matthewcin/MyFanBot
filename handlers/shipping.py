import random, string
from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras
from utils.image_gen import generar_ticket_imagen

def register(bot):
    
    # --- GENERAR ENVÍO (Para Motomandado) ---
    @bot.callback_query_handler(func=lambda call: call.data == "nuevo_envio")
    def menu_envios(call):
        msg = bot.send_message(
            call.message.chat.id, 
            "📝 **Nuevo Envío**\n\nIngresa los datos en una sola línea así:\n`Cliente - Prenda y Talla - Dirección`\n\nEj: *Mateo - Hoodie Bad Bunny L - Av. Siempre Viva 123*", 
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, procesar_envio)

    def procesar_envio(message):
        try:
            # Validación simple
            if "-" not in message.text:
                raise ValueError("Formato incorrecto")

            datos = message.text.split('-')
            # Limpiamos espacios extra
            cliente = datos[0].strip()
            prod_info = datos[1].strip()
            direccion = datos[2].strip() if len(datos) > 2 else "Retiro en Local"
            
            # Generar Tracking ID Interno
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            track_id = f"MFB-{suffix}"
            
            # Guardar en DB
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO envios (tracking_id, cliente_nombre, direccion, producto_info, estado)
                    VALUES (%s, %s, %s, %s, 'En Preparación')
                """, (track_id, cliente, direccion, prod_info))
            conn.commit()
            conn.close()
            
            # Generar Imagen (Etiqueta Virtual)
            img_bio = generar_ticket_imagen(track_id, cliente, prod_info, "En Preparación")
            
            bot.send_photo(
                message.chat.id, 
                img_bio, 
                caption=f"✅ **Etiqueta Generada**\nReenvía esto al repartidor.\n\n🆔 `{track_id}`\n📍 {direccion}", 
                parse_mode="Markdown"
            )
            # Volver al menú automáticamente o mostrar botón
            markup = types.InlineKeyboardMarkup()
            markup.add(btn_atras("main_menu"))
            bot.send_message(message.chat.id, "...", reply_markup=markup)
            
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: Usa el formato `Nombre - Producto - Dirección`. \nDetalle: {e}")

    # --- BUSCADOR INTERNO (Para ver si ya se entregó) ---
    @bot.callback_query_handler(func=lambda call: call.data == "track_pedido")
    def ask_tracking(call):
        msg = bot.send_message(call.message.chat.id, "🔎 Ingresa el ID del Tracker (Ej: MFB-X123):")
        bot.register_next_step_handler(msg, buscar_tracking_admin)

    def buscar_tracking_admin(message):
        track_id = message.text.strip().upper()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM envios WHERE tracking_id = %s", (track_id,))
        envio = cur.fetchone()
        conn.close()
        
        if envio:
            txt = (
                f"📦 **Detalle del Envío**\n"
                f"🆔 `{envio['tracking_id']}`\n"
                f"📅 Fecha: {envio['fecha']}\n"
                f"👤 Cliente: {envio['cliente_nombre']}\n"
                f"👕 Item: {envio['producto_info']}\n"
                f"📍 Destino: {envio['direccion']}\n"
                f"🚀 Estado: **{envio['estado']}**"
            )
            markup = types.InlineKeyboardMarkup()
            # Aquí podríamos agregar botón para cambiar estado "Marcar Entregado"
            markup.add(types.InlineKeyboardButton("✅ Marcar Entregado", callback_data=f"set_entregado_{track_id}"))
            markup.add(btn_atras("main_menu"))
            bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ No existe ese envío en la base de datos.")

    # --- CAMBIAR ESTADO A ENTREGADO ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("set_entregado_"))
    def marcar_entregado(call):
        track_id = call.data.split("_")[2]
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE envios SET estado = 'Entregado' WHERE tracking_id = %s", (track_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "✅ Marcado como entregado")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f"✅ El envío `{track_id}` ha sido cerrado.", parse_mode="Markdown")