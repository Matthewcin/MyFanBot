from PIL import Image, ImageDraw, ImageFont
import io
import os

# ==========================================
# 1. CONFIGURACIÓN Y RUTAS (CON DEBUG)
# ==========================================

# Construcción de rutas absolutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf') 
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

# --- DEBUG: IMPRIMIR RUTAS EN CONSOLA ---
print(f"[DEBUG] BASE_DIR: {BASE_DIR}")
print(f"[DEBUG] FONT_PATH: {FONT_PATH} - Existe: {os.path.exists(FONT_PATH)}")
print(f"[DEBUG] LOGO_PATH: {LOGO_PATH} - Existe: {os.path.exists(LOGO_PATH)}")
# ----------------------------------------

# Configuración HD (300 DPI)
DPI = 300
SCALE = 300 / 144  # aprox 2.0833

# --- MEDIDAS DE LA TARJETA NEGRA (Calculadas) ---
CARD_W = int(566.63 * SCALE) # ~1180 px
CARD_H = int(323.79 * SCALE) # ~674 px

# --- MEDIDAS HOJA A4 ---
A4_W = 2480
A4_H = 3508

# --- COORDENADAS RELATIVAS FINALES (DENTRO DE LA TARJETA) ---
# Estos valores son el resultado exacto de la matemática de tu script de referencia.
# Colocan los elementos en la misma posición visual.

# Margen izquierdo para todo el texto
POS_X_TEXTO = int(45 * SCALE)

# Altura Texto 1 (Remitente)
POS_Y_T1 = int(45 * SCALE)

# Altura Texto 2 (Destinatario) - Basado en tu ajuste de 900
POS_Y_T2 = int(358 * SCALE)

# Posición Logo
POS_X_LOGO = int(850 * SCALE) # Ajustado a la derecha
POS_Y_LOGO = int(45 * SCALE)  # Alineado arriba

# Tamaño Logo (163x121 escalado)
LOGO_W = int(163 * SCALE)
LOGO_H = int(121 * SCALE)

# Espaciado y Fuente
LINE_SPACING = int(26 * SCALE)
FONT_SIZE = int(20 * SCALE)


# ==========================================
# 2. MOTOR GRÁFICO
# ==========================================

def _crear_tarjeta_base(datos):
    """
    Genera la imagen de la tarjeta negra.
    """
    img = Image.new('RGB', (CARD_W, CARD_H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 1. CARGAR FUENTE (CON DEBUG)
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except Exception as e:
        print(f"[ERROR] No se pudo cargar la fuente 'negrita.ttf'. Usando default. Error: {e}")
        font = ImageFont.load_default()

    # 2. DATOS REMITENTE (Fijos)
    sender_lines = [
        "DESDE:",
        "BOGOTÁ - YANETH PLAZAS",
        "CC.1026600344 CEL: 3134553455",
        "CRA.29#3-24, VERAGUAS CP.111411",
        "YELLOWER.CO@GMAIL.COM"
    ]
    
    curr_y = POS_Y_T1
    for line in sender_lines:
        draw.text((POS_X_TEXTO, curr_y), line, font=font, fill="white")
        curr_y += LINE_SPACING

    # 3. DATOS DESTINATARIO (Dinámicos)
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

    curr_y = POS_Y_T2
    for line in recipient_lines:
        draw.text((POS_X_TEXTO, curr_y), line, font=font, fill="white")
        curr_y += LINE_SPACING

    # 4. PEGAR LOGO (CON DEBUG)
    try:
        if os.path.exists(LOGO_PATH):
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo = logo.resize((LOGO_W, LOGO_H), Image.Resampling.LANCZOS)
            # Pegar en la esquina superior derecha
            target_x = CARD_W - LOGO_W - int(50 * SCALE)
            target_y = POS_Y_T1
            img.paste(logo, (target_x, target_y), logo)
            print("[DEBUG] Logo pegado correctamente.")
        else:
            print(f"[ERROR] El archivo de logo NO EXISTE en: {LOGO_PATH}")
    except Exception as e:
        print(f"[ERROR] Falló al procesar/pegar el logo: {e}")

    return img


# ==========================================
# 3. FUNCIONES PÚBLICAS
# ==========================================

def generar_etiqueta_unica(datos):
    img = _crear_tarjeta_base(datos)
    bio = io.BytesIO()
    img.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio

def generar_hoja_a4(lista_datos):
    if not lista_datos: return None
    
    hoja = Image.new('RGB', (A4_W, A4_H), color=(255, 255, 255))
    draw = ImageDraw.Draw(hoja)
    
    MARGIN_X, MARGIN_Y = 50, 50
    GAP = 20
    COLS = 2

    for i, datos in enumerate(lista_datos):
        if i >= 8: break
        tarjeta = _crear_tarjeta_base(datos)
        col, row = i % COLS, i // COLS
        x = MARGIN_X + (col * (CARD_W + GAP))
        y = MARGIN_Y + (row * (CARD_H + GAP))
        hoja.paste(tarjeta, (int(x), int(y)))
        draw.rectangle([x, y, x + CARD_W, y + CARD_H], outline=(200, 200, 200), width=1)

    bio = io.BytesIO()
    hoja.save(bio, format='PNG', dpi=(300, 300))
    bio.seek(0)
    return bio

# Parche de compatibilidad
def generar_etiqueta_moto(datos, return_object=False):
    if return_object: return _crear_tarjeta_base(datos)
    return generar_etiqueta_unica(datos)