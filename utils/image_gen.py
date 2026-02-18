from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
# Asegúrate de tener la fuente negrita.ttf en utils/assets/fonts/
FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'negrita.ttf') 
# Asegúrate de tener el logo_white.png en utils/assets/images/
LOGO_PATH = os.path.join(ASSETS_DIR, 'images', 'logo_white.png')

def generar_etiqueta_moto(datos):
    """
    Genera la etiqueta negra con medidas exactas: 10cm x 5.7cm (a 300 DPI).
    Resolución resultante: 1181 x 673 px (Máxima Calidad).
    """
    # 1. Dimensiones Exactas (300 DPI)
    W, H = 1181, 673
    img = Image.new('RGB', (W, H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 2. Configuración de Fuente
    WHITE = (255, 255, 255)
    # Tamaño de fuente exacto solicitado por el usuario
    FONT_SIZE = 10.1 
    # Reducimos el interlineado proporcionalmente al nuevo tamaño de fuente
    LINE_HEIGHT = int(FONT_SIZE * 1.5) 

    try:
        # Pillow acepta float para el tamaño desde versiones recientes
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except OSError:
        print("⚠️ Error cargando fuente, usando default.")
        font = ImageFont.load_default()
    except Exception as e:
        print(f"⚠️ Error inesperado con la fuente: {e}, usando default.")
        font = ImageFont.load_default()


    # 3. Cargar y Ajustar Logo (Se mantiene grande a la derecha)
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        # El logo ocupará el 65% de la altura de la tarjeta
        target_h = int(H * 0.65) 
        aspect_ratio = logo.width / logo.height
        target_w = int(target_h * aspect_ratio)
        
        # Usamos LANCZOS para el redimensionado de mayor calidad
        logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Posición: Centrado verticalmente, pegado a la derecha con margen
        logo_x = W - target_w - 50 
        logo_y = (H - target_h) // 2
        
        img.paste(logo, (logo_x, logo_y), logo)
    except Exception as e:
         print(f"⚠️ No se pudo cargar el logo: {e}")

    # 4. Dibujar Texto
    MARGIN_LEFT = 50
    CURRENT_Y = 50    # Margen superior inicial

    # --- SECCIÓN REMITENTE (Datos Fijos) ---
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

    # --- ESPACIO DIVISOR ---
    # Ajustamos el espacio proporcionalmente
    CURRENT_Y += LINE_HEIGHT * 2

    # --- SECCIÓN DESTINATARIO (Datos Dinámicos) ---
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

    # 5. Exportar en PNG (Formato sin pérdida de máxima calidad)
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio