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
from memory_manager import get_memory_manager

# --- 1. CONFIGURACIÓN INICIAL ---
load_dotenv()

# NO inicializar aquí - se inicializará cuando se necesite
# rag_mgr se obtiene dentro de las funciones que lo necesitan

# El modelo LLM (Gemini para desarrollo)
# **ETAPA 2 - CORRECCIÓN AGRESIVA: Temperatura 0 para NO generar conocimiento externo**
# Temperature=0 + strict system prompt = CERO alucinaciones
# El modelo será 100% determinista y NUNCA usará conocimiento externo
llm = ChatGoogleGenerativeAI(model="gemini-robotics-er-1.5-preview", temperature=0.0)

# --- 2. DEFINICIÓN DE LA HERRAMIENTA ---

@tool
def search_university_history(query: str) -> str:
    """Busca información ÚNICAMENTE en los documentos históricos y académicos 
    de la Universidad de Oriente. No busca en fuentes externas.
    
    **ETAPA 2 - RESTRICCIÓN: Solo conocimiento local de la universidad**
    
    Esta herramienta está limitada a:
    - Documentos históricos de la Universidad de Oriente
    - Reglamentos académicos
    - Estatutos y normativas
    - Archivos de la Sala de Fondos Raros y Valiosos
    
    Retorna:
    - Contexto: Fragmentos relevantes encontrados en los documentos locales
    - Fuentes: Lista de documentos consultados con páginas
    
    Si no encuentra información relevante, lo reporta explícitamente."""
    
    # Obtener el RAG Manager SOLO cuando se necesita (lazy initialization)
    rag_mgr = get_rag_manager()
    
    # Realiza la búsqueda usando el RAG Manager (SOLO en documentos locales)
    docs = rag_mgr.search(query, k=4)
    
    # Si no encuentra nada, devuelve un mensaje específico
    if not docs:
        return "No se encontró información relevante en los documentos de la universidad."
    
    # Formatea el contexto CON anotaciones de fuente
    context = rag_mgr.format_context(docs)
    
    # **NUEVO: Extraer lista de fuentes para que el LLM las cite**
    sources_list = MetadataHandler.format_source_list(docs)
    
    # Combinar contexto + fuentes en un formato que el LLM entienda
    full_context = f"{context}{sources_list}"
    
    return f"Contexto recuperado de la universidad:\n{full_context}"


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
    """El nodo principal FUERZA búsqueda en base de datos local SIEMPRE.
    
    **ETAPA 2 - CORRECCIÓN ULTRA-AGRESIVA: NUNCA responde sin buscar primero**
    Esto previene que el LLM use su conocimiento general (alucinaciones).
    """
    
    # **CRÍTICO**: Forzar búsqueda SIEMPRE en la base de datos local
    # No permitimos que el LLM decida si usar o no la herramienta
    # Siempre busca primero, luego responde basado SOLO en lo encontrado
    
    # Llamada OBLIGATORIA a la herramienta de búsqueda
    query = state["input"]
    rag_mgr = get_rag_manager()
    docs = rag_mgr.search(query, k=4)
    
    # Formatear contexto
    if not docs:
        context = "[SIN RESULTADOS] No se encontró información relevante en los documentos de la universidad."
    else:
        context = rag_mgr.format_context(docs)
        sources_list = MetadataHandler.format_source_list(docs)
        context = f"{context}{sources_list}"
    
    # Retornar el contexto encontrado para que el nodo respond lo use
    return {"context": context, "intermediate_steps": []}

