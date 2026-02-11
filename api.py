import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from helpers import format_db_items
from img_workflow import chain
from output_types import ItemSuggestions, ContentBlock

app = FastAPI(title="BetterTextract API", version="1.0.0")


class FacturaRequest(BaseModel):
    """Modelo para la solicitud del endpoint"""
    content_block: ContentBlock
    db_items: dict


class FacturaResponse(BaseModel):
    """Modelo para la respuesta del endpoint"""
    success: bool
    message: str
    data: dict


@app.post("/extract", response_model=FacturaResponse)
async def extract_factura(request: FacturaRequest):
    """
    Endpoint para extraer datos de una factura.
    
    Args:
        request: Contiene el content block de la factura
    
    Returns:
        FacturaResponse con el estado del workflow
    """
    try:
        # Validar que el content_block no esté vacío
        if not request.content_block.base64 or not request.content_block.base64.strip():
            raise ValueError("El content block no puede estar vacío")
        
        # Ejecutar el workflow en un thread pool para no bloquear
        loop = asyncio.get_event_loop()
        state = await loop.run_in_executor(
            None,
            lambda: chain.invoke({
                "factura": request.content_block.model_dump(),
                "billItems": {
                    "message": "failure", 
                    "bitems": []
                },
                "dbItems": format_db_items(request.db_items),
                "itemPairs": ItemSuggestions(found=False, suggestions={})
                })
        )
        
        return FacturaResponse(
            success=True,
            message="Extracción completada exitosamente",
            data=state
        )
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Archivo no encontrado: {request.content_block.base64[:30]}..."  # Mostrar solo los primeros caracteres para no saturar el mensaje
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error de validación: {str(e)}"
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()  # Imprime el traceback completo
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la factura: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Endpoint para verificar que el servidor está activo"""
    return {"status": "ok", "message": "BetterTextract API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
