"""
ESTRUCTURA DEL PROYECTO - Tesis Agentic RAG
============================================

# ✅ ETAPAS COMPLETADAS

## Etapa 0: Refactorización Estructural ✅
- Módulos centralizados (rag_manager, metadata_handler, ingest_utils)
- Lazy loading de embeddings
- Código limpio y modular

## Etapa 1: Memoria Conversacional ✅ NUEVA
- SqliteSaver para persistencia
- Thread_id para sesiones
- Historial que crece correctamente
- LLM recibe contexto completo
- localStorage para recuperación

---

# ARCHIVOS PRINCIPALES (CRÍTICOS - NO ELIMINAR)

1. main.py

   - FastAPI server
   - Endpoint POST /chat para consultas
   - Manejo de CORS
   - Punto de entrada del servidor
   - ✅ NUEVO: Soporta thread_id para memoria

2. agent_brain.py

   - Lógica del agente LangGraph
   - Definición de nodos y rutas
   - Herramienta search_university_history
   - Compilación del grafo
   - ✅ NUEVO: Compilado con SqliteSaver checkpointer
   - ✅ NUEVO: generate_response() agrega al historial

3. memory_manager.py ✅ NUEVO

   - Gestor de sesiones con SqliteSaver
   - Recuperación de estado anterior (get_last_state)
   - Persistencia en checkpoints.db
   - Thread management

3. rag_manager.py

   - Gestor centralizado de RAG
   - Carga y manejo de FAISS
   - Búsqueda de documentos
   - Inicialización lazy

4. metadata_handler.py

   - Extracción de metadatos
   - Formateo de citaciones
   - Preparación para Etapa 2

5. memory_manager.py (Preparación para Etapa 1)
   - Gestor de sesiones
   - Preparación para SqliteSaver (Etapa 1)
   - Gestión de estados
     [NOTA: No se usa aún - se activará en Etapa 1]

# ARCHIVOS DE INGESTA

1. ingest_data.py

   - Script principal de ingesta
   - Punto de entrada para cargar documentos
   - Mantiene compatibilidad hacia atrás

2. ingest_pdf.py

   - Clase PDFIngestor
   - Pipeline de procesamiento de PDFs
   - Modular para futuros formatos

3. ingest_utils.py
   - Funciones auxiliares reutilizables
   - Carga de embeddings
   - Fragmentación de texto
   - Gestión de metadatos

# ARCHIVOS DE CONFIGURACIÓN

1. .env
   - Variables de entorno
   - GOOGLE_API_KEY
   - Otros parámetros de configuración

# DIRECTORIOS

1. frontend/

   - index.html - Interfaz web
   - script.js - Lógica del cliente
   - styles.css - Estilos CSS

2. data/

   - documento_tesis.pdf - PDF principal a procesar

3. vectorstore_faiss/

   - index.faiss - Base de datos vectorial compilada
   - Almacena embeddings de documentos

4. venv/
   - Entorno virtual de Python
   - Dependencias instaladas

# ARCHIVOS ELIMINADOS (OBSOLETOS)

✓ test_refactoring.py - Test de refactorización Etapa 0
✓ test_lazy_loading.py - Test de lazy loading
✓ ETAPA_0_SUMMARY.md - Documentación de Etapa 0
✓ checkpoints.db - Base de datos de sesiones (no usada)
✓ memoria_chat.sqlite - Intento anterior de persistencia
✓ **pycache**/ - Caché de Python (se regenera automáticamente)

# FLUJO DE TRABAJO

1. Usuario accede a http://localhost:8000/
   └─> Frontend (HTML/JS) se carga

2. Usuario escribe pregunta en el chat
   └─> script.js envía POST /chat

3. main.py recibe la solicitud
   └─> Inicializa RAG Manager (lazy) si es primera vez
   └─> Ejecuta agent_brain.py

4. Agent decide si usar búsqueda
   ├─> SÍ: Usa rag_manager.search() → metadata_handler
   └─> NO: Responde directamente

5. Respuesta se envía al frontend
   └─> Frontend muestra resultado

# PRÓXIMOS PASOS (ETAPAS PLANIFICADAS)

Etapa 1: Memoria Conversacional

- Integrar SqliteSaver
- Persistencia automática

Etapa 2: Citación de Fuentes

- Validación formal de metadatos
- Incluir fuentes en respuestas

Etapa 3: OCR Avanzado

- PaddleOCR para PDFs escaneados
- Fallback inteligente

Etapa 4: Soberanía Total

- Ollama + Llama 3
- Desconexión de internet

Etapa 5: Sistema de Usuarios

- Login/Registro
- Multi-usuario

# CÓMO EJECUTAR

1. Activar venv:
   source venv/Scripts/Activate

2. Iniciar servidor:
   python main.py

3. Acceder a:
   http://localhost:8000

4. Cargar documentos (si necesario):
   python ingest_data.py

# DEPENDENCIAS CRÍTICAS

- fastapi: Server HTTP
- langchain: Framework IA
- langgraph: Orquestación de grafo
- faiss-cpu: Vector database
- sentence-transformers: Embeddings locales
- google-generativeai: LLM Gemini
  """

if **name** == "**main**":
print(**doc**)
