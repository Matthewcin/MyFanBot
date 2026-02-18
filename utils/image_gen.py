from PIL import Image, ImageDraw, ImageFont
import io
import os

# ==========================================
# 1. CONSTANTES EXACTAS (DE TU CALIBRACIÓN)
# ==========================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf')
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

DPI = 300
SCALE = 300 / 144

# Dimensiones del Lienzo de trabajo (Hoja gris)
HOJA_W = int(1191 * SCALE)
HOJA_H = int(1684.5 * SCALE)

# Dimensiones de la Tarjeta
CARD_W = 566.63 * SCALE
CARD_H = 323.79 * SCALE

MARGEN_PX = int(0.3 * 118.11)

# NUEVAS COORDENADAS (arriba a la izquierda)
OFFSET_Y = 30 * SCALE                     # Posición superior de la tarjeta

# Posiciones horizontales (margen izquierdo)
T1_X = 42 * SCALE
T2_X = 42 * SCALE
L_X  = 408 * SCALE

# Dimensiones de los bloques de texto
T1_W, T1_H = 326 * SCALE, 128 * SCALE
T2_W = CARD_W - (2 * MARGEN_PX)
T2_H = 126 * SCALE
L_W, L_H = 163 * SCALE, 121 * SCALE

# Posiciones verticales
T1_Y = OFFSET_Y + (15 * SCALE)            # Bloque remitente
T2_Y = OFFSET_Y + (160 * SCALE)           # Bloque destinatario (más abajo)

# Logo centrado verticalmente
centro_tarjeta_y = OFFSET_Y + (CARD_H / 2)
L_Y = centro_tarjeta_y - (L_H / 2)

# Coordenadas de la tarjeta (esquina superior izquierda)
CARD_X = T1_X - MARGEN_PX
CARD_Y = OFFSET_Y
# ==========================================

