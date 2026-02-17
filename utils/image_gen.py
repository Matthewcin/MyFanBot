from PIL import Image, ImageDraw, ImageFont
import io

def generar_ticket_imagen(tracking_id, cliente, producto, estado):
    # Lienzo
    img = Image.new('RGB', (600, 300), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Texto básico (Render no tiene fuentes custom por defecto)
    d.text((20, 20), "MYFANBOX - TICKET DE ENVIO", fill=(0, 0, 0))
    d.text((20, 60), f"ID RASTREO: {tracking_id}", fill=(0, 0, 0))
    d.text((20, 100), f"Cliente: {cliente}", fill=(0, 0, 0))
    d.text((20, 140), f"Producto: {producto}", fill=(0, 0, 0))
    d.text((20, 180), f"Estado: {estado}", fill=(0, 0, 255))
    d.text((20, 250), "Entregar con cuidado.", fill=(100, 100, 100))
    
    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio