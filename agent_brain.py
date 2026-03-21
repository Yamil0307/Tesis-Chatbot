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

    # Prompt para reescritura - más agresivo con contexto
    history_str = "\n".join([f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content}" for m in chat_history[-4:]])
    
    prompt_rewrite = f"""
    Eres una herramienta de reformulación de búsqueda para documentos académicos.
    Tu trabajo es reescribir la "PREGUNTA ACTUAL" para que sea totalmente independiente y específica, basándote en el HISTORIAL.
    
    INSTRUCCIONES ESPECIALES:
    - Si la pregunta menciona "tutores", "directores" o "autores", asegúrate de incluir el nombre del documento o persona del contexto.
    - Haz la pregunta lo más específica y clara posible para una búsqueda en base de datos.
    - Evita palabras vagas como "esto", "eso", "ella", "él".
    
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
    
    # K=40: Aumentamos para asegurar que capturamos portadas completas
    # especialmente cuando buscamos información formal como "tutores"
    print(f"🚀 Buscando '{query_to_search}' con K=40...")
    docs = rag_mgr.search(query_to_search, k=40)
    
    if not docs:
        context = "[SIN RESULTADOS]"
    else:
        # --- TRUCO MAESTRO: ORDENAR Y FILTRAR POR PÁGINA ---
        # 1. Ordenamos por página para que páginas 1-5 aparezcan primero
        # 2. Priorizamos fuertemente las primeras páginas (donde está la portada)
        docs.sort(key=lambda x: x.metadata.get('page', 999))
        
        # Separamos documentos de portada (pág 1-5) y otros
        portada_docs = [d for d in docs if d.metadata.get('page', 999) <= 5]
        otros_docs = [d for d in docs if d.metadata.get('page', 999) > 5]
        
        # Reconstruimos con portada al frente, pero limitando para no saturar
        docs_ordenados = portada_docs[:15] + otros_docs[:15]
        
        context_text = rag_mgr.format_context(docs_ordenados)
        sources_list = MetadataHandler.format_source_list(docs_ordenados)
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

    # PROMPT FUSIONADO: Instrucciones de portadas + formato académico de fuentes
    system_prompt = f"""
Eres un ESPECIALISTA EN INFORMACIÓN HISTÓRICA DE LA UNIVERSIDAD DE ORIENTE. Tu única fuente de verdad es el CONTEXTO proporcionado de libros y documentos históricos de la UO.

OBJETIVO PRINCIPAL:
Responde consultas sobre información histórica, académica y administrativa de la Universidad de Oriente basándote EXCLUSIVAMENTE en los documentos proporcionados.

INSTRUCCIONES CRÍTICAS PARA BÚSQUEDA EN PORTADAS:
**LAS PORTADAS SON LA FUENTE PRIMARIA.** Busca PRIMERO en fragmentos de páginas 1-5 (normalmente marcadas como "Pág 1", "Pág 2", etc.)

INFORMACIÓN EN PORTADAS TÍPICAMENTE INCLUYE:
- Título de la tesis/documento
- Autor(es) - busca palabras: "por", "autor", "presentado por"
- Tutores/Directores - busca palabras: "Tutor:", "Tutores:", "Director:", "Dirigida por", "Bajo la dirección de"
- Institución: Universidad de Oriente
- Departamento/Facultad
- Año académico

ESTRATEGIA DE BÚSQUEDA:
1. **ESCANEA PRIMERO PÁGINAS 1-5:** Son los fragmentos más importantes. La información que busques DEBE estar aquí.
2. **RECONOCE FORMATOS TÍPICOS:** En portadas formales la información suele estar:
   - Centro de la página
   - Con títulos en mayúsculas o negrita
   - En secciones claramente identificadas
3. **FILTRA SECCIONES NO FORMALES:** Ignora "Agradecimientos", "Dedicatoria", opiniones personales, anécdotas.
4. **SI NO ESTÁ EN PORTADA, NO EXISTE:** Si la información que busca no aparece en fragmentos de pág 1-5, entonces no se encuentra en los documentos.

INSTRUCCIONES CRÍTICAS DE CITACIÓN:
- Si la respuesta se basa en fragmentos de los documentos, AL FINAL de tu respuesta, incluye SIEMPRE la sección:
### FUENTES CONSULTADAS:
- Para cada fuente, usa el formato:
- [Nombre del Archivo] (página X): "Fragmento del texto...".
- Si hay varias fuentes, haces lo mismo: [Nombre del Archivo] (página X): "Fragmento del texto...".
- No inventes fuentes ni fragmentos. Si no hay fuentes, escribe: "No se encontraron fuentes relevantes en los documentos consultados."
- Prohibido el uso de corchetes numéricos [1], [2], etc.

REGLAS PARA RESPUESTAS:
- Responde SOLO con información exacta encontrada en el contexto, especialmente en portadas.
- Si encuentras datos en múltiples lugares, prefiere la información de la portada/primeras páginas.
- Si la información NO está disponible, responde: "Esta información no se encuentra disponible en los documentos de la Universidad de Oriente proporcionados."
- NUNCA hagas suposiciones, inferencias o uses conocimiento externo.
- Mantén respuestas directas, breves y verificables.

CONTEXTO (DOCUMENTOS DE LA UNIVERSIDAD DE ORIENTE, PRIORIZADOS POR PÁGINA):
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

    # --- AGREGAR SIEMPRE FUENTES AL FINAL DE LA RESPUESTA ---
    # Extraer sección de fuentes del contexto (si existe)
    fuentes = None
    if context and "FUENTES CONSULTADAS:" in context:
        partes = context.split("FUENTES CONSULTADAS:", 1)
        fuentes = "FUENTES CONSULTADAS:" + partes[1].strip()
    # Evitar duplicar si el modelo ya las incluyó
    if fuentes and "FUENTES CONSULTADAS:" not in response_content:
        response_content = f"{response_content}\n\n{fuentes}"

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

