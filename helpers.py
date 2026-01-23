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
            {"Name": "Carne", "UPrice": 8000, "Quantity": 1}]
  return {"dbItems": lista}

def handle_file_for_llm(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == '.pdf':
        with open(file_path, "rb") as f:
            return f.read()  # Return raw PDF bytes for LLM
    else:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")  # Return base64 for images