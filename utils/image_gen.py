from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- RUTAS ---
# Ajusta según tu estructura de carpetas
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
MARGEN_PX = int(0.3 * 118.11) # Margen rojo interno de la tarjeta

# DIMENSIONES HOJA A4
A4_W = 2480
A4_H = 3508

# --- CÁLCULO DE POSICIONES RELATIVAS ---
# Aquí traducimos las coordenadas de tu calibración "media hoja" 
# a coordenadas relativas dentro de la tarjeta (0,0).

# El padding extra de (5 * SCALE) que usaste en tu código
PADDING_TXT = int(5 * SCALE)

# 1. Inicio Texto (X)
# En tu código: T1_X + (5*SCALE). T1_X era (CARD_X + MARGEN).
# Por tanto: Margen + 5*Scale
POS_X_TXT = MARGEN_PX + PADDING_TXT

# 2. Altura Texto 1 (Remitente)
# Empieza justo después del margen superior
POS_Y_T1 = MARGEN_PX + PADDING_TXT

# 3. Altura Texto 2 (Destinatario)
# En tu código: T2_Y = 900. Card_Y (Top) = 750 (aprox).
# Diferencia visual: 150 * SCALE.
POS_Y_T2 = int(150 * SCALE) + MARGEN_PX

# 4. Posición Logo
# En tu código: L_X = 408, L_Y = 834. Card_X = 42, Card_Y = 750.
# Diferencia X: 408 - 42 = 366.
# Diferencia Y: 834 - 750 = 84.
POS_X_LOGO = int(366 * SCALE) + MARGEN_PX
POS_Y_LOGO = int(84 * SCALE) + MARGEN_PX

# Tamaño Logo (Del código que pasaste: 163x121)
SIZE_W_LOGO = int(163 * SCALE)
SIZE_H_LOGO = int(121 * SCALE)


def generar_etiqueta_moto(datos, return_object=False):
    """
    Genera UNA sola tarjeta negra perfecta (objeto Image).
    """
    img = Image.new('RGB', (CARD_W, CARD_H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(FONT_PATH, int(20 * SCALE))
    except:
        font = ImageFont.load_default()

    line_spacing = int(26 * SCALE)

    # --- BLOQUE 1: REMITENTE (Yaneth Plazas) ---
    sender_lines = [
        "DESDE:",
        "BOGOTÁ - YANETH PLAZAS",
        "CC.1026600344 CEL: 3134553455",
        "CRA.29#3-24, VERAGUAS CP.111411",
        "YELLOWER.CO@GMAIL.COM"
    ]

    curr_y = POS_Y_T1
    for line in sender_lines:
        draw.text((POS_X_TXT, curr_y), line, font=font, fill="white")
        curr_y += line_spacing

    # --- BLOQUE 2: DESTINATARIO (Dinámico del Bot) ---
    # Recuperamos la lógica de "MyFanBox"
    nombre = datos.get('nombre', '').upper()
    destino = datos.get('destino', '').upper() # Ciudad - Depto
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

    curr_y = POS_Y_T2
    for line in recipient_lines:
        draw.text((POS_X_TXT, curr_y), line, font=font, fill="white")
        curr_y += line_spacing

    # --- LOGO ---
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo = logo.resize((SIZE_W_LOGO, SIZE_H_LOGO), Image.Resampling.LANCZOS)
        img.paste(logo, (POS_X_LOGO, POS_Y_LOGO), logo)
    except:
        pass
    
    # Si pedimos el objeto para pegarlo en A4
    if return_object:
        return img

    # Si pedimos el archivo directo (por compatibilidad)
    bio = io.BytesIO()
    img.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio


def generar_hoja_a4(lista_pedidos):
    """
    Genera una hoja A4 y pega las etiquetas empezando ARRIBA A LA IZQUIERDA.
    """
    if not lista_pedidos:
        return None

    # 1. Crear Hoja A4 BLANCA
    hoja = Image.new('RGB', (A4_W, A4_H), color=(255, 255, 255))
    draw = ImageDraw.Draw(hoja)
    
    # --- CONFIGURACIÓN DE MÁRGENES DE IMPRESIÓN ---
    # Margen izquierdo y superior (50px es aprox 0.4cm, seguro para imprimir)
    MARGIN_PAGE_X = 50
    MARGIN_PAGE_Y = 50
    
    # Espacio entre tarjetas
    GAP = 20
    
    # Columnas por hoja (2 entra bien en A4 vertical)
    COLS = 2

    for i, datos in enumerate(lista_pedidos):
        if i >= 8: break # Máximo 8 por hoja
        
        # Generar la tarjeta negra individual
        tarjeta = generar_etiqueta_moto(datos, return_object=True)
        
        # Calcular posición (Grid)
        col = i % COLS
        row = i // COLS
        
        x = MARGIN_PAGE_X + (col * (CARD_W + GAP))
        y = MARGIN_PAGE_Y + (row * (CARD_H + GAP))
        
        # Pegar tarjeta
        hoja.paste(tarjeta, (x, y))
        
        # (Opcional) Línea de corte gris muy fina para guillotina
        draw.rectangle([x, y, x + CARD_W, y + CARD_H], outline=(200, 200, 200), width=1)

    bio = io.BytesIO()
    hoja.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio