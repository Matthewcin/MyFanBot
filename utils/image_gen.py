from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf') 
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

# --- CONFIGURACIÓN HD (300 DPI) ---
DPI = 300
SCALE = 300 / 144  # Factor de escala para HD

# DIMENSIONES EXACTAS DE LA TARJETA
CARD_W = int(566.63 * SCALE)
CARD_H = int(323.79 * SCALE)
MARGEN_PX = int(0.3 * 118.11)

# OFFSET PARA COORDENADAS RELATIVAS
# (Para que el texto empiece donde terminaba el margen de la hoja anterior)
OFFSET_Y = 750 * SCALE - MARGEN_PX
OFFSET_X = 42 * SCALE - MARGEN_PX

def generar_etiqueta_moto(datos, return_object=False):
    """
    Genera la etiqueta en HD 300 DPI sin fondo de hoja, solo la tarjeta negra.
    """
    # Crear lienzo negro (La tarjeta)
    img = Image.new('RGB', (CARD_W, CARD_H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # --- CONFIGURACIÓN DE FUENTE ---
    try:
        # Tamaño equivalente al diseño calibrado
        font = ImageFont.truetype(FONT_PATH, int(20 * SCALE))
    except:
        font = ImageFont.load_default()

    line_spacing = int(26 * SCALE)

    # ==========================================
    # 1. BLOQUE 1: REMITENTE (FIJO)
    # ==========================================
    sender_lines = [
        "DESDE:",
        "BOGOTÁ - YANETH PLAZAS",
        "CC.1026600344 CEL: 3134553455",
        "CRA.29#3-24, VERAGUAS CP.111411",
        "YELLOWER.CO@GMAIL.COM"
    ]

    curr_x = (42 * SCALE) - OFFSET_X
    curr_y = (750 * SCALE) - OFFSET_Y

    for line in sender_lines:
        draw.text((curr_x, curr_y), line, font=font, fill="white")
        curr_y += line_spacing

    # ==========================================
    # 2. BLOQUE 2: DESTINATARIO (DINÁMICO)
    # ==========================================
    # Ajuste: T2_Y bajado a 900 según calibración
    t2_y_calibrado = (900 * SCALE) - OFFSET_Y
    
    nombre = datos.get('nombre', '').upper()
    destino = datos.get('destino', '').upper() # Ciudad - Departamento
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

    curr_y = t2_y_calibrado
    for line in recipient_lines:
        draw.text((curr_x, curr_y), line, font=font, fill="white")
        curr_y += line_spacing

    # ==========================================
    # 3. LOGO (PNG HD)
    # ==========================================
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        
        # Medida exacta calibrada: 86x64
        l_w, l_h = int(86 * SCALE), int(64 * SCALE)
        logo = logo.resize((l_w, l_h), Image.Resampling.LANCZOS)
        
        # Posición relativa
        lx = (408 * SCALE) - OFFSET_X
        ly = (834 * SCALE) - OFFSET_Y
        
        img.paste(logo, (int(lx), int(ly)), logo)
    except:
        pass

    # --- RETORNO ---
    if return_object:
        return img

    bio = io.BytesIO()
    # Importante: guardar con DPI 300 en los metadatos
    img.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio

# Ejemplo de uso para el bot:
# datos = {
#     'nombre': 'Juan Diego Castaño Zuluaga',
#     'destino': 'Marinilla-Antioquia',
#     'cc': '1001455663',
#     'telefono': '3143564195',
#     'direccion': 'Calle 30 # 44-20 | CP.054020',
#     'barrio': 'Las Acacias'
# }
# bio = generar_etiqueta_moto(datos)