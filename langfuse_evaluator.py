# langfuse_evaluator.py
import json
from langchain_google_genai import ChatGoogleGenerativeAI
import sqlite3
import os
from datetime import datetime
import requests

# Reusar tu mismo modelo Gemma — no gastar en un modelo externo para el judge
judge_llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.0,
    max_output_tokens=512
)

# Configuración de Langfuse para envío HTTP
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")

def _init_evaluations_db():
    """Crea tabla de evaluaciones si no existe"""
    conn = sqlite3.connect("checkpoints.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_id TEXT UNIQUE,
            query TEXT,
            context TEXT,
            answer TEXT,
            faithfulness REAL,
            retrieval_relevance REAL,
            answer_quality REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def _save_evaluation_to_db(trace_id: str, query: str, context: str, answer: str, 
                          faithfulness: float, relevance: float, quality: float):
    """Guarda evaluación en SQLite"""
    try:
        conn = sqlite3.connect("checkpoints.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO evaluations 
            (trace_id, query, context, answer, faithfulness, retrieval_relevance, answer_quality)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (trace_id, query, context[:1000], answer[:1000], faithfulness, relevance, quality))
        conn.commit()
        conn.close()
        print(f"✅ Evaluación guardada en SQLite: {trace_id}")
    except Exception as e:
        print(f"⚠️ Error guardando en SQLite: {e}")

def _send_to_langfuse(trace_id: str, faithfulness: float, relevance: float, quality: float):
    """Envía scores a Langfuse via API REST (opcional)"""
    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        print(f"⏭️ Langfuse no configurado, scores guardados solo en SQLite")
        return
    
    try:
        # Endpoint de Langfuse para scores
        url = f"{LANGFUSE_HOST}/api/public/scores"
        
        scores = [
            {"traceId": trace_id, "name": "faithfulness", "value": faithfulness},
            {"traceId": trace_id, "name": "retrieval_relevance", "value": relevance},
            {"traceId": trace_id, "name": "answer_quality", "value": quality},
        ]
        
        for score_data in scores:
            response = requests.post(
                url,
                json=score_data,
                auth=(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY),
                timeout=5
            )
            if response.status_code not in [200, 201, 204]:
                print(f"⚠️ Langfuse respondió con {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"⚠️ Error enviando a Langfuse: {e}")


def _clean_context_for_eval(context: str) -> str:
    """Elimina la sección de fuentes para que el juez no la evalúe."""
    if "FUENTES CONSULTADAS:" in context:
        return context.split("FUENTES CONSULTADAS:")[0].strip()
    return context


def _clean_answer_for_eval(answer: str) -> str:
    """Elimina la sección de fuentes de la respuesta para evaluación."""
    if "FUENTES CONSULTADAS:" in answer:
        return answer.split("FUENTES CONSULTADAS:")[0].strip()
    return answer


# Patrones donde el retriever claramente falló (no trajo nada útil)
RETRIEVAL_FAIL_PATTERNS = [
    "no se encontró información suficiente",
    "información solicitada no se encuentra en los documentos",
    "no hay información disponible",
]

# Patrones donde el agente encontró contexto pero el nombre no coincide
# → El retriever funcionó, el problema es la query o el dato real no existe
NAME_MISMATCH_PATTERNS = [
    "no aparece exactamente en el contexto",
    "no aparece en el contexto",
    "el nombre no coincide",
    "nombre no aparece",
]


def _classify_evasive(answer: str):
    """
    Clasifica el tipo de respuesta evasiva.
    
    Retorna:
      'retrieval_fail'  → el retriever no trajo docs relevantes
      'name_mismatch'   → el retriever trajo docs pero el nombre no coincide
      None              → respuesta normal, evaluar con LLM
    """
    answer_lower = answer.lower()
    if any(p in answer_lower for p in NAME_MISMATCH_PATTERNS):
        return "name_mismatch"
    if any(p in answer_lower for p in RETRIEVAL_FAIL_PATTERNS):
        return "retrieval_fail"
    return None


def _safe_score(raw) -> float:
    """
    Extrae el score numérico del output de Gemma.
    
    Gemma con thinking devuelve una lista: 
    [{'type': 'thinking', 'thinking': '...'}, '0.6']
    El score real es SIEMPRE el último elemento.
    """
    try:
        # CASO 1: Es una lista (Gemma con thinking activado)
        if isinstance(raw, list):
            # El score real es el último elemento, ignorar el bloque thinking
            last = raw[-1]
            raw = str(last) if not isinstance(last, str) else last

        # CASO 2: Es un dict (AIMessage o bloque estructurado)
        elif isinstance(raw, dict):
            raw = str(raw.get("content", raw.get("text", "0.5")))

        # Limpiar y convertir
        raw = str(raw).strip().replace(",", ".")
        
        # Buscar el primer número decimal válido en el string limpio
        import re
        nums = re.findall(r"(?<!\d)\d+\.?\d*(?!\d)", raw)
        if nums:
            return max(0.0, min(1.0, float(nums[0])))
            
        return 0.5  # Fallback neutro

    except Exception:
        return 0.5


async def evaluate_rag_response(
    trace_id: str,
    query: str,
    context: str,
    answer: str
):
    """
    Corre los 3 evaluadores y envía los scores a SQLite (y opcionalmente a Langfuse).
    Se ejecuta en background, no bloquea la respuesta al usuario.
    """
    # Inicializar DB
    _init_evaluations_db()
    
    # Limpiar contexto y respuesta antes de evaluar (eliminar sección de fuentes)
    context = _clean_context_for_eval(context)
    answer = _clean_answer_for_eval(answer)
    
    if not context or context.strip() == "":
        # Si no hay contexto (SIN RESULTADOS), marcar como N/A
        _save_evaluation_to_db(trace_id, query, context, answer, 1.0, 0.0, 0.2)
        _send_to_langfuse(trace_id, 1.0, 0.0, 0.2)
        return
    
    # Clasificar tipo de respuesta evasiva si la hay
    evasive_type = _classify_evasive(answer)
    
    if evasive_type == "retrieval_fail":
        # Retriever falló — no trajo lo necesario
        print(f"📊 [EVALUACIÓN] Fallo de retrieval")
        _save_evaluation_to_db(trace_id, query, context, answer, 1.0, 0.0, 0.1)
        _send_to_langfuse(trace_id, 1.0, 0.0, 0.1)
        return
    
    elif evasive_type == "name_mismatch":
        # El agente fue correcto al no responder — nombre no coincide exactamente
        # Faithfulness=1.0 (correcto no inventar), Relevance=0.5 (trajo docs pero del tema equivocado),
        # Quality=0.5 (respuesta honesta y correcta dado lo que había)
        print(f"📊 [EVALUACIÓN] Name mismatch — agente correcto al abstenerse")
        _save_evaluation_to_db(trace_id, query, context, answer, 1.0, 0.5, 0.5)
        _send_to_langfuse(trace_id, 1.0, 0.5, 0.5)
        return

    try:
        # ── EVALUADOR 1: Faithfulness (¿La respuesta se basa solo en el contexto?) ──
        faithfulness_prompt = f"""Eres un evaluador EXTREMADAMENTE CRÍTICO de fidelidad en RAG.

INSTRUCCIÓN PRINCIPAL: Busca CUALQUIER signo de que el modelo inventó, asumió, o extrapoló información.

CONTEXTO RECUPERADO (la ÚNICA fuente válida):
{context[:2500]}

RESPUESTA DEL SISTEMA (esto será evaluado):
{answer[:1200]}

CHECKLIST DE ALUCINACIÓN - Marca BAJA puntuación si encuentras:
☐ Datos específicos (números, nombres, fechas) que NO están exactamente en el contexto
☐ Conexiones causales (porque, resulta en, causó) NO explícitas en el texto
☐ Interpretaciones o "lecturas entre líneas"
☐ Información general que completa datos incompletos del contexto
☐ Plurales/singulares, tiempos verbales que cambian el significado original
☐ Información que requiere cálculo o inferencia (ej: edad a partir de año de nacimiento)

ESCALA (SÉ CRÍTICO):
- 1.0 = CADA palabra se puede rastrear al contexto. Cero inferencias. Copia/paráfrasis directa.
- 0.85 = Muy fiel. Máximo 1-2 palabras o paráfrasis leves aceptables.
- 0.6 = Moderadamente fiel. Tiene inferencias menores pero mantiene la esencia.
- 0.3 = Poco fiel. Muchas inferencias/suposiciones mezcladas.
- 0.0 = Completamente inventada. No se basa en el contexto.

DECISIÓN IMPORTANTE: Si dudas entre 0.6 y 0.85, ELIGE 0.6. Sé crítico.

Responde ÚNICAMENTE con un decimal entre 0 y 1."""

        # ── EVALUADOR 2: Relevancia del retrieval ──
        relevance_prompt = f"""Eres un evaluador DESPIADADO de relevancia en RAG.

PREGUNTA (lo que el usuario quiere saber):
{query}

CONTEXTO RECUPERADO (¿responde esto la pregunta?):
{context[:2500]}

CHECKLIST DE IRRELEVANCIA - Marca BAJA puntuación si:
☐ El contexto habla de un tema relacionado pero NO de la pregunta específica
☐ El contexto tiene información sobre la misma persona/documento pero responde OTRA pregunta
☐ Hay datos generales pero faltan los datos específicos que pide la pregunta
☐ El contexto es "casi relevante" pero no tiene lo necesario para una respuesta completa
☐ La información está en el contexto pero de forma muy vaga o indirecta

ESCALA (PUNTO MÍO: Exigente):
- 1.0 = El contexto contiene LA RESPUESTA EXACTA o datos muy específicos que la resuelven completamente.
- 0.75 = El contexto tiene datos útiles pero faltan detalles específicos para una respuesta completa.
- 0.5 = El contexto es parcialmente relevante, toca el tema pero no responde bien la pregunta específica.
- 0.2 = El contexto es vagamente relacionado, no ayuda mucho.
- 0.0 = Completamente irrelevante.

DECISIÓN IMPORTANTE: Pregunta: "¿Cuál es X?" y contexto dice "hay varios X" → máximo 0.5. No es respuesta.

Responde ÚNICAMENTE con un decimal entre 0 y 1."""

        # ── EVALUADOR 3: Calidad de respuesta ──
        quality_prompt = f"""Eres un evaluador IMPLACABLE de calidad de respuesta.

PREGUNTA ORIGINAL:
{query}

RESPUESTA DEL SISTEMA:
{answer[:1200]}

CHECKLIST DE MALA CALIDAD - Marca BAJA si:
☐ No responde directamente la pregunta (es evasiva)
☐ Falta información específica que la pregunta solicita
☐ Es vaga, imprecisa, o genérica cuando se esperaba especificidad
☐ Incluye información irrelevante que distrae
☐ Está incompleta o a mitad de camino
☐ Contradice lo que dice el contexto
☐ Dice "no se encontró" cuando probablemente hay datos
☐ Responde con "depende" o "podría ser" cuando debería ser definitivo

ESCALA (EXTREMADAMENTE CRÍTICO):
- 1.0 = Responde COMPLETAMENTE la pregunta, específico, claro, sin ambigüedades.
- 0.75 = Buena respuesta, cubre lo esencial pero le falta algún detalle.
- 0.5 = Respuesta aceptable pero incompleta, vaga, o con ambigüedades.
- 0.2 = Respuesta pobre, muy vaga, no es útil.
- 0.0 = No responde la pregunta en absoluto.

EJEMPLOS DE CALIFICACIÓN BAJA:
- Pregunta: "¿Cuál es la calificación?" Respuesta: "Aprobó" → 0.2 (vago, no da número)
- Pregunta: "¿Quién es?" Respuesta: "Una persona importante" → 0.0 (genérico, no responde)
- Pregunta: "¿Dónde? Respuesta: "Aquí/Allá" sin más detalle → 0.2

DECISIÓN: Cuando dudes, sé crítico. La respuesta DEBE ser específica y completa.

Responde ÚNICAMENTE con un decimal entre 0 y 1."""

        # Invocar el judge para los 3 evaluadores
        f_raw = judge_llm.invoke(faithfulness_prompt).content
        print(f"🔍 [DEBUG JUDGE] faithfulness raw: '{f_raw}'")
        r_raw = judge_llm.invoke(relevance_prompt).content
        print(f"🔍 [DEBUG JUDGE] relevance raw: '{r_raw}'")
        q_raw = judge_llm.invoke(quality_prompt).content
        print(f"🔍 [DEBUG JUDGE] quality raw: '{q_raw}'")

        faithfulness_score = _safe_score(f_raw)
        relevance_score = _safe_score(r_raw)
        quality_score = _safe_score(q_raw)

        print(f"📊 [EVALUACIÓN] trace={trace_id[:8]}... | faith={faithfulness_score:.2f} | relev={relevance_score:.2f} | qual={quality_score:.2f}")

        # 1. GUARDAR EN SQLITE (fuente de verdad local)
        _save_evaluation_to_db(trace_id, query, context, answer, faithfulness_score, relevance_score, quality_score)
        
        # 2. ENVIAR A LANGFUSE (opcional)
        _send_to_langfuse(trace_id, faithfulness_score, relevance_score, quality_score)

    except Exception as e:
        print(f"⚠️ [EVALUACIÓN] Error en evaluación: {e}")
