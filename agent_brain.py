import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

# --- IMPORTAR GESTORES ---
from rag_manager import get_rag_manager
from metadata_handler import MetadataHandler
from memory_manager import get_memory_manager

load_dotenv()

# --- CONFIGURACIÓN DEL MODELO ---
# Usamos gemma-4-31b-it.
# Temperature = 0.0 para máxima precisión y menos alucinaciones.
llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it", 
    temperature=0.0,
    max_output_tokens=1024
)

# --- ESTADO DEL AGENTE ---
class AgentState(TypedDict):
    input: str 
    chat_history: List[Any]
    context: str 
    search_query: str 
    thread_id: str 
    query_id: Optional[str]

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
    
    # K=8: Reducido para evitar ruido y mezcla de contextos
    # Con chunk_size=300, menos documentos son suficientes para buena precisión
    print(f"🚀 Buscando '{query_to_search}' con K=8...")
    docs = rag_mgr.search(query_to_search, k=8)
    
    if not docs:
        context = "[SIN RESULTADOS]"
    else:
        # Sin ordenamiento por página - usamos los 8 documentos tal cual vienen del retrieval
        # Para registros administrativos no aplica la lógica de "portadas"
        docs_ordenados = docs[:8]
        
        context_text = rag_mgr.format_context(docs_ordenados)
        sources_list = MetadataHandler.format_source_list(docs_ordenados)
        context = f"{context_text}\n\n{sources_list}"
    
    return {"context": context}


# NODO 3: Generador (Auditor Estricto)
def generate_response(state: AgentState) -> Dict[str, Any]:
    # Chequear si la consulta fue cancelada
    thread_id = state.get("thread_id", "")
    memory_mgr = get_memory_manager()
    if thread_id and memory_mgr.is_cancelled(thread_id):
        # No agregar nada al historial si fue cancelado
        # El frontend ya mostró el mensaje de cancelación
        return {"chat_history": state["chat_history"]}
    
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

    # System prompt exacto proporcionado por el usuario
    system_prompt = f"""Eres un EXTRACTOR DE INFORMACIÓN DE DOCUMENTOS HISTÓRICOS de la Universidad de Oriente.

Tu única fuente de verdad es el CONTEXTO proporcionado. No puedes usar conocimiento externo.

OBJETIVO:
Extraer información EXACTA y verificable de los documentos.

REGLAS CRÍTICAS:

1. NO INVENTES INFORMACIÓN
- No completes datos faltantes
- No hagas suposiciones
- Puedes interpretar relaciones explícitas del documento aunque estén redactadas de forma diferente a la pregunta.

2. RESPETA LOS NOMBRES Y DATOS EXACTOS
- No corrijas nombres aunque parezcan mal escritos
- No cambies números, fechas o montos
- Copia los datos tal como aparecen en el contexto

3. NO MEZCLES PERSONAS NI DOCUMENTOS
- Si aparecen múltiples personas, responde SOLO sobre la persona preguntada
- Verifica que el nombre en el contexto coincide EXACTAMENTE con la pregunta
- Si hay duda o ambigüedad, NO respondas

4. RESPUESTA SOLO CON INFORMACIÓN RELEVANTE
- No incluyas información adicional innecesaria
- No agregues contexto extra
- Sé directo y preciso

5. SI NO HAY INFORMACIÓN SUFICIENTE
Responde exactamente:
"No se encontró información suficiente en los documentos para responder la pregunta."

6. PRIORIZA EXACTITUD SOBRE COMPLETITUD
- Es mejor dar menos información correcta que más información incorrecta

FORMATO DE RESPUESTA:

- Responde en texto claro y estructurado
- Incluye solo los datos relevantes a la pregunta
- Usa listas si es necesario para claridad

CONTEXTO:
{context}

PREGUNTA:
{input_message}

RESPUESTA:
"""

    def extract_response_text(response):
        """
        Extrae únicamente la respuesta final visible del modelo,
        ignorando bloques de thinking/reasoning.
        """

        content = response.content

        # Caso: lista estructurada
        if isinstance(content, list):

            text_parts = []

            for item in content:

                # Caso 1: string plano = respuesta válida
                if isinstance(item, str):
                    text_parts.append(item)

                # Caso 2: dict estructurado
                elif isinstance(item, dict):

                    # Ignorar thinking
                    if item.get("type") == "thinking":
                        continue

                    # Texto normal
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))

                # Caso 3: objeto con atributos
                elif hasattr(item, "type"):

                    if getattr(item, "type", "") == "thinking":
                        continue

                    if getattr(item, "type", "") == "text":
                        text_parts.append(getattr(item, "text", ""))

                # Caso 4: fallback seguro
                else:
                    text_parts.append(str(item))

            return "\n".join(text_parts).strip()

        # Caso normal
        return str(content).strip()

    try:
        response = llm.invoke(system_prompt)
        
        # Usar la función helper para extraer solo la respuesta
        extracted = extract_response_text(response)
        
        # Si la función devuelve vacío, usar el contenido original como fallback
        if not extracted or len(extracted.strip()) < 5:
            # Fallback: usar response.content directamente
            if hasattr(response, 'content'):
                response_content = str(response.content)
            else:
                response_content = str(response)
        else:
            response_content = extracted
        
    except Exception as e:
        print(f"❌ ERROR en LLM: {type(e).__name__}: {e}")
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

