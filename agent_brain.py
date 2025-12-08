import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

# --- IMPORTAR GESTORES CENTRALIZADOS ---
from rag_manager import get_rag_manager
from metadata_handler import MetadataHandler

# --- 1. CONFIGURACIÓN INICIAL ---
load_dotenv()

# NO inicializar aquí - se inicializará cuando se necesite
# rag_mgr se obtiene dentro de las funciones que lo necesitan

# El modelo LLM (Gemini para desarrollo)
# Usaremos el modelo que ya probaste con éxito: gemini-2.0-flash
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5)

# --- 2. DEFINICIÓN DE LA HERRAMIENTA ---

@tool
def search_university_history(query: str) -> str:
    """Busca y recupera información relevante sobre la Universidad de Oriente, su historia, 
    reglamentos o documentos académicos de la Sala de Fondos Raros y Valiosos.
    Úsala solo si necesitas información factual o histórica."""
    
    # Obtener el RAG Manager SOLO cuando se necesita (lazy initialization)
    rag_mgr = get_rag_manager()
    
    # Realiza la búsqueda usando el RAG Manager
    docs = rag_mgr.search(query, k=4)
    
    # Formatea el contexto
    context = rag_mgr.format_context(docs)
    
    # Si no encuentra nada, devuelve un mensaje específico
    if not context:
        return "No se encontró información relevante en los documentos de la universidad."
        
    return f"Contexto recuperado de la universidad: {context}"

# Agrupamos todas las herramientas disponibles (solo tenemos una por ahora)
tools = [search_university_history]

# --- 3. DEFINICIÓN DEL ESTADO DEL AGENTE (LangGraph) ---
class AgentState(TypedDict):
    """Representa el estado de la conversación para LangGraph."""
    input: str 
    chat_history: List[Any]
    intermediate_steps: List[Any]
    context: str # <--- Dejamos 'context' como parte del estado.

# --- 4. DEFINICIÓN DE LOS NODOS DE LA GRÁFICA (Los cerebros) ---

# Nodo A: El Agente principal (pensar y decidir)
def run_agent(state: AgentState) -> Dict[str, Any]:
    """El nodo principal donde el agente decide si usar una herramienta o responder."""
    
    # 1. Creamos la cadena de agente con las herramientas disponibles
    agent_chain = llm.bind_tools(tools)
    
    # 2. Obtenemos solo el último mensaje del usuario para la decisión
    last_message = state["input"]
    
    # 3. El LLM decide si llamar a la herramienta o responder directamente
    response = agent_chain.invoke(last_message)
    
    # 4. El resultado del LLM es un objeto AIMessage con o sin llamadas a herramientas
    # Lo ponemos en intermediate_steps para el siguiente nodo (should_continue)
    return {"intermediate_steps": [response]}

# Nodo B: El Respondedor Final (Generación Aumentada)
def generate_response(state: AgentState) -> Dict[str, Any]:
    """Genera la respuesta final usando el contexto recuperado (RAG) o sin él."""
    
    context = state["context"]
    input_message = state["input"]
    
    # Definimos la instrucción final para la respuesta
    system_prompt = (
        "Eres un chatbot experto en la historia y reglamentos de la Universidad de Oriente (Santiago de Cuba). "
        "Tu misión es responder las preguntas del usuario de forma precisa y profesional. "
        "Utiliza EXCLUSIVAMENTE el siguiente contexto recuperado de los documentos de la universidad (si existe) para formular tu respuesta. "
        "Si el contexto está vacío o no es relevante, responde de forma educada que no tienes la información disponible en tu base de datos."
        "\n\n--- CONTEXTO DE LOS DOCUMENTOS ---"
        f"\n{context}"
    )

    # Creamos la cadena final: Instrucción + Pregunta
    response_chain = llm.bind(system=system_prompt)
    final_response = response_chain.invoke([HumanMessage(content=input_message)])

    return {"chat_history": [AIMessage(content=final_response.content)]}

