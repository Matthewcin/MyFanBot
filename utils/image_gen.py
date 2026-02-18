from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- RUTAS ---
# Ajuste para que encuentre la carpeta assets subiendo un nivel desde utils
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf') 
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

# --- CONFIGURACIÓN HD (300 DPI) ---
DPI = 300
SCALE = 300 / 144

# DIMENSIONES EXACTAS DE LA TARJETA (Solo la tarjeta negra)
CARD_W = int(566.63 * SCALE)
CARD_H = int(323.79 * SCALE)
MARGEN_PX = int(0.3 * 118.11)

# OFFSET PARA COORDENADAS RELATIVAS
# Esto ajusta las coordenadas originales de la hoja grande para que encajen en la tarjeta pequeña
OFFSET_Y = 750 * SCALE - MARGEN_PX
OFFSET_X = 42 * SCALE - MARGEN_PX

def generar_etiqueta_moto(datos, return_object=False):
    """
    Genera la tarjeta negra HD con los datos de envío.
    """
    # Crear lienzo negro (Solo la tarjeta)
    img = Image.new('RGB', (CARD_W, CARD_H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # --- CONFIGURACIÓN DE FUENTE ---
    try:
        font = ImageFont.truetype(FONT_PATH, int(20 * SCALE))
    except:
        font = ImageFont.load_default()

    line_spacing = int(26 * SCALE)

    # ==========================================
    # 1. BLOQUE REMITENTE (YANETH PLAZAS - FIJO)
    # ==========================================
    sender_lines = [
        "DESDE:",
        "BOGOTÁ - YANETH PLAZAS",
        "CC.1026600344 CEL: 3134553455",
        "CRA.29#3-24, VERAGUAS CP.111411",
        "YELLOWER.CO@GMAIL.COM"
    ]

    # Coordenadas ajustadas al nuevo lienzo
    curr_x = (42 * SCALE) - OFFSET_X
    curr_y = (750 * SCALE) - OFFSET_Y

    for line in sender_lines:
        draw.text((curr_x, curr_y), line, font=font, fill="white")
        curr_y += line_spacing

    # ==========================================
    # 2. BLOQUE DESTINATARIO (DINÁMICO)
    # ==========================================
    # Datos dinámicos que llegan del bot
    nombre = datos.get('nombre', '').upper()
    destino = datos.get('destino', '').upper() # Debe incluir Ciudad y Depto
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

    # Coordenada Y bajada a 900 según calibración
    t2_y_calibrado = (900 * SCALE) - OFFSET_Y
    curr_y = t2_y_calibrado
    
    for line in recipient_lines:
        draw.text((curr_x, curr_y), line, font=font, fill="white")
        curr_y += line_spacing

    # ==========================================
    # 3. LOGO (PNG HD)
    # ==========================================
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        
        # Medida calibrada: 86x64 escalada a HD
        l_w, l_h = int(86 * SCALE), int(64 * SCALE)
        logo = logo.resize((l_w, l_h), Image.Resampling.LANCZOS)
        
        # Posición ajustada
        lx = (408 * SCALE) - OFFSET_X
        ly = (834 * SCALE) - OFFSET_Y
        
        img.paste(logo, (int(lx), int(ly)), logo)
    except Exception as e:
        print(f"Error cargando logo: {e}")
        pass

    # --- RETORNO ---
    if return_object:
        return img

    bio = io.BytesIO()
    # Guardamos con 300 DPI en los metadatos
    img.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio

# --- PARCHE DE COMPATIBILIDAD ---
# Esta función existe solo para que no falle la importación en shipping.py
# Si la llaman, devolverá una sola etiqueta en lugar de una hoja A4.
def generar_hoja_a4(lista_pedidos):
    if not lista_pedidos:
        return None
    # Devuelve solo la primera etiqueta de la lista
    return generar_etiqueta_moto(lista_pedidos[0])