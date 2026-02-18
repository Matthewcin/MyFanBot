from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf') 
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

# --- CONFIGURACIÓN DE TAMAÑOS (300 DPI) ---
CARD_W, CARD_H = 1181, 673  # 10cm x 5.7cm
A4_W, A4_H = 2480, 3508     # A4 Vertical

def generar_etiqueta_moto(datos, return_object=False):
    """
    Genera la etiqueta individual.
    Si return_object=True, devuelve la imagen PIL (para pegar en A4).
    Si return_object=False, devuelve bytes (para enviar por Telegram).
    """
    img = Image.new('RGB', (CARD_W, CARD_H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    WHITE = (255, 255, 255)
    
    # Ajuste visual para que coincida con tu referencia
    FONT_SIZE = 36 
    LINE_HEIGHT = 50

    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except:
        font = ImageFont.load_default()

    # --- LOGO ---
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        target_h = int(CARD_H * 0.65) 
        aspect_ratio = logo.width / logo.height
        target_w = int(target_h * aspect_ratio)
        logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
        logo_x = CARD_W - target_w - 50 
        logo_y = (CARD_H - target_h) // 2
        img.paste(logo, (logo_x, logo_y), logo)
    except:
        pass

    # --- TEXTO ---
    MARGIN_LEFT = 50
    CURRENT_Y = 50

    sender_lines = [
        "DESDE:",
        "BOGOTÁ – YANETH PLAZAS",
        "CC.1026600344 CEL: 3134553455",
        "CRA.29#3-24, VERAGUAS CP.111411",
        "YELLOWER.CO@GMAIL.COM"
    ]

    for line in sender_lines:
        draw.text((MARGIN_LEFT, CURRENT_Y), line, font=font, fill=WHITE)
        CURRENT_Y += LINE_HEIGHT

    CURRENT_Y += LINE_HEIGHT * 0.8 

    # Datos dinámicos
    ciudad = datos.get('ciudad', '').upper()
    depto = datos.get('depto', '').upper()
    nombre = datos.get('nombre', '').upper()
    cc = datos.get('cc', '').upper()
    tel = datos.get('telefono', '').upper()
    dir_envio = datos.get('direccion', '').upper()

    recipient_lines = [
        f"ENVIAR A: {ciudad}. {depto}",
        f"{nombre}",
        f"CC.{cc}   CEL: {tel}",
        f"{dir_envio}"
    ]

    for line in recipient_lines:
        draw.text((MARGIN_LEFT, CURRENT_Y), line, font=font, fill=WHITE)
        CURRENT_Y += LINE_HEIGHT

    if return_object:
        return img

    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio

def generar_hoja_a4(lista_pedidos):
    """
    Recibe una lista de diccionarios (máx 8).
    Genera una hoja A4 lista para imprimir.
    """
    # Hoja blanca
    hoja = Image.new('RGB', (A4_W, A4_H), color=(255, 255, 255))
    
    # Márgenes calculados para centrar 2 columnas
    # Ancho contenido: 1181 * 2 = 2362. A4 Ancho: 2480. Sobra: 118. Margen X = 59.
    MARGIN_X = 59
    MARGIN_Y = 150 
    GAP_X = 0      # Pegadas de lado
    GAP_Y = 10     # Separación vertical pequeña para corte
    
    cols = 2
    
    for i, datos in enumerate(lista_pedidos):
        if i >= 8: break 
        
        # Generar imagen individual (objeto PIL)
        tarjeta_img = generar_etiqueta_moto(datos, return_object=True)
        
        # Calcular posición
        col = i % cols
        row = i // cols
        
        x = MARGIN_X + (col * (CARD_W + GAP_X))
        y = MARGIN_Y + (row * (CARD_H + GAP_Y))
        
        # Pegar
        hoja.paste(tarjeta_img, (x, y))
        
        # Guía de corte gris muy suave
        draw = ImageDraw.Draw(hoja)
        draw.rectangle([x, y, x+CARD_W, y+CARD_H], outline=(200, 200, 200), width=2)

    # Exportar
    bio = io.BytesIO()
    hoja.save(bio, format='PNG')
    bio.seek(0)
    return bio