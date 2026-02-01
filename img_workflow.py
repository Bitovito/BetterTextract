import os
import pprint
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from output_types import BillItems, State, ItemSuggestions
from langgraph.graph import StateGraph, START, END
from helpers import handle_file_for_llm, get_db_items

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
)

extraction_llm = llm.with_structured_output(BillItems)

comparison_llm = llm.with_structured_output(ItemSuggestions)

def extract_items(state: State):
    """Primer paso; extraer datos de insumos comprados."""
    factura_actual = handle_file_for_llm("./facturas/factura2.pdf")
    ejemplo1 = handle_file_for_llm("./facturas/factura_1.pdf")
    ejemplo2 = handle_file_for_llm("./facturas/factura_2.pdf")
    ejemplo4 = handle_file_for_llm("./facturas/factura_4.pdf")
    
    msg_for_llm = [
        # 1. CONTEXTO E INSTRUCCIONES
        SystemMessage(
            content=(
                """Eres un experto en lectura de Facturas Electrónicas chilenas. Tu tarea es extraer información de productos o servicios.

                ESTRUCTURA DE UNA FACTURA CHILENA:
                - El detalle de productos se encuentra en la sección central, entre los datos del receptor y el bloque de totales.
                - Esta sección se presenta como una tabla con filas horizontales, cada fila = un producto o servicio.
                - Solo extrae filas válidas de productos. Ignora: encabezados, subtítulos, notas, totales y resúmenes tributarios.

                EXTRACCIÓN DE CAMPOS POR FILA:
                - Nombre: Texto libre, usualmente la celda más ancha, puede ocupar varias líneas.
                - Cantidad: Valor numérico. Si no está explícito, asume 1.
                - Unidad: kg, g, l, ml, unidad, etc. Si no está clara, déjalo vacío.
                - Precio Unitario: Valor numérico alineado a la derecha.

                IMPORTANTE: No inventes información. Si algún valor no es visible con certeza, déjalo vacío o nulo.
                NOTA: En Chile, el simbolo de puntuación punto (.) se usa como separador de miles y la coma (,) como separador decimal."""
            )
        ),
        
        # 2. EJEMPLO 1 CON CONTEXTO
        HumanMessage(
            content=(
                "EJEMPLO 1 - Factura correctamente extraída:\n\n"
                "Aquí está la factura de ejemplo:"
            )
        ),
        HumanMessage(
            content=[
                {"type": "text", "text": "[INSERTAR AQUI: Primera factura de ejemplo]"},
                ejemplo1
            ]
        ),
        SystemMessage(
            content=(
                "EXTRACCIÓN ESPERADA DEL EJEMPLO 1 (4 ITEMS):\n"
                "[\n"
                "  {\"name\": \"Carga de gas 05 kg Normal\", \"quantity\": 5, \"measureUnit\": \"UN\", \"unitPrice\": 2726,00},\n"
                "  {\"name\": \"Carga de gas 11 kg Normal\", \"quantity\": 4, \"measureUnit\": \"UN\", \"unitPrice\": 4377,00},\n"
                "  {\"name\": \"Carga de gas 15 kg Normal\", \"quantity\": 30, \"measureUnit\": \"UN\", \"unitPrice\": 5745,00},\n"
                "  {\"name\": \"Carga de gas 45 kg Normal\", \"quantity\": 9, \"measureUnit\": \"UN\", \"unitPrice\": 17049,00}\n"
                "]\n"
            )
        ),
        
        # 3. EJEMPLO 2 CON CONTEXTO
        HumanMessage(
            content=(
                "EJEMPLO 2 - Otra factura correctamente extraída:\n\n"
                "Aquí está la segunda factura de ejemplo:"
            )
        ),
        HumanMessage(
            content=[
                {"type": "text", "text": "[INSERTAR AQUI: Segunda factura de ejemplo]"},
                ejemplo2
            ]
        ),
        SystemMessage(
            content=(
                "EXTRACCIÓN ESPERADA DEL EJEMPLO 2 (2 ITEMS):\n"
                "[\n"
                "  {\"name\": \"Arriendo dispensador agua fria-caliente\", \"quantity\": 6, \"measureUnit\": \"UN\", \"unitPrice\": 100},\n"
                "  {\"name\": \"Botellon 20 litros\", \"quantity\": 34, \"measureUnit\": \"UN\", \"unitPrice\": 1785},\n"
                "]\n"
            )
        ),
        
        # 4. SOLICITUD ACTUAL - LA FACTURA QUE DEBE PROCESAR
        HumanMessage(
            content=(
                "TAREA ACTUAL:\n\n"
                "Extrae los productos de la siguiente factura (esta es la factura real que debes procesar):"
            )
        ),
        HumanMessage(
            content=[
                {"type": "text", "text": "Factura a procesar:"},
                factura_actual
            ]
        ),
    ]
    msg = extraction_llm.invoke(msg_for_llm)
    return {"billItems": msg}
# También obtener la unidad de medida (unidad, kg, g, litro, etc.)

def compare_items(state: State):
    """Segundo paso; ver si hay items en la BD que tengan mismo significado semántico"""
    print("---- Estado antes de la comparación ----")
    pprint.pprint(state)
    
    if state["billItems"].message == "failure":
        return {"itemPairs": ItemSuggestions(found=False, suggestions={})}
    db_items: BillItems = get_db_items()

    msg_for_llm = [
        SystemMessage(
            content=(
                "Hablas en español. Eres un asistente que compara items extraidos de una factura de compra con items en una base de datos."
            )
        ),
        HumanMessage(
            content=(
                f"Compara los siguientes items extraidos de una factura de compra: *{state['billItems']}* "
                f"con los siguientes items en la base de datos: *{db_items}*. Devuelve una lista "
                "con los nombres de los items en la base de datos que tengan el mismo significado "
                "semántico que los items extraidos de la factura. Si no encuentras items similares, devuelve una lista vacia y un False"
            )
        )
    ]
    msg = comparison_llm.invoke(msg_for_llm)
    print("----- Mensaje post comparación ----")
    pprint.pprint(msg)
    return {"itemPairs": msg}

workflow = StateGraph(State)
workflow.add_node("extract_items", extract_items)
workflow.add_node("compare_items", compare_items)
workflow.add_edge(START, "extract_items")
workflow.add_edge("extract_items", "compare_items")
workflow.add_edge("compare_items", END)

chain = workflow.compile()

# state = chain.invoke({
#     "billItems": {
#         "message": "failure", 
#         "bitems": []
#         },
#     "dbItems": list[str],
#     "itemPairs": ItemSuggestions
#     })