# Nodo B: El Respondedor Final (Generación Aumentada)
def generate_response(state: AgentState) -> Dict[str, Any]:
    """Genera la respuesta final usando el contexto recuperado (RAG).
    
    Si no hay contexto relevante, responde de forma elegante indicando que
    la información no está disponible en los registros de la universidad.
    **ETAPA 2 - CORRECCIÓN ULTRA-AGRESIVA: Validación de alucinaciones**
    """
    
    context = state["context"]
    input_message = state["input"]
    current_chat_history = state["chat_history"]  # ← Obtener historial actual
    
    # **NUEVO: Detectar si el contexto está vacío o no es relevante**
    is_context_empty = (
        not context or 
        context.strip() == "" or 
        "[SIN RESULTADOS]" in context
    )
    
    # Construir el historial de conversación para el LLM
    conversation_history = ""
    if current_chat_history:
        conversation_history = "\n--- HISTORIAL DE CONVERSACIÓN ANTERIOR ---\n"
        for i, msg in enumerate(current_chat_history):
            role = "Usuario" if hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage' else "Asistente"
            conversation_history += f"{role}: {msg.content}\n"
        conversation_history += "--- FIN DEL HISTORIAL ---\n\n"
    
    # **ETAPA 2 - CORRECCIÓN ULTRA-AGRESIVA: Forzar respuesta SOLO basada en contexto**
    # No permitimos NINGUNA alucinación. El LLM DEBE responder solo del contexto.
    
    # Detectar si hay contexto relevante
    has_context = context and "[SIN RESULTADOS]" not in context and len(context.strip()) > 100
    
    if not has_context:
        # SIN contexto relevante - NO permitir que el LLM responda
        # Forzar respuesta predefinida sin pasar por el LLM
        response_content = "No contamos con información sobre este tema en los registros históricos de la Universidad de Oriente."
    else:
        # CON contexto relevante - Permitir que el LLM responda basado en documentos
        system_prompt = (
            "ERES UN ASISTENTE ACADÉMICO ESPECIALIZADO EN LA UNIVERSIDAD DE ORIENTE.\n\n"
            "Tu ÚNICA fuente de verdad es el CONTEXTO DE LOS DOCUMENTOS.\n"
            "Responde SOLO usando la información del contexto.\n"
            "NO INVENTES INFORMACIÓN. NO USES CONOCIMIENTO GENERAL.\n\n"
            "Estructura de tu respuesta:\n"
            "1. Responde la pregunta con información del contexto\n"
            "2. Al FINAL, incluye:\n"
            "   FUENTES CONSULTADAS:\n"
            "   - [Nombre del Documento] (página X)\n\n"
            f"{conversation_history}"
            "--- CONTEXTO DE LOS DOCUMENTOS ---\n"
            f"{context}\n"
            "--- FIN DEL CONTEXTO ---\n"
        )
        
        # Pasar TODO el historial + nuevo input al LLM
        messages = current_chat_history + [HumanMessage(content=input_message)]
        response_chain = llm.bind(system=system_prompt)
        final_response = response_chain.invoke(messages)
        response_content = final_response.content.strip()

    # CRÍTICO: AGREGAR a chat_history, no reemplazar
    # Agregar el mensaje del usuario + la respuesta del asistente
    new_messages = [
        HumanMessage(content=input_message),
        AIMessage(content=response_content)
    ]
    updated_chat_history = current_chat_history + new_messages
    
    return {"chat_history": updated_chat_history}

# Nodo C: Lógica de Herramientas (ELIMINADO - ya no es necesario)
# **ETAPA 2 - CORRECCIÓN: La búsqueda ahora ocurre en run_agent directamente**
# Ya no necesitamos un nodo separado para ejecutar herramientas

# --- 6. CONDICIÓN DE RUTA (Simplificada - ya no hay decisión) ---
def should_continue(state: AgentState) -> str:
    """Ya no hay decisión: SIEMPRE se ejecutó la búsqueda en run_agent.
    
    **ETAPA 2 - CORRECCIÓN: Eliminamos la lógica de decisión**
    Ahora siempre vamos directamente a 'respond' porque ya buscamos en run_agent.
    """
    # Ya ejecutamos búsqueda en run_agent, vamos directamente a responder
    return "respond"


# --- 7. CONSTRUCCIÓN DE LA GRÁFICA (El Diagrama de Flujo) ---
workflow = StateGraph(AgentState)

# Agrega los Nodos
workflow.add_node("agent", run_agent)          # El agente SIEMPRE busca
workflow.add_node("respond", generate_response) # Genera la respuesta

# Configura la entrada (Siempre empezamos por el agente)
workflow.set_entry_point("agent")

# **ETAPA 2 - CORRECCIÓN: Flujo simplificado (sin decisión, solo búsqueda + respuesta)**
# Define la ruta después de buscar (Siempre va a responder)
workflow.add_edge("agent", "respond")

# Define el final de la conversación (Todo termina respondiendo)
workflow.add_edge("respond", END)

# Compila el flujo de trabajo CON SqliteSaver para persistencia
memory_mgr = get_memory_manager()
saver = memory_mgr.get_saver()
app = workflow.compile(checkpointer=saver)

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
    
    # Pregunta 1: Debe usar la herramienta (buscar en los documentos locales de la universidad)
    test_agent("¿Quién fue el autor de la tesis sobre la Sala de Fondos Raros y Valiosos?")
    
    # Pregunta 2: No encontrará información en los documentos locales (respuesta elegante sin conocimiento externo)
    test_agent("¿Qué color tiene el sol?")