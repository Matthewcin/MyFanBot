from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- RUTAS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf') 
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

# --- CONFIGURACIÓN HD (300 DPI) ---
DPI = 300
SCALE = 300 / 144

# 1. DIMENSIONES EXACTAS DE LA TARJETA (Lienzo Final)
CARD_W = int(566.63 * SCALE)
CARD_H = int(323.79 * SCALE)
MARGEN_PX = int(0.3 * 118.11)

# 2. CALCULO DE COORDENADAS RELATIVAS
# Estas son las posiciones "absolutas" en la hoja A4 que tú definiste
ABS_T1_X = 42 * SCALE
ABS_T1_Y = 750 * SCALE
ABS_T2_Y = 900 * SCALE
ABS_L_X = 408 * SCALE
ABS_L_Y = 834 * SCALE

# Calculamos dónde empezaba la tarjeta en la hoja A4
START_X = ABS_T1_X - MARGEN_PX
START_Y = ABS_T1_Y - MARGEN_PX

# 3. TRANSFORMACIÓN: Coordenadas relativas a la tarjeta (0,0)
# Simplemente restamos el inicio de la tarjeta a las coordenadas absolutas
REL_T1_X = ABS_T1_X - START_X
REL_T1_Y = ABS_T1_Y - START_Y
REL_T2_Y = ABS_T2_Y - START_Y
REL_L_X = ABS_L_X - START_X
REL_L_Y = ABS_L_Y - START_Y

# Medidas del logo según tu código final (163x121 escalado)
L_W = int(163 * SCALE)
L_H = int(121 * SCALE)

def generar_etiqueta_moto(datos, return_object=False):
    """
    Genera únicamente la tarjeta negra HD (300 DPI)
    """
    img = Image.new('RGB', (CARD_W, CARD_H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(FONT_PATH, int(20 * SCALE))
    except:
        font = ImageFont.load_default()

    line_spacing = int(26 * SCALE)

    # ==========================================
    # BLOQUE 1: REMITENTE (YANETH PLAZAS)
    # ==========================================
    sender_lines = [
        "DESDE:",
        "BOGOTÁ - YANETH PLAZAS",
        "CC.1026600344 CEL: 3134553455",
        "CRA.29#3-24, VERAGUAS CP.111411",
        "YELLOWER.CO@GMAIL.COM"
    ]

    curr_x = REL_T1_X
    curr_y = REL_T1_Y

    for line in sender_lines:
        draw.text((curr_x, curr_y), line, font=font, fill="white")
        curr_y += line_spacing

    # ==========================================
    # BLOQUE 2: DESTINATARIO (DINÁMICO)
    # ==========================================
    # Extraer datos con valores por defecto por seguridad
    nombre = datos.get('nombre', '').upper()
    destino = datos.get('destino', '').upper()
    cc = datos.get('cc', '').upper()
    tel = datos.get('telefono', '').upper()
    direccion = datos.get('direccion', '').upper()
    barrio = datos.get('barrio', '').upper()

    recipient_lines = [
        f"ENVIAR A: {destino}",
        f"{nombre}",
        f"CC.{cc}  CEL: {tel}",
        f"{direccion}",
        f"BRR: {barrio}"
    ]

    curr_y = REL_T2_Y
    for line in recipient_lines:
        draw.text((curr_x, curr_y), line, font=font, fill="white")
        curr_y += line_spacing

    # ==========================================
    # LOGO (PNG HD)
    # ==========================================
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo = logo.resize((L_W, L_H), Image.Resampling.LANCZOS)
        img.paste(logo, (int(REL_L_X), int(REL_L_Y)), logo)
    except Exception as e:
        print(f"Error cargando logo: {e}")
        pass

    # --- RETORNO ---
    if return_object:
        return img

    bio = io.BytesIO()
    img.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio

# --- PARCHE DE COMPATIBILIDAD ---
# Evita que shipping.py se rompa por no encontrar esta función.
# Redirige la llamada para generar una sola etiqueta.
def generar_hoja_a4(lista_pedidos):
    if not lista_pedidos:
        return None
    return generar_etiqueta_moto(lista_pedidos[0])