import random, string
from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras, menu_principal_kb
# Importamos ambas funciones de imagen
from utils.image_gen import generar_etiqueta_moto, generar_hoja_a4

SHIPPING_SESSION = {}

def register(bot):
    
    # --- WIZARD DE ENVÍO ---
    @bot.callback_query_handler(func=lambda call: call.data == "nuevo_envio")
    def start_shipping_wizard(call):
        uid = call.from_user.id
        SHIPPING_SESSION[uid] = {}
        
        msg = bot.send_message(
            call.message.chat.id, 
            "🛵 **Nuevo Envío - Paso 1/4**\n\nIngresa Ciudad y Departamento separados por punto.\n\nEj: `Medellín. Antioquia`", 
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, step_ciudad_depto)

    def step_ciudad_depto(message):
        uid = message.from_user.id
        text = message.text.replace('-', '.').strip()
        
        if '.' not in text:
            msg = bot.send_message(message.chat.id, "⚠️ Usa un punto para separar.\nEj: `Bogotá. Cundinamarca`")
            bot.register_next_step_handler(msg, step_ciudad_depto)
            return
            
        parts = text.split('.', 1)
        SHIPPING_SESSION[uid]['ciudad'] = parts[0].strip()
        SHIPPING_SESSION[uid]['depto'] = parts[1].strip()
        
        msg = bot.send_message(message.chat.id, "👤 **Paso 2/4**\n\nIngresa el Nombre Completo:")
        bot.register_next_step_handler(msg, step_nombre)
        
    def step_nombre(message):
        uid = message.from_user.id
        SHIPPING_SESSION[uid]['nombre'] = message.text.strip()
        
        msg = bot.send_message(
            message.chat.id, 
            "🆔 **Paso 3/4**\n\nIngresa Cédula y Celular separados por guión.\n\nEj: `1015456789 - 3005550192`",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, step_cc_tel)

    def step_cc_tel(message):
        uid = message.from_user.id
        text = message.text.strip()
        
        if '-' not in text:
            msg = bot.send_message(message.chat.id, "⚠️ Usa guión.\nEj: `12345 - 300123`")
            bot.register_next_step_handler(msg, step_cc_tel)
            return

        parts = text.split('-', 1)
        SHIPPING_SESSION[uid]['cc'] = parts[0].strip()
        SHIPPING_SESSION[uid]['telefono'] = parts[1].strip()
        
        msg = bot.send_message(message.chat.id, "📍 **Paso 4/4**\n\nIngresa la Dirección exacta:")
        bot.register_next_step_handler(msg, step_direccion_final)

    def step_direccion_final(message):
        uid = message.from_user.id
        chat_id = message.chat.id
        SHIPPING_SESSION[uid]['direccion'] = message.text.strip()
        
        bot.send_message(chat_id, "⏳ Generando etiqueta...")
        
        try:
            datos = SHIPPING_SESSION[uid]
            
            # Tracking ID
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            track_id = f"MFB-{suffix}"
            
            # GUARDAR TODOS LOS CAMPOS EN DB
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO envios (tracking_id, cliente_nombre, ciudad, depto, cc, telefono, direccion, producto_info, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Motomandado', 'En Preparación')
                """, (track_id, datos['nombre'], datos['ciudad'], datos['depto'], datos['cc'], datos['telefono'], datos['direccion']))
            conn.commit()
            conn.close()
            
            # Generar Imagen Individual
            img_bio = generar_etiqueta_moto(datos)
            
            bot.send_photo(
                chat_id, 
                img_bio, 
                caption=f"✅ **Etiqueta Lista**\n🆔 `{track_id}`\n\n(Puedes imprimir el lote A4 desde el menú)", 
                parse_mode="Markdown"
            )
            
            bot.send_message(chat_id, "Panel:", reply_markup=menu_principal_kb())
            
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error: {e}")
        finally:
            SHIPPING_SESSION.pop(uid, None)


    # --- IMPRIMIR LOTE A4 (ÚLTIMAS 8) ---
    @bot.callback_query_handler(func=lambda call: call.data == "imprimir_lote")
    def imprimir_lote_a4(call):
        msg_wait = bot.send_message(call.message.chat.id, "🖨 Preparando hoja A4 (300 DPI)...")
        
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Traer todos los campos necesarios
                cur.execute("""
                    SELECT cliente_nombre, ciudad, depto, cc, telefono, direccion 
                    FROM envios 
                    ORDER BY fecha DESC 
                    LIMIT 8
                """)
                envios = cur.fetchall()
            
            conn.close()

            if not envios:
                bot.edit_message_text("❌ No hay envíos registrados.", call.message.chat.id, msg_wait.message_id)
                return

            # Mapear DB -> Diccionario para ImageGen
            lista_datos = []
            for e in envios:
                d = {
                    'nombre': e['cliente_nombre'],
                    'ciudad': e['ciudad'] or "CIUDAD",
                    'depto': e['depto'] or "DEPTO",
                    'cc': e['cc'] or "123",
                    'telefono': e['telefono'] or "000",
                    'direccion': e['direccion']
                }
                lista_datos.append(d)

            # Generar A4
            img_a4 = generar_hoja_a4(lista_datos)
            
            bot.delete_message(call.message.chat.id, msg_wait.message_id)
            bot.send_document(
                call.message.chat.id, 
                img_a4, 
                visible_file_name="etiquetas_A4.png",
                caption=f"✅ **Hoja A4 Generada**\nContiene {len(lista_datos)} etiquetas.\n\nLista para imprimir."
            )

        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Error A4: {e}")

    # --- TRACKER SIMPLE ---
    @bot.callback_query_handler(func=lambda call: call.data == "track_pedido")
    def ask_tracking(call):
        msg = bot.send_message(call.message.chat.id, "🔎 Ingresa ID (MFB-XXXX):")
        bot.register_next_step_handler(msg, buscar_tracking_admin)

    def buscar_tracking_admin(message):
        tid = message.text.strip().upper()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM envios WHERE tracking_id = %s", (tid,))
        res = cur.fetchone()
        conn.close()
        
        if res:
            txt = f"📦 **{tid}**\n👤 {res['cliente_nombre']}\n📍 {res['ciudad']}, {res['direccion']}\n🚀 {res['estado']}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Entregado", callback_data=f"set_entregado_{tid}"))
            markup.add(btn_atras("main_menu"))
            bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ No existe.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("set_entregado_"))
    def marcar_entregado(call):
        tid = call.data.split("_")[2]
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE envios SET estado = 'Entregado' WHERE tracking_id = %s", (tid,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Actualizado")
        bot.delete_message(call.message.chat.id, call.message.message_id)