def _crear_tarjeta_recortada(datos):
    """
    Dibuja la hoja completa usando las coordenadas calibradas,
    y recorta solo la tarjeta negra.
    """
    img = Image.new('RGB', (HOJA_W, HOJA_H), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    # 1. Fondo negro de la tarjeta
    draw.rectangle([CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H], fill=(0, 0, 0))

    # 2. Fuente
    try:
        font = ImageFont.truetype(FONT_PATH, int(20 * SCALE))
    except:
        try:
            # Fallback a Arial en Windows
            font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", int(20 * SCALE))
        except:
            font = ImageFont.load_default()

    # 3. Texto Remitente (fijo)
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

    # 4. Texto Destinatario (dinámico desde la BD)
    ciudad = datos.get('ciudad', '').upper().strip()
    depto  = datos.get('depto', '').upper().strip()
    if ciudad and depto:
        destino = f"{ciudad}-{depto}"
    else:
        destino = ciudad or depto or "DESTINO NO ESPECIFICADO"

    nombre    = datos.get('nombre', '').upper() or "NOMBRE NO ESPECIFICADO"
    cc        = datos.get('cc', '').upper() or "0000000000"
    telefono  = datos.get('telefono', '').upper() or "0000000000"
    direccion = datos.get('direccion', '').upper() or "DIRECCION NO ESPECIFICADA"
    barrio    = datos.get('barrio', '').upper() or "-"

    destinatario = [
        f"ENVIAR A: {destino}",
        f"{nombre}",
        f"CC.{cc}  CEL: {telefono}",
        f"{direccion}",
        f"BRR: {barrio}"
    ]

    cy = T2_Y + (5 * SCALE)
    for line in destinatario:
        draw.text((T2_X + (5 * SCALE), cy), line, font=font, fill="white")
        cy += int(26 * SCALE)

    # 5. Logo
    try:
        if os.path.exists(LOGO_PATH):
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo = logo.resize((int(L_W), int(L_H)), Image.Resampling.LANCZOS)
            img.paste(logo, (int(L_X), int(L_Y)), logo)
        else:
            # Dibujar placeholder si no hay logo
            draw.rectangle([L_X, L_Y, L_X + L_W, L_Y + L_H], fill=(100, 100, 100), outline=(255, 255, 255))
            draw.text((L_X + 20, L_Y + 40), "LOGO", font=font, fill="white")
    except Exception as e:
        print(f"Error con logo: {e}")
        # Dibujar placeholder
        draw.rectangle([L_X, L_Y, L_X + L_W, L_Y + L_H], fill=(100, 100, 100), outline=(255, 255, 255))
        draw.text((L_X + 20, L_Y + 40), "LOGO", font=font, fill="white")

    # 6. Recortar solo la tarjeta
    box = (int(CARD_X), int(CARD_Y), int(CARD_X + CARD_W), int(CARD_Y + CARD_H))
    tarjeta_final = img.crop(box)
    return tarjeta_final

# ==========================================
# 2. FUNCIONES PÚBLICAS
# ==========================================

def generar_etiqueta_unica(datos):
    """Retorna la tarjeta negra (sin hoja) en un BytesIO."""
    img = _crear_tarjeta_recortada(datos)
    bio = io.BytesIO()
    img.save(bio, format='PNG', dpi=(DPI, DPI))
    bio.seek(0)
    return bio

def generar_hoja_a4(lista_datos):
    """Crea una hoja A4 blanca y pega hasta 8 tarjetas en grilla."""
    if not lista_datos:
        return None

    # Dimensiones A4 estándar a 300 DPI
    A4_WIDTH = 2480
    A4_HEIGHT = 3508
    
    hoja = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), color=(255, 255, 255))
    draw = ImageDraw.Draw(hoja)

    # Configuración de grilla
    MARGIN_X = 50
    MARGIN_Y = 50
    GAP = 20
    COLS = 2

    w_card = int(CARD_W)
    h_card = int(CARD_H)

    for i, datos in enumerate(lista_datos):
        if i >= 8:  # Máximo 8 tarjetas por hoja A4
            break
            
        tarjeta = _crear_tarjeta_recortada(datos)
        
        col = i % COLS
        row = i // COLS
        
        x = MARGIN_X + (col * (w_card + GAP))
        y = MARGIN_Y + (row * (h_card + GAP))
        
        hoja.paste(tarjeta, (x, y))
        
        # Línea de corte gris
        draw.rectangle([x, y, x + w_card, y + h_card], outline=(200, 200, 200), width=2)

    bio = io.BytesIO()
    hoja.save(bio, format='PNG', dpi=(DPI, DPI))
    bio.seek(0)
    return bio

def generar_etiqueta_moto(datos, return_object=False):
    """Compatibilidad con código antiguo."""
    if return_object:
        return _crear_tarjeta_recortada(datos)
    return generar_etiqueta_unica(datos)

# ==========================================
# 3. FUNCIÓN DE PRUEBA (opcional)
# ==========================================

if __name__ == "__main__":
    print("🧪 Probando generador de imágenes...")
    
    # Datos de prueba
    datos_prueba = {
        'nombre': 'JUAN PÉREZ GÓMEZ',
        'ciudad': 'MEDELLÍN',
        'depto': 'ANTIOQUIA',
        'cc': '1234567890',
        'telefono': '3001234567',
        'direccion': 'CALLE 50 # 65-20 APTO 301',
        'barrio': 'LAURELES'
    }
    
    # Generar tarjeta individual
    img_bio = generar_etiqueta_unica(datos_prueba)
    with open("test_tarjeta.png", "wb") as f:
        f.write(img_bio.getvalue())
    print("✅ Tarjeta individual guardada como test_tarjeta.png")
    
    # Generar hoja A4 con 4 tarjetas
    lista = [datos_prueba] * 4
    hoja_bio = generar_hoja_a4(lista)
    with open("test_hoja.png", "wb") as f:
        f.write(hoja_bio.getvalue())
    print("✅ Hoja A4 guardada como test_hoja.png")