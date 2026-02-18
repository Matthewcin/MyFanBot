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

# DIMENSIONES DE LA TARJETA (Individual)
CARD_W = int(566.63 * SCALE)
CARD_H = int(323.79 * SCALE)
MARGEN_PX = int(0.3 * 118.11)

# DIMENSIONES HOJA A4 (Para impresión de 8)
A4_W = 2480
A4_H = 3508

# --- CÁLCULO DE COORDENADAS RELATIVAS (DENTRO DE LA TARJETA) ---
# En tu calibración, la tarjeta empezaba en (T1_X - MARGEN).
# Por tanto, dentro de la tarjeta, el Texto 1 empieza exactamente en el Margen.

POS_TXT_X = MARGEN_PX
POS_T1_Y = MARGEN_PX

# Para el Texto 2 (Destinatario):
# En la hoja grande era Y=900. La tarjeta empezaba en Y=750-Margen.
# Diferencia: 900 - 750 = 150. Sumamos el margen.
POS_T2_Y = int(150 * SCALE) + MARGEN_PX

# Para el Logo:
# En la hoja grande era X=408, Y=834.
# Tarjeta empezaba en X=42-Margen, Y=750-Margen.
# Relativo X: 408 - 42 = 366. Sumamos margen.
# Relativo Y: 834 - 750 = 84. Sumamos margen.
POS_LOGO_X = int(366 * SCALE) + MARGEN_PX
POS_LOGO_Y = int(84 * SCALE) + MARGEN_PX
LOGO_W = int(163 * SCALE)
LOGO_H = int(121 * SCALE)


def generar_etiqueta_moto(datos, return_object=False):
    """
    Genera UNA sola tarjeta negra con los datos.
    """
    # 1. Crear lienzo negro (Solo la tarjeta)
    img = Image.new('RGB', (CARD_W, CARD_H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(FONT_PATH, int(20 * SCALE))
    except:
        font = ImageFont.load_default()

    line_spacing = int(26 * SCALE)

    # --- BLOQUE 1: REMITENTE ---
    sender_lines = [
        "DESDE:",
        "BOGOTÁ - YANETH PLAZAS",
        "CC.1026600344 CEL: 3134553455",
        "CRA.29#3-24, VERAGUAS CP.111411",
        "YELLOWER.CO@GMAIL.COM"
    ]

    curr_y = POS_T1_Y
    for line in sender_lines:
        draw.text((POS_TXT_X, curr_y), line, font=font, fill="white")
        curr_y += line_spacing

    # --- BLOQUE 2: DESTINATARIO ---
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

    curr_y = POS_T2_Y
    for line in recipient_lines:
        draw.text((POS_TXT_X, curr_y), line, font=font, fill="white")
        curr_y += line_spacing

    # --- LOGO ---
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo = logo.resize((LOGO_W, LOGO_H), Image.Resampling.LANCZOS)
        img.paste(logo, (POS_LOGO_X, POS_LOGO_Y), logo)
    except:
        pass

    # Si necesitamos la imagen en memoria para pegarla en la A4
    if return_object:
        return img

    # Si es para enviar sola (1 sola etiqueta)
    bio = io.BytesIO()
    img.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio

def generar_hoja_a4(lista_pedidos):
    """
    Genera una hoja A4 BLANCA y pega hasta 8 tarjetas negras.
    """
    if not lista_pedidos:
        return None

    # 1. Crear Hoja A4 BLANCA
    hoja = Image.new('RGB', (A4_W, A4_H), color=(255, 255, 255))
    draw = ImageDraw.Draw(hoja)
    
    # Configuración de márgenes para la grilla (Ajustado para centrar)
    MARGIN_X = 50
    MARGIN_Y = 150
    GAP_X = 20
    GAP_Y = 20
    cols = 2

    # 2. Generar y pegar cada tarjeta
    for i, datos in enumerate(lista_pedidos):
        if i >= 8: break # Máximo 8 por hoja
        
        # Generamos la tarjeta negra individual
        tarjeta = generar_etiqueta_moto(datos, return_object=True)
        
        # Calculamos posición
        col = i % cols
        row = i // cols
        
        x = MARGIN_X + (col * (CARD_W + GAP_X))
        y = MARGIN_Y + (row * (CARD_H + GAP_Y))
        
        # Pegamos la tarjeta negra sobre la hoja blanca
        hoja.paste(tarjeta, (x, y))
        
        # (Opcional) Línea de corte gris muy fina alrededor
        draw.rectangle([x, y, x + CARD_W, y + CARD_H], outline=(200, 200, 200), width=1)

    bio = io.BytesIO()
    hoja.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio