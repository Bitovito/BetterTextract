import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from output_types import BillItems, State, ItemSuggestions
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
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
    factura = handle_file_for_llm("./facturas/factura2.pdf")
    msg_for_llm = [
        SystemMessage(
            content=(
                "Hablas en español. Eres un asistente que lee facturas de compra en formato de Chile. "
                "Extrae los productos a los que hace referencia esta factura de compra, especificamente el nombre, "
                "la cantidad del producto, su unidad de medida y su precio. El archivo está adjunto."
            )
        ),
        HumanMessage(content=factura if isinstance(factura, str) else "Archivo PDF adjunto.")
    ]
    msg = extraction_llm.invoke(msg_for_llm)
    print(msg.bitems)
    return {"billItems": msg.bitems}
# También obtener la unidad de medida (unidad, kg, g, litro, etc.)

def compare_items(state: State):
    """Segundo paso; ver si hay items en la BD que tengan mismo significado semántico"""
    db_items: BillItems = get_db_items()

    msg_for_llm = [
        SystemMessage(
            content=(
                "Hablas en español. Eres un asistente que compara items extraidos de una factura de compra con items en una base de datos."
            )
        ),
        HumanMessage(
            content=(
                f"Compara los siguientes items extraidos de una factura de compra: {state['billItems']} "
                f"con los siguientes items en la base de datos: {db_items}. Devuelve una lista "
                "con los nombres de los items en la base de datos que tengan el mismo significado "
                "semántico que los items extraidos de la factura. Si no encuentras items similares, devuelve una lista vacia y un False"
            )
        )
    ]
    msg = comparison_llm.invoke(msg_for_llm)
    print(msg)
    return {"itemPairs": msg}

workflow = StateGraph(State)
workflow.add_node("extract_items", extract_items)
workflow.add_node("compare_items", compare_items)
workflow.add_edge(START, "extract_items")
workflow.add_edge("extract_items", "compare_items")
workflow.add_edge("compare_items", END)

chain = workflow.compile()

display(Image(chain.get_graph().draw_mermaid_png()))

state = chain.invoke({})