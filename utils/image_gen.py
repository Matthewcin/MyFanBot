from PIL import Image, ImageDraw, ImageFont
import io

def generar_ticket_imagen(tracking_id, cliente, producto, estado):
    """
    Genera una imagen simple con datos del envío.
    En el futuro puedes cargar una plantilla .png con Image.open()
    """
    # Crear lienzo blanco
    img = Image.new('RGB', (600, 400), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Colores
    negro = (0, 0, 0)
    azul = (0, 100, 255)
    
    # Texto (Si tienes fuentes ttf úsalas, sino default)
    try:
        fnt_titulo = ImageFont.truetype("arial.ttf", 40)
        fnt_texto = ImageFont.truetype("arial.ttf", 20)
    except:
        fnt_titulo = ImageFont.load_default()
        fnt_texto = ImageFont.load_default()
    
    d.text((50, 50), "MYFANBOX - Ticket de Envío", font=fnt_titulo, fill=azul)
    d.text((50, 120), f"Tracking ID: {tracking_id}", font=fnt_texto, fill=negro)
    d.text((50, 160), f"Cliente: {cliente}", font=fnt_texto, fill=negro)
    d.text((50, 200), f"Producto: {producto}", font=fnt_texto, fill=negro)
    d.text((50, 240), f"Estado: {estado}", font=fnt_texto, fill=negro)
    d.text((50, 300), "¡Gracias por tu compra!", font=fnt_texto, fill=azul)
    
    # Guardar en buffer
    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio