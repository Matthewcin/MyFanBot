import random
import string
from telebot import types
from database.db import get_connection
from utils.keyboards import btn_atras, menu_principal_kb
from utils.image_gen import generar_etiqueta_moto, generar_hoja_a4

# --- MEMORIAS TEMPORALES ---
SHIPPING_SESSION = {}  # Para el paso a paso de crear envío
PRINT_SELECTION = {}   # Para la selección manual de impresión {uid: [id1, id2]}

def register(bot):
    
    # =========================================================
    # 🛵 WIZARD: NUEVO ENVÍO (PASO A PASO)
    # =========================================================
    
    @bot.callback_query_handler(func=lambda call: call.data == "nuevo_envio")
    def start_shipping_wizard(call):
        uid = call.from_user.id
        SHIPPING_SESSION[uid] = {}
        
        # Paso 1: Ciudad y Depto
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
            msg = bot.send_message(message.chat.id, "⚠️ Formato incorrecto. Usa un punto para separar.\nEj: `Bogotá. Cundinamarca`")
            bot.register_next_step_handler(msg, step_ciudad_depto)
            return
            
        parts = text.split('.', 1)
        SHIPPING_SESSION[uid]['ciudad'] = parts[0].strip()
        SHIPPING_SESSION[uid]['depto'] = parts[1].strip()
        
        # Paso 2: Nombre
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
        
        # Paso 4: Dirección
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
            
            # 2. Guardar en DB
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO envios (tracking_id, cliente_nombre, ciudad, depto, cc, telefono, direccion, producto_info, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Motomandado', 'En Preparación')
                """, (track_id, datos['nombre'], datos['ciudad'], datos['depto'], datos['cc'], datos['telefono'], datos['direccion']))
            conn.commit()
            conn.close()
            
            # 3. GENERAR IMAGEN INDIVIDUAL
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
            bot.send_message(chat_id, f"❌ Error generando etiqueta: {e}")
        finally:
            # Limpiar sesión
            SHIPPING_SESSION.pop(uid, None)


    # =========================================================
    # 🖨 SUB-MENÚ: CENTRO DE IMPRESIÓN
    # =========================================================

    @bot.callback_query_handler(func=lambda call: call.data == "menu_impresion")
    def show_print_menu(call):
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # Opción 1: Imprimir uno solo (Buscar por ID)
        markup.add(types.InlineKeyboardButton("☝️ Imprimir Uno Solo (Buscar ID)", callback_data="print_single_ask"))
        
        # Opción 2: Imprimir Últimos 8 (Hoja A4 automática)
        markup.add(types.InlineKeyboardButton("📄 Imprimir Últimos 8 (A4)", callback_data="imprimir_lote"))
        
        # Opción 3: Seleccionar manual (Checkboxes)
        markup.add(types.InlineKeyboardButton("✅ Seleccionar Impresión", callback_data="menu_print_select"))
        
        markup.add(btn_atras("main_menu"))
        
        bot.edit_message_text(
            "🖨 **Centro de Impresión**\nSelecciona una opción:",
            call.message.chat.id, call.message.message_id,
            reply_markup=markup, parse_mode="Markdown"
        )

    # --- OPCIÓN 1: IMPRIMIR UNO SOLO ---
    @bot.callback_query_handler(func=lambda call: call.data == "print_single_ask")
    def ask_single_id(call):
        msg = bot.send_message(call.message.chat.id, "🖨 Envía el **ID del Tracker** que quieres reimprimir (Ej: MFB-X123):")
        bot.register_next_step_handler(msg, process_single_print)

    def process_single_print(message):
        tid = message.text.strip().upper()
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM envios WHERE tracking_id = %s", (tid,))
                e = cur.fetchone()
            
            if not e:
                bot.send_message(message.chat.id, "❌ Ese ID no existe.", reply_markup=menu_principal_kb())
                return

            # Preparar datos para imagen
            datos = {
                'nombre': e['cliente_nombre'],
                'ciudad': e['ciudad'] or "",
                'depto': e['depto'] or "",
                'cc': e['cc'] or "",
                'telefono': e['telefono'] or "",
                'direccion': e['direccion']
            }
            
            # Generar imagen individual
            img_bio = generar_etiqueta_moto(datos)
            
            bot.send_photo(
                message.chat.id, 
                img_bio, 
                caption=f"✅ **Copia Generada**\n🆔 `{tid}`", 
                parse_mode="Markdown"
            )
            
            # Volver al menú de impresión
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Volver a Impresión", callback_data="menu_impresion"))
            bot.send_message(message.chat.id, "Opciones:", reply_markup=markup)

        except Exception as err:
            bot.send_message(message.chat.id, f"❌ Error: {err}")
        finally:
            conn.close()


    # --- OPCIÓN 2: IMPRIMIR ÚLTIMOS 8 (A4 AUTOMÁTICO) ---
    @bot.callback_query_handler(func=lambda call: call.data == "imprimir_lote")
    def imprimir_lote_a4(call):
        msg_wait = bot.send_message(call.message.chat.id, "🖨 Generando A4 con los últimos 8...")
        
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT cliente_nombre, ciudad, depto, cc, telefono, direccion 
                    FROM envios 
                    ORDER BY fecha DESC 
                    LIMIT 8
                """)
                envios = cur.fetchall()
            
            if not envios:
                bot.edit_message_text("❌ No hay datos.", call.message.chat.id, msg_wait.message_id)
                return

            # Mapear datos
            lista_datos = []
            for e in envios:
                lista_datos.append({
                    'nombre': e['cliente_nombre'],
                    'ciudad': e['ciudad'] or "",
                    'depto': e['depto'] or "",
                    'cc': e['cc'] or "",
                    'telefono': e['telefono'] or "",
                    'direccion': e['direccion']
                })

            img_a4 = generar_hoja_a4(lista_datos)
            
            bot.delete_message(call.message.chat.id, msg_wait.message_id)
            bot.send_document(
                call.message.chat.id, 
                img_a4, 
                visible_file_name="ultimos_8.png",
                caption=f"✅ **Hoja A4 (Últimos 8)**"
            )
            
            bot.send_message(call.message.chat.id, "Panel:", reply_markup=menu_principal_kb())

        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Error: {e}")
        finally:
            conn.close()


    # --- OPCIÓN 3: SELECCIONAR IMPRESIÓN (CHECKBOXES) ---
    @bot.callback_query_handler(func=lambda call: call.data == "menu_print_select")
    def menu_seleccion_impresion(call):
        uid = call.from_user.id
        if uid not in PRINT_SELECTION: PRINT_SELECTION[uid] = []
        selected_ids = PRINT_SELECTION[uid]
        
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Mostramos los últimos 16 para elegir
                cur.execute("SELECT tracking_id, cliente_nombre FROM envios ORDER BY fecha DESC LIMIT 16")
                envios = cur.fetchall()
            
            if not envios:
                bot.answer_callback_query(call.id, "No hay envíos.")
                return

            markup = types.InlineKeyboardMarkup(row_width=1)
            for e in envios:
                tid = e['tracking_id']
                icon = "✅" if tid in selected_ids else "⬜"
                markup.add(types.InlineKeyboardButton(f"{icon} {e['cliente_nombre']}", callback_data=f"toggle_p_{tid}"))

            count = len(selected_ids)
            if count > 0:
                markup.add(types.InlineKeyboardButton(f"🖨 IMPRIMIR ESTOS ({count}/8)", callback_data="do_print_selection"))
            else:
                markup.add(types.InlineKeyboardButton("👆 Selecciona tarjetas", callback_data="ignore"))
                
            markup.add(btn_atras("menu_impresion"))
            
            bot.edit_message_text("✅ **Selección Manual**\nMarca hasta 8 para la hoja A4:", 
                                  call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
            
        except Exception as e:
            bot.send_message(call.message.chat.id, f"Error: {e}")
        finally:
            conn.close()

    @bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_p_"))
    def toggle_selection(call):
        uid = call.from_user.id
        tid = call.data.split("_")[2]
        if uid not in PRINT_SELECTION: PRINT_SELECTION[uid] = []
        
        if tid in PRINT_SELECTION[uid]:
            PRINT_SELECTION[uid].remove(tid)
        else:
            if len(PRINT_SELECTION[uid]) >= 8:
                bot.answer_callback_query(call.id, "⚠️ Máximo 8 por hoja.", show_alert=True)
                return
            PRINT_SELECTION[uid].append(tid)
            
        menu_seleccion_impresion(call)

    @bot.callback_query_handler(func=lambda call: call.data == "do_print_selection")
    def execute_print_selection(call):
        uid = call.from_user.id
        ids = PRINT_SELECTION.get(uid, [])
        if not ids: return
        
        msg = bot.send_message(call.message.chat.id, "🖨 Generando hoja personalizada...")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                fmt = ','.join(['%s']*len(ids))
                query = f"SELECT cliente_nombre, ciudad, depto, cc, telefono, direccion FROM envios WHERE tracking_id IN ({fmt})"
                cur.execute(query, tuple(ids))
                data_db = cur.fetchall()
            
            lista = []
            for e in data_db:
                lista.append({
                    'nombre': e['cliente_nombre'],
                    'ciudad': e['ciudad'] or "",
                    'depto': e['depto'] or "",
                    'cc': e['cc'] or "",
                    'telefono': e['telefono'] or "",
                    'direccion': e['direccion']
                })
                
            img_a4 = generar_hoja_a4(lista)
            bot.delete_message(call.message.chat.id, msg.message_id)
            bot.send_document(call.message.chat.id, img_a4, visible_file_name="seleccion_A4.png", caption="✅ **Hoja Personalizada Lista**")
            
            PRINT_SELECTION[uid] = [] # Limpiar
            bot.send_message(call.message.chat.id, "Panel:", reply_markup=menu_principal_kb())

        except Exception as e:
            bot.send_message(call.message.chat.id, f"Error: {e}")
        finally:
            conn.close()

    @bot.callback_query_handler(func=lambda call: call.data == "ignore")
    def ignore(call):
        bot.answer_callback_query(call.id, "Selecciona una tarjeta de la lista.")

    # =========================================================
    # 🔎 RASTREADOR Y ENTREGAS
    # =========================================================
    
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
            txt = (
                f"📦 **Detalle del Envío**\n"
                f"🆔 `{res['tracking_id']}`\n"
                f"📅 Fecha: {res['fecha']}\n"
                f"👤 Cliente: {res['cliente_nombre']}\n"
                f"📍 Destino: {res['ciudad']}, {res['direccion']}\n"
                f"🚀 Estado: **{res['estado']}**"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Marcar Entregado", callback_data=f"set_entregado_{tid}"))
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
        
        bot.answer_callback_query(call.id, "✅ Actualizado")
        bot.edit_message_text(
            f"✅ El envío `{tid}` ha sido marcado como **Entregado**.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=menu_principal_kb()
        )