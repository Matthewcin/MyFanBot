from PIL import Image, ImageDraw, ImageFont
import io
import os

# ==========================================
# 1. CONSTANTES EXACTAS (TU CALIBRACIÓN)
# ==========================================

# Ajustamos la ruta base para que funcione dentro de la carpeta 'utils'
# Sube un nivel para encontrar la carpeta 'assets'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf') 
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

DPI = 300
SCALE = 300 / 144

# Dimensiones del Lienzo de trabajo (Tu hoja gris)
HOJA_W = int(1191 * SCALE)
HOJA_H = int(1684.5 * SCALE)

# Dimensiones de la Tarjeta
CARD_W = 566.63 * SCALE
CARD_H = 323.79 * SCALE

MARGEN_PX = int(0.3 * 118.11)

# Coordenadas exactas de tu código
T1_X, T1_Y = 42 * SCALE, 750 * SCALE
T1_W, T1_H = 326 * SCALE, 128 * SCALE

# Ajuste confirmado: 900
T2_X, T2_Y = 42 * SCALE, 900 * SCALE 
T2_W = CARD_W - (2 * MARGEN_PX)
T2_H = 126 * SCALE

L_X, L_Y = 408 * SCALE, 834 * SCALE
L_W, L_H = 163 * SCALE, 121 * SCALE

CARD_X = T1_X - MARGEN_PX
CARD_Y = T1_Y - MARGEN_PX


# ==========================================
# 2. MOTOR DE GENERACIÓN (NÚCLEO)
# ==========================================

def _crear_tarjeta_recortada(datos):
    """
    Dibuja la hoja completa usando TU código exacto, 
    pero al final recorta y devuelve solo la tarjeta negra.
    """
    # 1. Crear el lienzo grande (igual que tu script)
    img = Image.new('RGB', (HOJA_W, HOJA_H), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    # 2. Dibujar rectángulo negro (igual que tu script)
    draw.rectangle([CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H], fill=(0, 0, 0))

    # 3. Cargar Fuente
    try:
        font = ImageFont.truetype(FONT_PATH, int(20 * SCALE))
    except:
        font = ImageFont.load_default()

    # 4. Texto Remitente (Fijo)
    remitente = [
        "DESDE:",
        "BOGOTÁ - YANETH PLAZAS",
        "CC.1026600344 CEL: 3134553455",
        "CRA.29#3-24, VERAGUAS CP.111411",
        "YELLOWER.CO@GMAIL.COM"
    ]
    
    cy = T1_Y + (5 * SCALE)
    for line in remitente:
        draw.text((T1_X + (5 * SCALE), cy), line, font=font, fill="white")
        cy += int(26 * SCALE)

    # 5. Texto Destinatario (Dinámico desde el Bot)
    nombre = datos.get('nombre', '').upper()
    destino = datos.get('destino', '').upper()
    cc = datos.get('cc', '').upper()
    tel = datos.get('telefono', '').upper()
    direccion = datos.get('direccion', '').upper()
    barrio = datos.get('barrio', '').upper()

    destinatario = [
        f"ENVIAR A: {destino}",
        f"{nombre}",
        f"CC.{cc}  CEL: {tel}",
        f"{direccion}",
        f"BRR: {barrio}"
    ]
    
    cy = T2_Y + (5 * SCALE)
    for line in destinatario:
        draw.text((T2_X + (5 * SCALE), cy), line, font=font, fill="white")
        cy += int(26 * SCALE)

    # 6. Logo
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo = logo.resize((int(L_W), int(L_H)), Image.Resampling.LANCZOS)
        img.paste(logo, (int(L_X), int(L_Y)), logo)
    except Exception as e:
        print(f"Error logo: {e}")
        pass

    # 7. EL TRUCO: Recortamos solo la parte negra
    # Usamos las coordenadas exactas donde dibujaste el rectángulo negro
    box = (int(CARD_X), int(CARD_Y), int(CARD_X + CARD_W), int(CARD_Y + CARD_H))
    tarjeta_final = img.crop(box)
    
    return tarjeta_final


# ==========================================
# 3. FUNCIONES PARA EL BOT
# ==========================================

def generar_etiqueta_unica(datos):
    """
    Retorna solo la tarjeta negra (sin hoja).
    """
    img = _crear_tarjeta_recortada(datos)
    
    bio = io.BytesIO()
    img.save(bio, format='PNG', dpi=(DPI, DPI))
    bio.seek(0)
    return bio


def generar_hoja_a4(lista_datos):
    """
    Crea una hoja blanca A4 y pega las tarjetas negras en orden (hasta 8).
    """
    if not lista_datos:
        return None

    # Dimensiones A4 a 300 DPI
    A4_WIDTH = 2480
    A4_HEIGHT = 3508
    
    # Crear hoja blanca limpia
    hoja = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), color=(255, 255, 255))
    draw = ImageDraw.Draw(hoja)

    # Configuración de grilla para pegar las tarjetas
    MARGIN_X = 50
    MARGIN_Y = 50
    GAP = 20
    COLS = 2

    # Medidas reales de la tarjeta recortada
    w_card = int(CARD_W)
    h_card = int(CARD_H)

    for i, datos in enumerate(lista_datos):
        if i >= 8: break
        
        # Generamos la tarjeta negra perfecta usando tu código base
        tarjeta = _crear_tarjeta_recortada(datos)
        
        # Calcular posición
        col = i % COLS
        row = i // COLS
        
        x = MARGIN_X + (col * (w_card + GAP))
        y = MARGIN_Y + (row * (h_card + GAP))
        
        # Pegar
        hoja.paste(tarjeta, (x, y))
        
        # Línea de corte gris
        draw.rectangle([x, y, x + w_card, y + h_card], outline=(200, 200, 200), width=1)

    bio = io.BytesIO()
    hoja.save(bio, format='PNG', dpi=(DPI, DPI))
    bio.seek(0)
    return bio


# Compatibilidad para que shipping.py no falle
def generar_etiqueta_moto(datos, return_object=False):
    if return_object:
        return _crear_tarjeta_recortada(datos)
    return generar_etiqueta_unica(datos)