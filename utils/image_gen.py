from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf') 
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

# --- CONVERSIÓN DE MEDIDAS (300 DPI) ---
# Factor de conversión: 1 cm = 118.11 px
PIXELS_PER_CM = 118.11

def cm_to_px(cm):
    return int(cm * PIXELS_PER_CM)

# --- MEDIDAS DEL LIENZO (10 x 5.7 cm) ---
CARD_W = cm_to_px(10.0)   # 1181 px
CARD_H = cm_to_px(5.7)    # 673 px
A4_W, A4_H = 2480, 3508   # Hoja A4

# --- CONFIGURACIÓN EXACTA (TU PEDIDO) ---
# Margen General (0.3 cm)
MARGIN = cm_to_px(0.3)

# Caja Texto 1 (Remitente): 5.9 ancho x 2.3 alto
BOX1_W = cm_to_px(5.9)
BOX1_H = cm_to_px(2.3)

# Caja Texto 2 (Destinatario): 9.4 ancho x 2.4 alto
BOX2_W = cm_to_px(9.4)
BOX2_H = cm_to_px(2.4)

# Logo: 2.3 ancho x 2.1 alto
LOGO_W = cm_to_px(2.3)
LOGO_H = cm_to_px(2.1)

# Fuente: 10.1 pt
# Conversión técnica: 1 pt = 1/72 pulgada. A 300 DPI -> (10.1 * 300) / 72 = 42 px
FONT_SIZE_PX = 42
# Interlineado ajustado a la fuente
LINE_HEIGHT = int(FONT_SIZE_PX * 1.2) 

def generar_etiqueta_moto(datos, return_object=False):
    """
    Genera la etiqueta usando medidas milimétricas exactas.
    """
    img = Image.new('RGB', (CARD_W, CARD_H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # --- FUENTE ---
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE_PX)
    except:
        font = ImageFont.load_default()

    # ==========================================
    # 1. POSICIONAMIENTO DEL LOGO
    # ==========================================
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        
        # Redimensionar EXACTAMENTE a 2.3 x 2.1 cm
        logo = logo.resize((LOGO_W, LOGO_H), Image.Resampling.LANCZOS)
        
        # Posición:
        # X = Ancho Total - Margen Derecho (0.3) - Ancho Logo
        # Y = Centrado respecto a la altura de la caja 1 (para que quede lindo) o centrado total
        # Vamos a ponerlo alineado a la derecha respetando el margen de 0.3
        logo_x = CARD_W - MARGIN - LOGO_W
        # Centrado verticalmente respecto al área superior (Remitente) o absoluto?
        # Lo pondré centrado verticalmente respecto a la Caja 1 para equilibrar
        logo_y = MARGIN + (BOX1_H - LOGO_H) // 2 
        
        # Si prefieres centrado total vertical en la tarjeta, usa esta línea en su lugar:
        # logo_y = (CARD_H - LOGO_H) // 2
        
        img.paste(logo, (logo_x, logo_y), logo)
    except:
        pass

    # ==========================================
    # 2. CAJA DE TEXTO 1 (REMITENTE)
    # ==========================================
    # Coordenadas: (0.3, 0.3)
    cursor_x = MARGIN
    cursor_y = MARGIN

    sender_lines = [
        "DESDE:",
        "BOGOTÁ – YANETH PLAZAS",
        "CC.1026600344",
        "CEL: 3134553455", # Bajé el Celular para que entre mejor
        "CRA.29#3-24, VERAGUAS",
        # "YELLOWER.CO@GMAIL.COM" # Quizás no entre si es muy alto, probemos
    ]

    for line in sender_lines:
        # Verificar si nos salimos de la altura de la caja 1
        if (cursor_y - MARGIN) + LINE_HEIGHT > BOX1_H:
            break # No cabe más texto en la caja 1
        draw.text((cursor_x, cursor_y), line, font=font, fill=(255, 255, 255))
        cursor_y += LINE_HEIGHT

    # ==========================================
    # 3. CAJA DE TEXTO 2 (DESTINATARIO)
    # ==========================================
    # Esta caja empieza debajo de la Caja 1.
    # Y = Margen Arriba + Alto Caja 1 + Un pequeño respiro (o pegado)
    
    # Ubicación inicial de la caja 2
    box2_start_y = MARGIN + BOX1_H 
    cursor_x = MARGIN
    cursor_y = box2_start_y

    # Datos dinámicos
    ciudad = datos.get('ciudad', '').upper()
    depto = datos.get('depto', '').upper()
    nombre = datos.get('nombre', '').upper()
    cc = datos.get('cc', '').upper()
    tel = datos.get('telefono', '').upper()
    dir_envio = datos.get('direccion', '').upper()

    recipient_lines = [
        f"PARA: {ciudad}. {depto}",
        f"{nombre}",
        f"CC.{cc}  CEL: {tel}",
        f"{dir_envio}"
    ]

    for line in recipient_lines:
        # Controlar que no se salga de la tarjeta
        if cursor_y + LINE_HEIGHT > CARD_H - MARGIN:
            break
        draw.text((cursor_x, cursor_y), line, font=font, fill=(255, 255, 255))
        cursor_y += LINE_HEIGHT

    if return_object:
        return img

    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio

def generar_hoja_a4(lista_pedidos):
    """
    Pega hasta 8 etiquetas en una hoja A4.
    """
    hoja = Image.new('RGB', (A4_W, A4_H), color=(255, 255, 255))
    
    MARGIN_X = 59
    MARGIN_Y = 150 
    GAP_X = 0      
    GAP_Y = 10     
    cols = 2
    
    for i, datos in enumerate(lista_pedidos):
        if i >= 8: break 
        
        tarjeta_img = generar_etiqueta_moto(datos, return_object=True)
        col = i % cols
        row = i // cols
        x = MARGIN_X + (col * (CARD_W + GAP_X))
        y = MARGIN_Y + (row * (CARD_H + GAP_Y))
        hoja.paste(tarjeta_img, (x, y))
        
        # Guía de corte gris
        draw = ImageDraw.Draw(hoja)
        draw.rectangle([x, y, x+CARD_W, y+CARD_H], outline=(200, 200, 200), width=2)

    bio = io.BytesIO()
    hoja.save(bio, format='PNG')
    bio.seek(0)
    return bio