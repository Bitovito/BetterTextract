import base64
import os
from io import BytesIO
from pdf2image import convert_from_path
import requests
import zipfile
from pathlib import Path

def encode_image(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == '.pdf':
        images = convert_from_path(file_path)
        if images:
            buffer = BytesIO()
            images[0].save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
        raise ValueError("PDF conversion failed.")

    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
  
def get_db_items():
  """Función dummy que simula obtener items desde una base de datos."""
  lista = [{"Name": "Arroz", "UPrice": 1500, "Quantity": 2},
            {"Name": "Fideos", "UPrice": 1200, "Quantity": 1},
            {"Name": "Carne", "UPrice": 8000, "Quantity": 1},
            {"Name": "Agua 20L", "UPrice": 2500, "Quantity": 2}]
  return {"dbItems": lista}

def handle_file_for_llm(file_path):
    """
    Prepara un archivo (imagen o PDF) para ser usado con langchain HumanMessage.
    Retorna una lista de content blocks compatible con OpenAI.
    """
    ext = os.path.splitext(file_path)[-1].lower()
    
    if ext == '.pdf':
        # Convertir PDF a imágenes y codificar en base64
        images = convert_from_path(file_path)
        if not images:
            raise ValueError(f"No se pudieron extraer imágenes del PDF: {file_path}")
        
        # Usar la primera página
        image = images[0]
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        return {
            "type": "image",
            "base64": base64_image,
            "mime_type": "image/png",
        }
    
    elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
        # Imagen - codificar en base64
        with open(file_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")
        
        # Determinar mime_type
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        return {
            "type": "image",
            "base64": base64_image,
            "mime_type": mime_type,
        }
    
    else:
        raise ValueError(f"Tipo de archivo no soportado: {ext}")