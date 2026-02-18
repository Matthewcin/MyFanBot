# utils/image_gen.py
from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- CONFIGURACIÓN DE RUTAS ---
# Esto busca las carpetas automáticamente dentro de 'utils/assets/'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'Poppins-Regular.ttf')
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.webp')

def generar_etiqueta_moto(datos):
    """
    Genera la etiqueta negra estilo "motomandado".
    Recibe un diccionario 'datos' con: ciudad, depto, nombre, cc, telefono, direccion.
    """
    # 1. Crear lienzo negro (Ancho 800 x Alto 450 aprox)
    W, H = 800, 450
    img = Image.new('RGB', (W, H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 2. Cargar Fuente y Logo
    WHITE = (255, 255, 255)
    try:
        # Tamaño 24 se asemeja a la muestra
        font = ImageFont.truetype(FONT_PATH, 24)
    except OSError:
        print("⚠️ ERROR: No se encontró el archivo .ttf en utils/assets/fonts/")
        # Fallback a fuente fea por defecto si falla
        font = ImageFont.load_default()

    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        # Redimensionar logo proporcionalmente (ej: ancho 220px)
        aspect_ratio = logo.height / logo.width
        new_width = 220
        new_height = int(new_width * aspect_ratio)
        logo = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
    except FileNotFoundError:
         print("⚠️ ERROR: No se encontró logo_white.png en utils/assets/images/")
         logo = None

    # 3. Definir Márgenes y Espaciado
    MARGIN_LEFT = 40
    CURRENT_Y = 40    # Posición vertical inicial
    LINE_HEIGHT = 38  # Espacio entre renglones

    # --- SECCIÓN 1: REMITENTE (Estático) ---
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

    # --- SECCIÓN 2: PEGAR LOGO ---
    if logo:
        # Posición: Derecha, centrado verticalmente
        logo_x = W - logo.width - 50
        logo_y = (H - logo.height) // 2
        # Usar el mismo logo como máscara para transparencia
        img.paste(logo, (logo_x, logo_y), logo)

    # --- SECCIÓN 3: DESTINATARIO (Dinámico) ---
    # Añadir un doble espacio antes de esta sección
    CURRENT_Y += LINE_HEIGHT * 1.5

    # Formatear datos (Mayúsculas para que coincida)
    ciudad = datos.get('ciudad', '').upper()
    depto = datos.get('depto', '').upper()
    nombre = datos.get('nombre', '').upper()
    cc = datos.get('cc', '').upper()
    tel = datos.get('telefono', '').upper()
    dir_envio = datos.get('direccion', '').upper()

    recipient_lines = [
        f"ENVIAR A: {ciudad}.{depto}",
        f"{nombre}",
        # Usamos f-string padding (<20) para simular el espacio tabulado entre CC y CEL
        f"CC.{cc:<20} CEL: {tel}",
        f"{dir_envio}"
    ]

    for line in recipient_lines:
        draw.text((MARGIN_LEFT, CURRENT_Y), line, font=font, fill=WHITE)
        CURRENT_Y += LINE_HEIGHT

    # 4. Guardar imagen en memoria (buffer RAM)
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio