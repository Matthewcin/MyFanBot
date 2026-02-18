from PIL import Image, ImageDraw, ImageFont
import io
import os

# ==========================================
# 1. CONFIGURACIÓN Y CONSTANTES
# ==========================================

# Rutas (Ajustadas para subir un nivel desde 'utils' a 'assets')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf') 
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

# Configuración HD (300 DPI)
DPI = 300
SCALE = 300 / 144  # aprox 2.0833

# --- MEDIDAS DE LA TARJETA NEGRA ---
# (Calculadas con tus fórmulas originales)
CARD_W = int(566.63 * SCALE)
CARD_H = int(323.79 * SCALE)

# --- MEDIDAS DE LA HOJA A4 BLANCA ---
A4_W = 2480
A4_H = 3508

# --- MATEMÁTICAS DE COORDENADAS (RELATIVAS A LA TARJETA) ---
# Traducimos las coordenadas "absolutas de la hoja de prueba" a 
# coordenadas "relativas (0,0)" dentro de la tarjeta negra.

# Tu margen base
MARGEN_PX = int(0.3 * 118.11)
# El padding interno que usabas en el draw.text
PADDING_TXT = int(5 * SCALE)
# Espaciado entre líneas
LINE_SPACING = int(26 * SCALE)

# Posición X del Texto (Izquierda)
REL_X_TXT = MARGEN_PX + PADDING_TXT

# Posición Y del Texto 1 (Remitente)
REL_Y_T1 = MARGEN_PX + PADDING_TXT

# Posición Y del Texto 2 (Destinatario)
# Diferencia entre T2 (900) y T1 (750) = 150 * SCALE
REL_Y_T2 = int(150 * SCALE) + MARGEN_PX + PADDING_TXT

# Posición del Logo
# X: Diferencia entre Logo (408) y Inicio Tarjeta (42) = 366 * SCALE
REL_X_LOGO = int(366 * SCALE) + MARGEN_PX
# Y: Diferencia entre Logo (834) y Inicio Tarjeta (750) = 84 * SCALE
REL_Y_LOGO = int(84 * SCALE) + MARGEN_PX

# Tamaño Logo (163x121 escalado)
LOGO_W = int(163 * SCALE)
LOGO_H = int(121 * SCALE)


# ==========================================
# 2. MOTOR GRÁFICO (PRIVADO)
# ==========================================

def _crear_tarjeta_individual(datos):
    """
    Genera un objeto Image (PIL) de la tarjeta negra con los datos inyectados.
    """
    # 1. Crear lienzo negro del tamaño exacto de la tarjeta
    img = Image.new('RGB', (CARD_W, CARD_H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 2. Cargar Fuente
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
    
    curr_y = REL_Y_T1
    for line in sender_lines:
        draw.text((REL_X_TXT, curr_y), line, font=font, fill="white")
        curr_y += LINE_SPACING

    # 4. Datos Destinatario (Dinámicos desde la BD)
    # Usamos .get() con valores vacíos por seguridad
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

    curr_y = REL_Y_T2
    for line in recipient_lines:
        draw.text((REL_X_TXT, curr_y), line, font=font, fill="white")
        curr_y += LINE_SPACING

    # 5. Pegar Logo
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo = logo.resize((LOGO_W, LOGO_H), Image.Resampling.LANCZOS)
        img.paste(logo, (REL_X_LOGO, REL_Y_LOGO), logo)
    except Exception as e:
        print(f"Warning: No se pudo cargar el logo: {e}")
        pass

    return img


# ==========================================
# 3. FUNCIONES PÚBLICAS (API DEL BOT)
# ==========================================

def generar_etiqueta_unica(datos):
    """
    Caso 1: El usuario pide solo UNA etiqueta.
    Retorna: Bytes de la tarjeta negra (sin hoja A4).
    """
    img = _crear_tarjeta_individual(datos)
    
    bio = io.BytesIO()
    img.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio


def generar_hoja_a4(lista_datos):
    """
    Caso 2: El usuario pide varias etiquetas (o una lista).
    Retorna: Bytes de la hoja A4 BLANCA con las tarjetas organizadas.
    Capacidad: Hasta 8 tarjetas por hoja.
    """
    # Si la lista está vacía, retornar nada
    if not lista_datos:
        return None
    
    # --- LÓGICA DE GRILLA A4 ---
    # Crear hoja blanca
    hoja = Image.new('RGB', (A4_W, A4_H), color=(255, 255, 255))
    draw = ImageDraw.Draw(hoja)
    
    # Márgenes de impresión (Arriba a la Izquierda)
    START_X = 50
    START_Y = 50
    GAP = 20   # Espacio entre tarjetas
    COLS = 2   # 2 Columnas
    
    # Iterar sobre los datos (Máximo 8)
    for i, datos in enumerate(lista_datos):
        if i >= 8: break 
        
        # 1. Generar la tarjeta negra individual
        tarjeta = _crear_tarjeta_individual(datos)
        
        # 2. Calcular posición (Fila y Columna)
        col = i % COLS
        row = i // COLS
        
        x = START_X + (col * (CARD_W + GAP))
        y = START_Y + (row * (CARD_H + GAP))
        
        # 3. Pegar en la hoja
        hoja.paste(tarjeta, (x, y))
        
        # 4. Dibujar línea de corte gris (opcional, ayuda al cortar)
        draw.rectangle([x, y, x + CARD_W, y + CARD_H], outline=(200, 200, 200), width=1)

    bio = io.BytesIO()
    hoja.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio

# --- PARCHE DE COMPATIBILIDAD ---
# Si tu código antiguo llamaba a 'generar_etiqueta_moto', lo redirigimos a la única.
def generar_etiqueta_moto(datos, return_object=False):
    if return_object:
        return _crear_tarjeta_individual(datos)
    return generar_etiqueta_unica(datos)