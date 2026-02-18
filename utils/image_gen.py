from PIL import Image, ImageDraw, ImageFont
import io
import os

# ============================================================================
# 1. CONFIGURACIÓN EXACTA (COPIADA DE TU SCRIPT DE REFERENCIA)
# ============================================================================

# Rutas de archivos (Ajustado para la estructura del bot)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf') 
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

# --- CONSTANTES MATEMÁTICAS DEL SCRIPT "BUENO" ---
DPI = 300
SCALE = 300 / 144

# Dimensiones calculadas igual que en tu referencia
CARD_W = int(566.63 * SCALE)
CARD_H = int(323.79 * SCALE)
MARGEN_PX = int(0.3 * 118.11)

# Dimensiones Hoja A4 Real
A4_W = 2480
A4_H = 3508

# --- COORDENADAS DE REFERENCIA (ABSOLUTAS EN TU HOJA DE PRUEBA) ---
# Copiamos tus valores exactos:
REF_T1_X = 42 * SCALE
REF_T1_Y = 750 * SCALE
REF_T2_X = 42 * SCALE
REF_T2_Y = 900 * SCALE  # Tu ajuste bajado a 900
REF_L_X = 408 * SCALE
REF_L_Y = 834 * SCALE
REF_L_W = int(163 * SCALE)
REF_L_H = int(121 * SCALE)

# Padding interno que usabas en el loop: "draw.text((... + (5 * SCALE)..."
PADDING_TEXTO = 5 * SCALE
ESPACIO_LINEA = int(26 * SCALE)
TAMANO_FUENTE = int(20 * SCALE)

# --- CÁLCULO DE TRADUCCIÓN (LO IMPORTANTE) ---
# Calculamos dónde empezaba la tarjeta negra en tu hoja de referencia
REF_CARD_START_X = REF_T1_X - MARGEN_PX
REF_CARD_START_Y = REF_T1_Y - MARGEN_PX

# Ahora calculamos las posiciones RELATIVAS para que queden dentro de la tarjeta (0,0)
# Fórmula: Posición_Original - Inicio_Tarjeta_Original

# Texto 1 (Remitente)
REL_TXT_X = (REF_T1_X + PADDING_TEXTO) - REF_CARD_START_X
REL_T1_Y = (REF_T1_Y + PADDING_TEXTO) - REF_CARD_START_Y

# Texto 2 (Destinatario)
REL_T2_Y = (REF_T2_Y + PADDING_TEXTO) - REF_CARD_START_Y

# Logo
REL_LOGO_X = REF_L_X - REF_CARD_START_X
REL_LOGO_Y = REF_L_Y - REF_CARD_START_Y


# ============================================================================
# 2. MOTOR DE GENERACIÓN
# ============================================================================

def _crear_tarjeta_base(datos):
    """
    Crea el objeto Image (PIL) de la tarjeta negra individual.
    Es un recorte matemáticamente perfecto de tu diseño original.
    """
    # 1. Lienzo Negro del tamaño exacto de la tarjeta
    img = Image.new('RGB', (CARD_W, CARD_H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 2. Cargar Fuente
    try:
        font = ImageFont.truetype(FONT_PATH, TAMANO_FUENTE)
    except:
        font = ImageFont.load_default()

    # 3. Bloque 1: Remitente (Fijo - Yaneth Plazas)
    remitente = [
        "DESDE:",
        "BOGOTÁ - YANETH PLAZAS",
        "CC.1026600344 CEL: 3134553455",
        "CRA.29#3-24, VERAGUAS CP.111411",
        "YELLOWER.CO@GMAIL.COM"
    ]
    
    cy = REL_T1_Y
    for line in remitente:
        draw.text((REL_TXT_X, cy), line, font=font, fill="white")
        cy += ESPACIO_LINEA

    # 4. Bloque 2: Destinatario (Dinámico)
    # Obtenemos los datos con .get() para evitar errores si falta algo
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
    
    cy = REL_T2_Y
    for line in destinatario:
        draw.text((REL_TXT_X, cy), line, font=font, fill="white")
        cy += ESPACIO_LINEA

    # 5. Logo
    try:
        if os.path.exists(LOGO_PATH):
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo = logo.resize((REF_L_W, REF_L_H), Image.Resampling.LANCZOS)
            # Pegar usando el mismo logo como máscara para transparencia
            img.paste(logo, (int(REL_LOGO_X), int(REL_LOGO_Y)), logo)
        else:
            print("⚠️ Advertencia: No se encontró el logo en assets/images/logo_white.png")
    except Exception as e:
        print(f"⚠️ Error pegando logo: {e}")

    return img


# ============================================================================
# 3. FUNCIONES PARA EL BOT (API)
# ============================================================================

def generar_etiqueta_unica(datos):
    """
    Genera SOLO la tarjeta negra (sin hoja blanca).
    Retorna: BytesIO para enviar por Telegram.
    """
    img = _crear_tarjeta_base(datos)
    
    bio = io.BytesIO()
    img.save(bio, format='PNG', dpi=(DPI, DPI))
    bio.seek(0)
    return bio

def generar_hoja_a4(lista_datos):
    """
    Genera una hoja A4 BLANCA y pega hasta 8 tarjetas negras.
    Retorna: BytesIO para enviar por Telegram.
    """
    if not lista_datos:
        return None

    # 1. Crear Hoja A4 BLANCA
    hoja = Image.new('RGB', (A4_W, A4_H), color=(255, 255, 255))
    draw = ImageDraw.Draw(hoja)
    
    # 2. Configuración de impresión (Márgenes seguros)
    MARGIN_X = 50  # Margen izquierdo de la hoja
    MARGIN_Y = 50  # Margen superior de la hoja
    GAP = 20       # Espacio entre tarjetas
    COLS = 2       # Columnas

    # 3. Iterar y pegar
    for i, datos in enumerate(lista_datos):
        if i >= 8: break # Límite físico de la hoja
        
        # Generamos la tarjeta negra perfecta
        tarjeta = _crear_tarjeta_base(datos)
        
        # Calculamos posición en la grilla A4
        col = i % COLS
        row = i // COLS
        
        x = MARGIN_X + (col * (CARD_W + GAP))
        y = MARGIN_Y + (row * (CARD_H + GAP))
        
        # Pegamos la tarjeta negra sobre el fondo blanco
        hoja.paste(tarjeta, (int(x), int(y)))
        
        # (Opcional) Guía de corte gris muy finita
        draw.rectangle([x, y, x + CARD_W, y + CARD_H], outline=(200, 200, 200), width=1)

    bio = io.BytesIO()
    hoja.save(bio, format='PNG', dpi=(DPI, DPI))
    bio.seek(0)
    return bio

# --- PARCHE DE COMPATIBILIDAD ---
# Si algún código viejo llama a esta función, lo redirigimos a la etiqueta única
def generar_etiqueta_moto(datos, return_object=False):
    if return_object:
        return _crear_tarjeta_base(datos)
    return generar_etiqueta_unica(datos)