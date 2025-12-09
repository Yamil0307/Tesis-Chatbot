import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

# --- IMPORTAR GESTORES ---
from rag_manager import get_rag_manager
from metadata_handler import MetadataHandler
from memory_manager import get_memory_manager

load_dotenv()

# --- CONFIGURACIÓN DEL MODELO ---
# Usamos gemma-3-4b-it como solicitaste.
# Temperature = 0.0 para máxima precisión y menos inventos.
llm = ChatGoogleGenerativeAI(
    model="gemma-3-4b-it", 
    temperature=0.0,
    max_output_tokens=1024
)

# --- ESTADO DEL AGENTE ---
class AgentState(TypedDict):
    input: str 
    chat_history: List[Any]
    context: str 
    search_query: str 

# --- NODOS DEL GRAFO ---

# NODO 1: Contextualizador (Reescribir la pregunta)
def contextualize_query(state: AgentState) -> Dict[str, Any]:
    """
    Reescribe la consulta del usuario si depende del historial.
    Ej: "¿Quiénes son sus tutores?" -> "¿Quiénes son los tutores de David Torres?"
    """
    user_input = state["input"]
    chat_history = state["chat_history"]

    if not chat_history:
        return {"search_query": user_input}

    # Prompt para reescritura
    history_str = "\n".join([f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content}" for m in chat_history[-4:]])
    
    prompt_rewrite = f"""
    Eres una herramienta de reformulación de búsqueda.
    Tu trabajo es reescribir la "PREGUNTA ACTUAL" para que sea totalmente independiente, basándote en el HISTORIAL.
    
    HISTORIAL:
    {history_str}
    
    PREGUNTA ACTUAL:
    {user_input}
    
    PREGUNTA REESCRITA (Solo el texto):
    """
    
    try:
        response = llm.invoke(prompt_rewrite)
        rewritten_query = response.content.strip()
        print(f"🔄 [REWRITE] '{user_input}' -> '{rewritten_query}'")
        return {"search_query": rewritten_query}
    except Exception:
        return {"search_query": user_input}


# NODO 2: Recuperador (Búsqueda + Ordenamiento por Página)
def run_agent(state: AgentState) -> Dict[str, Any]:
    """Busca en la BD y ordena por número de página para priorizar portadas."""
    query_to_search = state.get("search_query", state["input"])
    rag_mgr = get_rag_manager()
    
    # K=25: Suficiente para capturar portada y contenido, sin saturar a Gemma 4B
    print(f"🚀 Buscando '{query_to_search}' con K=25...")
    docs = rag_mgr.search(query_to_search, k=25)
    
    if not docs:
        context = "[SIN RESULTADOS]"
    else:
        # --- TRUCO MAESTRO: ORDENAR POR PÁGINA ---
        # Ordenamos los documentos para que la Página 1, 2, 3 aparezcan PRIMERO.
        # Esto ayuda al modelo a ver los "Datos Formales" antes que los "Agradecimientos".
        docs.sort(key=lambda x: x.metadata.get('page', 999))
        
        context_text = rag_mgr.format_context(docs)
        sources_list = MetadataHandler.format_source_list(docs)
        context = f"{context_text}\n\n{sources_list}"
    
    return {"context": context}


# NODO 3: Generador (Auditor Estricto)
def generate_response(state: AgentState) -> Dict[str, Any]:
    context = state["context"]
    input_message = state["input"] # Usamos la original para responder
    current_chat_history = state["chat_history"]
    
    if context == "[SIN RESULTADOS]":
        return {
            "chat_history": current_chat_history + [
                HumanMessage(content=input_message),
                AIMessage(content="La información solicitada no se encuentra en los documentos proporcionados.")
            ]
        }

    # PROMPT DISEÑADO PARA GEMMA Y DATOS ACADÉMICOS
    system_prompt = f"""
    Eres un AUDITOR DE DOCUMENTOS ACADÉMICOS. Tu única fuente de verdad es el CONTEXTO proporcionado.
    
    INSTRUCCIONES CRÍTICAS SOBRE "TUTORES" Y "AUTORES":
    1. **LA PORTADA MANDA:** Busca nombres de Tutores, Autores o Títulos SIEMPRE en los fragmentos de las primeras páginas (Pág 1, 2).
    2. **IGNORA AGRADECIMIENTOS:** Es muy común que en la sección "Agradecimientos" o "Dedicatoria" se mencione a profesores. **ESO NO SON LOS TUTORES OFICIALES**. Ignora cualquier nombre que aparezca bajo "Agradezco a...", "Dedicado a...".
    3. **BUSCA ETIQUETAS:** Busca explícitamente las palabras "Tutor:", "Tutores:", "Director:", "Trabajo de Diploma", "Autor:".
    
    REGLAS GENERALES:
    - Si no encuentras el dato exacto, di "No se especifica en el documento".
    - No uses conocimiento externo.
    - Cita el fragmento donde encontraste el dato (Ej: [1]).
    
    CONTEXTO (ORDENADO POR PÁGINA):
    {context}
    
    PREGUNTA:
    {input_message}
    
    RESPUESTA:
    """
    
    try:
        response = llm.invoke(system_prompt)
        response_content = response.content.strip()
    except Exception as e:
        response_content = "Lo siento, hubo un error al procesar la respuesta."

    new_messages = [
        HumanMessage(content=input_message),
        AIMessage(content=response_content)
    ]
    
    return {"chat_history": current_chat_history + new_messages}


# --- FLUJO DE TRABAJO (LangGraph) ---
workflow = StateGraph(AgentState)

workflow.add_node("contextualize", contextualize_query)
workflow.add_node("search", run_agent)
workflow.add_node("respond", generate_response)

workflow.set_entry_point("contextualize")
workflow.add_edge("contextualize", "search")
workflow.add_edge("search", "respond")
workflow.add_edge("respond", END)

memory_mgr = get_memory_manager()
saver = memory_mgr.get_saver()
app = workflow.compile(checkpointer=saver)

# --- PRUEBA LOCAL ---
if __name__ == "__main__":
    print("🤖 Agente Gemma-3-4b Iniciado. Probando flujo...")
    
    # Configuración de memoria
    config = {"configurable": {"thread_id": "prueba_gemma_v1"}}
    
    # 1. Pregunta de contexto
    msg1 = "¿De qué trata la tesis de David Torres?"
    print(f"\nUsuario: {msg1}")
    res1 = app.invoke({"input": msg1, "chat_history": [], "context": ""}, config=config)
    print(f"Agente: {res1['chat_history'][-1].content}")
    
    # 2. Pregunta de seguimiento (El problema de los tutores)
    msg2 = "¿Quiénes son sus tutores?"
    print(f"\nUsuario: {msg2}")
    # Pasamos el historial previo
    res2 = app.invoke({"input": msg2, "chat_history": res1['chat_history'], "context": ""}, config=config)
    print(f"Agente: {res2['chat_history'][-1].content}")