# Nodo C: Lógica de Herramientas (El Despachador)
def execute_tool(state: AgentState) -> Dict[str, Any]:
    """Ejecuta la herramienta llamada por el agente."""
    
    # El resultado del agente es un AIMessage.
    tool_calls = state["intermediate_steps"][0].tool_calls
    
    # Asumimos una sola llamada a herramienta por simplicidad
    tool_call = tool_calls[0]
    
    # El argumento 'query' está en tool_call.args
    tool_input = tool_call["args"]["query"]
    
    # --- CORRECCIÓN CLAVE ---
    # La variable 'search_university_history' es un objeto StructuredTool.
    # Se debe invocar con su método .invoke(), pasándole un diccionario con el argumento esperado.
    tool_output = search_university_history.invoke({"query": tool_input}) # <-- CORREGIDO
    
    # Retorna el contexto recuperado para el siguiente paso (generate_response)
    return {"context": tool_output}

# --- 6. CONDICIÓN DE RUTA (El Decision Maker) ---
def should_continue(state: AgentState) -> str:
    """Decide si el agente debe usar la herramienta o responder directamente."""
    
    # El resultado del nodo 'run_agent' es un AIMessage
    last_message = state["intermediate_steps"][0]
    
    # Verificamos si el mensaje contiene llamadas a herramientas (tool_calls)
    if last_message.tool_calls:
        # El agente decidió usar la herramienta (ir al nodo execute_tool)
        return "call_tool"
    else:
        # El agente decidió responder directamente (ir al nodo respond)
        return "respond"


# --- 7. CONSTRUCCIÓN DE LA GRÁFICA (El Diagrama de Flujo) ---
workflow = StateGraph(AgentState)

# Agrega los Nodos
workflow.add_node("agent", run_agent)          # El agente decide
workflow.add_node("call_tool", execute_tool)    # Ejecuta la búsqueda
workflow.add_node("respond", generate_response) # Genera la respuesta

# Configura la entrada (Siempre empezamos por el agente)
workflow.set_entry_point("agent")

# Define las Rutas Condicionales (El agente decide el camino)
workflow.add_conditional_edges(
    "agent",       # Desde el nodo 'agent'
    should_continue, # Ejecuta la función de decisión
    {
        "call_tool": "call_tool",  # Si debe buscar, va al nodo 'call_tool'
        "respond": "respond"       # Si debe responder, va al nodo 'respond'
    }
)

# Define la ruta después de buscar (Siempre va a responder)
workflow.add_edge("call_tool", "respond")

# Define el final de la conversación (Todo termina respondiendo)
workflow.add_edge("respond", END)

# Compila el flujo de trabajo
app = workflow.compile()

# --- 8. FUNCIÓN DE PRUEBA ---

# --- 8. FUNCIÓN DE PRUEBA ---

def test_agent(prompt: str):
    """Función simple para interactuar con el agente en consola."""
    print(f"\n🙋‍♂️ Usuario: {prompt}")
    
    # El estado inicial debe incluir 'context' para evitar el KeyError
    initial_state = {
        "input": prompt, 
        "chat_history": [],
        "context": "" # <--- ¡AQUÍ ESTÁ LA SOLUCIÓN CLAVE!
    }
    
    # Invoca el agente y recorre todos los nodos
    final_state = app.invoke(initial_state)
    
    # Imprime la respuesta final
    print(f"🤖 Agente: {final_state['chat_history'][-1].content}")
    print("-" * 50)


# --- 9. EJECUCIÓN ---

if __name__ == "__main__":
    
    # Pregunta 1: Debe usar la herramienta (buscar en el PDF)
    test_agent("¿Quién fue el autor de la tesis sobre la Sala de Fondos Raros y Valiosos?")
    
    # Pregunta 2: NO debe usar la herramienta (respuesta de conocimiento general)
    test_agent("¿Qué color tiene el sol?")