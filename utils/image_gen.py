from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- CONFIG HD ---
DPI = 300
SCALE = 300 / 144

# Tamaño tarjeta calibrada
CARD_W = int(566.63 * SCALE)
CARD_H = int(323.79 * SCALE)

MARGEN_PX = int(0.3 * 118.11)

# Coordenadas base calibradas
T1_X, T1_Y = 42 * SCALE, 750 * SCALE
T2_X, T2_Y = 42 * SCALE, 900 * SCALE   # ← Bajado a 900 definitivo

L_X, L_Y = 408 * SCALE, 834 * SCALE
L_W, L_H = 163 * SCALE, 121 * SCALE    # ← Logo nuevo tamaño

# Posición real dentro de la tarjeta
CARD_X = T1_X - MARGEN_PX
CARD_Y = T1_Y - MARGEN_PX

OFFSET_X = CARD_X
OFFSET_Y = CARD_Y


def generar_etiqueta_moto(datos, return_object=False):
    """
    Genera SOLO la tarjeta negra HD calibrada.
    """

    # Crear tarjeta negra exacta
    img = Image.new("RGB", (CARD_W, CARD_H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # --- FUENTE ---
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(base_dir, "assets", "fonts", "negrita.ttf")
        font = ImageFont.truetype(font_path, int(20 * SCALE))
    except:
        font = ImageFont.load_default()

    line_spacing = int(26 * SCALE)

    # ==================================================
    # 1️⃣ REMITENTE FIJO
    # ==================================================
    remitente = [
        "DESDE:",
        "BOGOTÁ - YANETH PLAZAS",
        "CC.1026600344 CEL: 3134553455",
        "CRA.29#3-24, VERAGUAS CP.111411",
        "YELLOWER.CO@GMAIL.COM"
    ]

    curr_x = T1_X - OFFSET_X + (5 * SCALE)
    curr_y = T1_Y - OFFSET_Y + (5 * SCALE)

    for line in remitente:
        draw.text((curr_x, curr_y), line, font=font, fill="white")
        curr_y += line_spacing


    # ==================================================
    # 2️⃣ DESTINATARIO DINÁMICO
    # ==================================================
    nombre = datos.get("nombre", "").upper()
    destino = datos.get("destino", "").upper()
    cc = datos.get("cc", "").upper()
    tel = datos.get("telefono", "").upper()
    direccion = datos.get("direccion", "").upper()
    barrio = datos.get("barrio", "").upper()

    destinatario = [
        f"ENVIAR A: {destino}",
        f"{nombre}",
        f"CC.{cc}  CEL: {tel}",
        f"{direccion}",
        f"BRR: {barrio}"
    ]

    curr_x = T2_X - OFFSET_X + (5 * SCALE)
    curr_y = T2_Y - OFFSET_Y + (5 * SCALE)

    for line in destinatario:
        draw.text((curr_x, curr_y), line, font=font, fill="white")
        curr_y += line_spacing


    # ==================================================
    # 3️⃣ LOGO HD CALIBRADO
    # ==================================================
    try:
        logo_path = os.path.join(base_dir, "assets", "images", "logo_white.png")
        logo = Image.open(logo_path).convert("RGBA")

        logo = logo.resize((int(L_W), int(L_H)), Image.Resampling.LANCZOS)

        logo_x = int(L_X - OFFSET_X)
        logo_y = int(L_Y - OFFSET_Y)

        img.paste(logo, (logo_x, logo_y), logo)
    except Exception as e:
        print("Error cargando logo:", e)

    # --- RETORNO ---
    if return_object:
        return img

    bio = io.BytesIO()
    img.save(bio, format="PNG", dpi=(DPI, DPI))
    bio.seek(0)
    return bio


# Compatibilidad con shipping.py
def generar_hoja_a4(lista_pedidos):
    if not lista_pedidos:
        return None
    return generar_etiqueta_moto(lista_pedidos[0])