import os
import base64
from io import BytesIO
from google.cloud import storage
from pdf2image import convert_from_bytes, convert_from_path
from output_types import BillItems, ItemSuggestions, BItem

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
    
def handle_gcs_blob(blob):
    """
    Procesa un blob de Google Cloud Storage (PDF o imagen).
    Retorna un content block compatible con el workflow.
    
    Args:
        blob: objeto storage.Blob de google.cloud.storage
        
    Returns:
        dict con keys: type, base64, mime_type
        
    Raises:
        ValueError: si el tipo de archivo no es soportado o falla la conversión
    """
    # Descargar archivo en memoria
    file_bytes = blob.download_as_bytes()
    
    # Determinar extensión del archivo
    ext = os.path.splitext(blob.name)[-1].lower()
    
    if ext == '.pdf':
        # Convertir PDF a imágenes (pdf2image)
        images = convert_from_bytes(file_bytes)
        if not images:
            raise ValueError(f"No se pudieron extraer imágenes del PDF: {blob.name}")
        
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
        # Imagen directa - codificar en base64
        base64_image = base64.b64encode(file_bytes).decode("utf-8")
        
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
        raise ValueError(f"Tipo de archivo no soportado: {ext}. Usa PDF o imágenes (JPG, PNG, GIF)")

def descargar_pdf_gcs(bucket_name, blob_name):
    """
    Descarga un archivo desde GCS y lo convierte a content block.
    (Wrapper conveniente si necesitas pasar bucket_name y blob_name por separado)
    
    Args:
        bucket_name: nombre del bucket en GCS
        blob_name: ruta del archivo dentro del bucket
        
    Returns:
        dict con content block (type, base64, mime_type)
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return handle_gcs_blob(blob)
    
def format_db_items(db_items):
    """Formatea los items de la base de datos para enviarlos al LLM"""
    formatted_items = []
    for key, values in db_items.items():
        try:
            # Extraer stock actual si es un diccionario anidado
            stock = values.get("stock", 0)
            if isinstance(stock, dict):
                stock = stock.get("current", 0)
            
            formatted_items.append(BItem(
                name=values["name"],
                measureUnit=values["unit"],
                quantity=int(stock),
                unitPrice=float(values["unitPrice"])
            ))
        except KeyError as e:
            print(f"Error al formatear item {key}: falta la clave {e}")
            continue
    
    return formatted_items