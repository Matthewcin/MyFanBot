from PIL import Image, ImageDraw, ImageFont
import io
import os

# ==========================================
# 1. CONFIGURACIÓN Y CONSTANTES
# ==========================================

# Rutas de archivos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf') 
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

# Configuración HD (300 DPI)
DPI = 300
SCALE = 300 / 144  # 2.0833...

# --- MEDIDAS DE LA TARJETA (Negra) ---
CARD_W = int(566.63 * SCALE)  # ~1180 px
CARD_H = int(323.79 * SCALE)  # ~674 px

# --- MEDIDAS DE LA HOJA A4 (Blanca) ---
A4_W = 2480
A4_H = 3508

# --- CÁLCULO DE COORDENADAS INTERNAS (RELATIVAS A LA TARJETA) ---
# Extraídas matemáticamente de tu código "resultado final" para que quede IGUAL.

# Margen rojo que usabas de referencia
MARGEN_PX = int(0.3 * 118.11)
# Padding extra que usabas en el draw.text
PADDING = int(5 * SCALE)
# Espaciado entre líneas de texto
LINE_SPACING = int(26 * SCALE)

# Posición X del Texto (Izquierda)
POS_TXT_X = MARGEN_PX + PADDING

# Posición Y del Texto 1 (Remitente) - Arriba
POS_TXT1_Y = MARGEN_PX + PADDING

# Posición Y del Texto 2 (Destinatario)
# En tu código global: T2_Y (900*S) - Card_Y (750*S - M) + Padding
# Diferencia base: 150 * SCALE
POS_TXT2_Y = int(150 * SCALE) + MARGEN_PX + PADDING

# Posición del Logo
# En tu código global: Logo_X (408*S) - Card_X (42*S - M)
# Diferencia base X: 366 * SCALE
POS_LOGO_X = int(366 * SCALE) + MARGEN_PX

# En tu código global: Logo_Y (834*S) - Card_Y (750*S - M)
# Diferencia base Y: 84 * SCALE
POS_LOGO_Y = int(84 * SCALE) + MARGEN_PX

# Tamaño del Logo (163x121 escalado)
LOGO_W = int(163 * SCALE)
LOGO_H = int(121 * SCALE)


# ==========================================
# 2. FUNCIÓN BASE: CREAR TARJETA INDIVIDUAL
# ==========================================
def crear_imagen_tarjeta(datos):
    """
    Crea y devuelve un objeto Image (PIL) con la tarjeta negra perfecta.
    No guarda en disco, solo memoria.
    """
    # 1. Lienzo Negro
    img = Image.new('RGB', (CARD_W, CARD_H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 2. Fuente
    try:
        font = ImageFont.truetype(FONT_PATH, int(20 * SCALE))
    except:
        font = ImageFont.load_default()

    # 3. Datos Remitente (Fijos - Yaneth Plazas)
    sender_lines = [
        "DESDE:",
        "BOGOTÁ - YANETH PLAZAS",
        "CC.1026600344 CEL: 3134553455",
        "CRA.29#3-24, VERAGUAS CP.111411",
        "YELLOWER.CO@GMAIL.COM"
    ]
    
    curr_y = POS_TXT1_Y
    for line in sender_lines:
        draw.text((POS_TXT_X, curr_y), line, font=font, fill="white")
        curr_y += LINE_SPACING

    # 4. Datos Destinatario (Dinámicos del Bot)
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

    curr_y = POS_TXT2_Y
    for line in recipient_lines:
        draw.text((POS_TXT_X, curr_y), line, font=font, fill="white")
        curr_y += LINE_SPACING

    # 5. Logo
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo = logo.resize((LOGO_W, LOGO_H), Image.Resampling.LANCZOS)
        img.paste(logo, (POS_LOGO_X, POS_LOGO_Y), logo)
    except:
        pass

    return img


# ==========================================
# 3. FUNCIONES PÚBLICAS (API)
# ==========================================

def generar_etiqueta_moto(datos, return_object=False):
    """
    Devuelve bytes de UNA sola tarjeta negra (sin hoja blanca).
    Ideal para ver en el celular o enviar por WhatsApp.
    """
    img = crear_imagen_tarjeta(datos)
    
    if return_object:
        return img

    bio = io.BytesIO()
    img.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio


def generar_hoja_a4(lista_pedidos):
    """
    Devuelve bytes de una HOJA A4 BLANCA con las tarjetas pegadas.
    Ideal para imprimir.
    """
    if not lista_pedidos:
        return None

    # 1. Crear Lienzo A4 BLANCO GIGANTE
    hoja = Image.new('RGB', (A4_W, A4_H), color=(255, 255, 255))
    draw = ImageDraw.Draw(hoja)

    # 2. Configuración de márgenes de impresión (Arriba a la Izquierda)
    # 50px es un margen seguro para impresoras caseras.
    START_X = 50
    START_Y = 50
    GAP = 20  # Espacio entre tarjetas
    COLS = 2  # Columnas por hoja

    # 3. Pegar tarjetas
    for i, datos in enumerate(lista_pedidos):
        if i >= 8: break # Máximo 8 por hoja
        
        # Generar tarjeta individual
        tarjeta = crear_imagen_tarjeta(datos)
        
        # Calcular posición en la grilla
        col = i % COLS
        row = i // COLS
        
        x = START_X + (col * (CARD_W + GAP))
        y = START_Y + (row * (CARD_H + GAP))
        
        # Pegar en la hoja blanca
        hoja.paste(tarjeta, (x, y))
        
        # Línea de corte (Gris clarito)
        draw.rectangle([x, y, x + CARD_W, y + CARD_H], outline=(200, 200, 200), width=1)

    # 4. Retornar hoja completa
    bio = io.BytesIO()
    hoja.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio