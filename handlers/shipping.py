# handlers/shipping.py
import random, string
from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras, menu_principal_kb
# Importamos el nuevo generador de imagen exacto
from utils.image_gen import generar_etiqueta_moto

# Memoria temporal para el Wizard de envío
# Format: { user_id: { 'ciudad': '', 'depto': '', ... } }
SHIPPING_SESSION = {}

def register(bot):
    
    # --- INICIO DEL WIZARD DE ENVÍO ---
    @bot.callback_query_handler(func=lambda call: call.data == "nuevo_envio")
    def start_shipping_wizard(call):
        uid = call.from_user.id
        # Inicializar sesión vacía
        SHIPPING_SESSION[uid] = {}
        
        # Paso 1: Ciudad y Departamento
        msg = bot.send_message(
            call.message.chat.id, 
            "🛵 **Nuevo Envío - Paso 1/4**\n\nIngresa Ciudad y Departamento separados por punto o guión.\n\nEj: `Medellín. Antioquia`", 
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, step_ciudad_depto)

    def step_ciudad_depto(message):
        uid = message.from_user.id
        text = message.text.replace('-', '.').strip() # Normalizar separador
        
        if '.' not in text:
            msg = bot.send_message(message.chat.id, "⚠️ Formato incorrecto. Usa un punto para separar.\nEj: `Bogotá. Cundinamarca`")
            bot.register_next_step_handler(msg, step_ciudad_depto)
            return
            
        parts = text.split('.', 1)
        SHIPPING_SESSION[uid]['ciudad'] = parts[0].strip()
        SHIPPING_SESSION[uid]['depto'] = parts[1].strip()
        
        # Paso 2: Nombre Completo
        msg = bot.send_message(message.chat.id, "👤 **Paso 2/4**\n\nIngresa el Nombre Completo del cliente:")
        bot.register_next_step_handler(msg, step_nombre)
        
    def step_nombre(message):
        uid = message.from_user.id
        SHIPPING_SESSION[uid]['nombre'] = message.text.strip()
        
        # Paso 3: CC y Teléfono
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
            msg = bot.send_message(message.chat.id, "⚠️ Formato incorrecto. Usa guión.\nEj: `12345 - 300123`")
            bot.register_next_step_handler(msg, step_cc_tel)
            return

        parts = text.split('-', 1)
        SHIPPING_SESSION[uid]['cc'] = parts[0].strip()
        SHIPPING_SESSION[uid]['telefono'] = parts[1].strip()
        
        # Paso 4: Dirección Exacta
        msg = bot.send_message(message.chat.id, "📍 **Paso 4/4**\n\nIngresa la Dirección exacta (Calle, número, apto):")
        bot.register_next_step_handler(msg, step_direccion_final)

    def step_direccion_final(message):
        uid = message.from_user.id
        chat_id = message.chat.id
        SHIPPING_SESSION[uid]['direccion'] = message.text.strip()
        
        # --- FIN DEL WIZARD: PROCESAR TODO ---
        bot.send_message(chat_id, "⏳ Generando etiqueta, espera un momento...")
        
        try:
            datos = SHIPPING_SESSION[uid]
            
            # 1. Generar Tracking ID Interno
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            track_id = f"MFB-{suffix}"
            
            # 2. Guardar en DB (Resumen simple en producto_info)
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO envios (tracking_id, cliente_nombre, direccion, producto_info, estado)
                    VALUES (%s, %s, %s, 'Envío Motomandado', 'En Preparación')
                """, (track_id, datos['nombre'], datos['direccion']))
            conn.commit()
            conn.close()
            
            # 3. GENERAR LA IMAGEN EXACTA
            # Pasamos el diccionario completo de datos
            img_bio = generar_etiqueta_moto(datos)
            
            # 4. Enviar resultado
            bot.send_photo(
                chat_id, 
                img_bio, 
                caption=f"✅ **Etiqueta Lista**\n\n🆔 Tracker: `{track_id}`\nReenvía esta imagen al repartidor.", 
                parse_mode="Markdown"
            )
            
            # Volver al menú
            bot.send_message(chat_id, "Panel Principal:", reply_markup=menu_principal_kb())
            
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error generando la etiqueta. Revisa que los archivos de fuente y logo existan en la carpeta utils/assets.\nError: {e}")
        finally:
            # Limpiar sesión
            SHIPPING_SESSION.pop(uid, None)


    # --- BUSCADOR INTERNO (Sin cambios respecto a la versión anterior) ---
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
                f"📍 Destino: {envio['direccion']}\n"
                f"🚀 Estado: **{envio['estado']}**"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Marcar Entregado", callback_data=f"set_entregado_{track_id}"))
            markup.add(btn_atras("main_menu"))
            bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ No existe ese envío en la base de datos.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("set_entregado_"))
    def marcar_entregado(call):
        track_id = call.data.split("_")[2]
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE envios SET estado = 'Entregado' WHERE tracking_id = %s", (track_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "✅ Marcado como entregado")
        bot.edit_message_text(f"✅ El envío `{track_id}` ha sido marcado como **Entregado**.", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=menu_principal_kb())