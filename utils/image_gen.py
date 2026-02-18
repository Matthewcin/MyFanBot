from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- RUTAS ---
# Ajustamos base_dir para que suba un nivel desde 'utils' y encuentre 'assets'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf') 
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

# --- CONFIGURACIÓN HD (300 DPI) ---
DPI = 300
SCALE = 300 / 144

# --- DIMENSIONES DEL LIENZO FINAL (SOLO LA TARJETA) ---
CARD_W = int(566.63 * SCALE)
CARD_H = int(323.79 * SCALE)
MARGEN_PX = int(0.3 * 118.11)

# --- CÁLCULO DE COORDENADAS RELATIVAS ---
# Basado en tu código de calibración final.
# El punto (0,0) de la nueva imagen equivale al inicio de la tarjeta negra en la hoja A4.

# Un pequeño padding extra que usabas en tu código (5 * SCALE)
PADDING_EXTRA = int(5 * SCALE)

# Posición X inicial para textos (Margen rojo + padding extra)
FINAL_TXT_X = MARGEN_PX + PADDING_EXTRA

# Posición Y inicial para Bloque 1 (Margen rojo + padding extra)
FINAL_T1_Y = MARGEN_PX + PADDING_EXTRA

# Posición Y inicial para Bloque 2
# Cálculo: (T2_Y original + padding) - (Inicio tarjeta Y)
# (900*S + 5*S) - (750*S - MARGEN) = 155*S + MARGEN
FINAL_T2_Y = int(155 * SCALE) + MARGEN_PX

# Posición del Logo
# Cálculo X: L_X original - Inicio tarjeta X = 408*S - (42*S - MARGEN) = 366*S + MARGEN
FINAL_LOGO_X = int(366 * SCALE) + MARGEN_PX
# Cálculo Y: L_Y original - Inicio tarjeta Y = 834*S - (750*S - MARGEN) = 84*S + MARGEN
FINAL_LOGO_Y = int(84 * SCALE) + MARGEN_PX

# Dimensiones del logo (tomadas de tu código final: 163x121)
FINAL_LOGO_W = int(163 * SCALE)
FINAL_LOGO_H = int(121 * SCALE)


def generar_etiqueta_moto(datos, return_object=False):
    """
    Genera únicamente la tarjeta negra HD (300 DPI).
    """
    # Crear lienzo negro (Solo el tamaño de la tarjeta)
    img = Image.new('RGB', (CARD_W, CARD_H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(FONT_PATH, int(20 * SCALE))
    except:
        font = ImageFont.load_default()

    line_spacing = int(26 * SCALE)

    # ==========================================
    # BLOQUE 1: REMITENTE (YANETH PLAZAS - FIJO)
    # ==========================================
    sender_lines = [
        "DESDE:",
        "BOGOTÁ - YANETH PLAZAS",
        "CC.1026600344 CEL: 3134553455",
        "CRA.29#3-24, VERAGUAS CP.111411",
        "YELLOWER.CO@GMAIL.COM"
    ]

    curr_x = FINAL_TXT_X
    curr_y = FINAL_T1_Y

    for line in sender_lines:
        draw.text((curr_x, curr_y), line, font=font, fill="white")
        curr_y += line_spacing

    # ==========================================
    # BLOQUE 2: DESTINATARIO (DINÁMICO)
    # ==========================================
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

    curr_y = FINAL_T2_Y
    for line in recipient_lines:
        draw.text((curr_x, curr_y), line, font=font, fill="white")
        curr_y += line_spacing

    # ==========================================
    # LOGO (PNG HD)
    # ==========================================
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo = logo.resize((FINAL_LOGO_W, FINAL_LOGO_H), Image.Resampling.LANCZOS)
        img.paste(logo, (FINAL_LOGO_X, FINAL_LOGO_Y), logo)
    except Exception as e:
        print(f"Error cargando logo: {e}")
        pass

    # --- RETORNO ---
    if return_object:
        return img

    bio = io.BytesIO()
    # Guardar con 300 DPI en metadatos
    img.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio

# --- PARCHE DE COMPATIBILIDAD ---
# Mantenemos esto para que shipping.py no falle al importar.
def generar_hoja_a4(lista_pedidos):
    if not lista_pedidos:
        return None
    return generar_etiqueta_moto(lista_pedidos[0])