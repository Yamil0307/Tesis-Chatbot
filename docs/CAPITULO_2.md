# CAPÍTULO 2: DISEÑO E IMPLEMENTACIÓN DE LA ARQUITECTURA AGÉNTICA

El presente capítulo describe en detalle la arquitectura diseñada e implementada para el chatbot Agentic RAG de consulta de documentos históricos de la Universidad de Oriente. Se presentan los componentes fundamentales del sistema, las tecnologías empleadas y las decisiones de diseño que sustentan el funcionamiento de la aplicación.

---

## 2.1. Arquitectura General y Flujo de Estados

### 2.1.1. Visión General del Sistema

La arquitectura del sistema se fundamenta en el paradigma de Agentic RAG (Retrieval-Augmented Generation), donde un agente autónomo orquestra la interacción entre la recuperación de información y la generación de respuestas. A diferencia de los flujos lineales tradicionales donde el usuario envía una consulta y recibe una respuesta directa, esta arquitectura implementa ciclos de razonamiento que permiten al sistema evaluar, reformular y validar las búsquedas antes de generar una respuesta final.

El sistema se organiza en tres capas principales: la capa de presentación (Frontend), la capa de procesamiento (Backend con Agente LangGraph) y la capa de datos (FAISS + SQLite). Esta separación de responsabilidades facilita el mantenimiento, permite la escalabilidad independiente de cada componente y garantiza la modularidad del código.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (HTML/JS/CSS)                          │
│              Diseño a pantalla completa                             │
│            Colores: Azul UO #00308F, Rojo UO #C81F1F              │
└──────────────────────────────┬────────────────────────────────────┘
                               │ HTTP JSON
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                             │
│                       Puerto: 8000                                  │
└──────────────────────────────┬────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
│   Auth Manager   │  │Memory Manager│  │  Agent Brain     │
│  (JWT + bcrypt)  │  │(SqliteSaver) │  │  (LangGraph)     │
└──────────────────┘  └──────────────┘  └──────────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │  FAISS      │  │  SQLite      │  │  LangGraph Checkpoints│    │
│  │ (vectores)  │  │ (usuarios)   │  │    (memoria)         │    │
│  └──────────────┘  └──────────────┘  └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1.2. Justificación del Uso de LangGraph

La elección de LangGraph como orquestador del agente se fundamenta en su capacidad para implementar grafos de estado con ciclos de decisión, característica fundamental para lograr la autorreflexión del sistema. A diferencia de los flujos lineales donde cada paso se ejecuta secuencialmente sin posibilidad de evaluación o replanificación, LangGraph permite definir nodos con lógica condicional que pueden modificar el flujo de ejecución basándose en el resultado de operaciones anteriores.

LangGraph proporciona una abstracción de más alto nivel sobre LangChain, permitiendo definir el comportamiento del agente mediante un grafo dirigido donde cada nodo representa una operación atómica y las aristas definen las transiciones posibles. Esta representación gráfica facilita tanto el desarrollo como la depuración del sistema, ya que el flujo de ejecución es claramente visible y modificable.

El grafo de estados implementado en el sistema cuenta con tres nodos principales que se ejecutan secuencialmente: contextualize, search y respond. El nodo contextualize analiza el historial de conversación para reformular la consulta del usuario cuando esta depende de información previamente discutida. El nodo search realiza la recuperación de documentos relevantes de la base de conocimientos. Finalmente, el nodo generate produce la respuesta final integrando el contexto recuperado con las capacidades del modelo de lenguaje.

---

## 2.2. Ingesta y Procesamiento Inteligente de Documentos Históricos

### 2.2.1. Pipeline de Ingestión de Documentos PDF

El sistema implementa un pipeline modularizado de ingestión de documentos que permite procesar archivos PDF de manera eficiente y escalable. Este pipeline se encuentra encapsulado en la clase PDFIngestor, которая maneja todas las etapas desde la carga del documento hasta la indexación en la base de datos vectorial.

La primera etapa del pipeline consiste en la carga del documento mediante PyPDFLoader, una herramienta de LangChain que permite extraer el texto contenido en las páginas del PDF. Este método resulta efectivo para documentos que contienen texto digitalizable, es decir, documentos que fueron creados digitalmente o escaneados con OCR previo. La extracción mantiene la información de página, fundamental para la posterior citación de fuentes.

Una vez cargado el documento, el sistema fragmenta el texto en chunks (fragmentos) de aproximadamente 300 caracteres con una superposición de 50 caracteres entre fragmentos consecutivos. Esta estrategia de fragmentación más granular garantiza que información relevante no quede dividida de manera arbitraria entre dos fragmentos adyacentes, manteniendo la coherencia semántica del contenido y evitando la mezcla de información de diferentes documentos.

### 2.2.2. Procesamiento de Imágenes mediante OCR

Para documentos escaneados o imágenes que no contienen texto digitalizable, el sistema implements OCR (Optical Character Recognition) utilizando la API de Mistral AI (modelo mistral-ocr-latest). Esta funcionalidad se encuentra implementada en el módulo ingest_ocr.py, que procesa imágenes individuales, y en ingest_ocr_folder.py, que permite procesar masivamente carpetas completas de imágenes.

El proceso de OCR codifica la imagen en formato base64 y la envía a la API de Mistral, que devuelve el texto reconocido junto con metadatos adicionales. Este enfoque permite manejar diversos formatos de imagen (JPG, JPEG, PNG, TIFF, BMP, GIF, WEBP) y mantiene una alta precisión en el reconocimiento de caracteres, característica fundamental considerando la calidad variable de los documentos históricos.

El sistema implementa una estrategia de fallback automático: al procesar un PDF, primero intenta extraer el texto con PyPDFLoader; si el resultado contiene menos de 500 caracteres (indicando probable ausencia de texto digitalizable), automáticamente activa el proceso de OCR para garantizar la extracción del contenido.

### 2.2.3. Enriquecimiento de Metadatos y Limpieza de OCR

Cada fragmento de documento se enriqurece con metadatos que facilitan la recuperación y citación posterior. Los metadatos almacenados incluyen: source (ruta del archivo), page (número de página dentro del documento original), file_name (nombre del archivo), chunk_index (posición del fragmento dentro del documento), processed_date (fecha de procesamiento) y search_score (score de relevancia de la búsqueda).

El sistema implementa una limpieza básica del texto extraído del OCR que elimina espacios múltiples, normaliza saltos de línea, elimina líneas vacías repetidas y limpia caracteres de control. Esta limpieza mejora la calidad del texto almacenado en los chunks y reduce el ruido en las búsquedas.

El sistema no utiliza resúmenes automáticos generados por IA (AI summary) para evitar la contaminación semántica entre fragmentos. Esta decisión garantiza que cada chunk contenga únicamente el texto original del documento sin resúmenes que puedan introducir información no presente en el fragmento específico.

---

## 2.3. Representación Semántica y Almacenamiento Vectorial

### 2.3.1. Configuración de Embeddings

El sistema utiliza sentence-transformers/all-MiniLM-L6-v2 como modelo de embeddings. Esta elección se fundamenta en su excelente relación entre calidad de embeddings y velocidad de procesamiento, características fundamentales para un sistema de producción que debe responder en tiempo razonable.

El modelo all-MiniLM-L6-v2 produce embeddings de 384 dimensiones, suficientemente expresivos para capturar relaciones semánticas complejas mientras mantienen un tamaño manejable para el almacenamiento en FAISS. La configuración de carga utiliza HuggingFaceEmbeddings de LangChain, con carga lazy para optimizar el uso de recursos.

### 2.3.2. Indexación en FAISS

FAISS (Facebook AI Similarity Search) constituye el motor de búsqueda vectorial del sistema. Su selección responde a la necesidad de realizar búsquedas de similitud en espacios de alta dimensionalidad de manera eficiente, característica esencial para implementar recuperación semántica a escala.

El sistema implementa la estrategia de recuperación por similitud (similarity) en lugar de MMR. Esta estrategia busca los documentos más similares a la consulta, ideal para datos históricos donde se requiere precisión en lugar de diversidad. El sistema recupera k=8 documentos, número que garantiza capturar la información necesaria manteniendo un balance adecuado con el tiempo de procesamiento.

Adicionalmente, el sistema implementa un mecanismo de boost por nombre que prioriza los documentos que contienen las palabras de la consulta (especialmente nombres de personas), garantizando que las búsquedas por personas específicas retornen los documentos más relevantes.

### 2.3.3. Estrategia de Metadatos

Los metadatos se almacenan junto con cada vector en el índice FAISS, permitiendo filtrar y reranking posterior basado en criterios semánticos. Cada chunk de documento mantiene rastreo de su origen (documento fuente, número de página, posición en el documento), información crucial para implementar citación académica precisa.

El sistema guarda el vectorstore en disco de forma local en el directorio vectorstore_faiss/, permitiendo su recarga en ejecuciones posteriores sin necesidad de reprocesar los documentos. Esta persistencia es fundamental para entornos de producción donde el reprocesamiento sería costoso computacionalmente.

---

## 2.4. Diseño del Agente y Orquestación de Nodos

### 2.4.1. Estructura del Grafo de Estados

El agente implementa un grafo de estados utilizando LangGraph con la clase StateGraph. La definición del estado (AgentState) especifica los campos que circulan entre nodos: input (consulta del usuario), chat_history (historial de mensajes), context (documentos recuperados) y search_query (consulta reformulada).

La arquitectura de tres nodos implementada difiere del modelo Retrieval-Grader-Rewrite-Generate propuesto inicialmente en la planificación. Los nodos implementados responden a las necesidades específicas del sistema:

1. **Nodo contextualize (Reescritura de consultas)**: Este nodo analiza el historial de conversación para reformular consultas que dependen de contexto previo. Por ejemplo, si el usuario pregunta "¿Quiénes son sus tutores?" después de discutir sobre una tesis específica, el nodo reformula la consulta a "¿Quiénes son los tutores de la tesis de [nombre]?". Este nodo utiliza un prompt específico que instructua al modelo a generar preguntas independientes y específicas para búsqueda en base de datos.

2. **Nodo search (Recuperación de documentos)**: Este nodo ejecuta la búsqueda en FAISS utilizando la consulta reformulada (o la original si no hay historial). Recupera k=8 documentos aplicando búsqueda por similitud, y combina el contenido con la información de fuentes para formar el contexto que será utilizado en la generación. El sistema limita el contexto a máximo 6 documentos para evitar saturación del modelo.

3. **Nodo respond (Generación de respuesta)**: Este nodo produce la respuesta final integrando el contexto recuperado con el modelo de lenguaje. El system prompt implementa un rol de extractor de información que prioriza la exactitud sobre la completitud, con reglas explícitas: no inventar información, usar datos exactos del contexto, no mezclar personas, y responder "No se encontró información suficiente en los documentos para responder la pregunta" cuando no hay datos disponibles.

### 2.4.2. Mecanismos Anti-Alucinación

El sistema implementa múltiples mecanismos para prevenir alucinaciones (generación de información no presente en los documentos base):

- **Temperatura 0.0**: El modelo de lenguaje se configura con temperatura cero, guaranteeing respuestas deterministas y minimizando la creatividad del modelo.
- **Búsqueda obligatoria**: El flujo del agente siempre ejecuta la búsqueda en FAISS antes de generar una respuesta. No existe la posibilidad de que el modelo responda directamente sin consultar la base de conocimientos.
- **System prompt restrictivo**: El prompt del sistema incluye instrucciones explícitas de solo usar información del contexto proporcionado, prohibido usar conocimiento externo, y respuestas predefinidas para cuando no se encuentra información relevante ("No se encontró información suficiente en los documentos para responder la pregunta.").
- **Detectores de vacío**: Cuando la búsqueda no retorna resultados, el sistema devuelve automáticamente el mensaje "[SIN RESULTADOS]" forzando al modelo a indicar que no tiene información sobre el tema consultado.
- **Priorización de exactitud**: Las instrucciones enfatizan que es mejor dar menos información correcta que más información incorrecta, y el modelo debe preferir decir "no sé" a inventar datos.

### 2.4.3. Manejo de Memoria Conversacional

El sistema implementa memoria persistente mediante SqliteSaver de LangGraph, almacenada en checkpoints.db. Cada sesión de usuario mantiene un thread_id único que permite recuperar el estado conversacional entre invocaciones. Esta característica es fundamental para mantener coherencia en conversaciones extensas donde el usuario hace preguntas de seguimiento.

El historial de mensajes se construye concatenando HumanMessage y AIMessage, transmitiéndose entre invocaciones del agente. El sistema limita el historial a los últimos 4 mensajes para evitar contaminación semántica entre conversaciones largas. El modelo de lenguaje recibe este historial como parte del contexto, permitiendo que las respuestas consideren el flujo conversacional completo.

---

## 2.5. Interfaz de Usuario e Integración del Sistema

### 2.5.1. Backend con FastAPI

El backend se implementa utilizando FastAPI, un framework moderno y de alto rendimiento para construir APIs con Python. La aplicación corre en el puerto 8000 y expone los siguientes endpoints:

- **GET /**: Health check para verificar que el servidor está funcionando.
- **POST /register**: Registro de nuevos usuarios con validación de email y password.
- **POST /login**: Autenticación de usuarios que retorna un token JWT.
- **POST /chat**: Endpoint principal que recibe las consultas del usuario y retorna las respuestas del agente.

La autenticación utiliza JWT (JSON Web Tokens) con expiración de 60 minutos. Las contraseñas se almacenan hasheadas utilizando bcrypt, garantizando seguridad en caso de compromiso de la base de datos. El sistema de sesiones permite que cada usuario tenga conversaciones aisladas mediante el uso de thread_ids únicos por sesión.

### 2.5.2. Frontend

El frontend se desarrolla utilizando Vanilla JavaScript y CSS3, manteniendo la simplicidad y eficiencia sin dependencias externas innecesarias. El diseño implementa una interfaz a pantalla completa con dos paneles:

El panel izquierdo muestra información institucional de la Universidad de Oriente (logo, misión, características del sistema), mientras que el panel derecho contiene el área de chat. La paleta de colores utiliza los colores oficiales de la Universidad: azul UO (#00308F) para elementos institucionales y rojo UO (#C81F1F) para acentos y botones de acción del usuario.

La interfaz incluye: formulario de login/registro conmutativo, área de mensajes con diferenciación visual entre mensajes del usuario y del bot, dropdown interactivo para mostrar las fuentes consultadas, spinner de carga durante el procesamiento de consultas, e indicador de estado de conexión con la API.

### 2.5.3. Mecanismos de Citación de Fuentes

El sistema implementa citación académica automática mediante el módulo metadata_handler.py. Cada fragmento recuperado incluye metadatos de página y nombre de archivo, información que se formatea en la sección "FUENTES CONSULTADAS:" al final de cada respuesta del agente.

El formato de citación sigue el estándar académico: [Nombre del Archivo] (página X): "Fragmento del texto". Las fuentes se muestran en un elemento HTML details/summary que permite expandir y colapsar la lista de referencias, manteniendo la interfaz limpia mientras ofrece acceso completo a la información de origen.

---

## 2.6. Estrategia de Despliegue Local y Soberanía Tecnológica

### 2.6.1. Estado Actual de la Soberanía

El sistema actual mantiene dependencia del modelo de lenguaje Gemini de Google (gemma-3-4b-it) y del servicio de OCR de Mistral AI. Esta configuración fue seleccionada por su facilidad de integración y calidad de resultados durante la fase de desarrollo. Sin embargo, la arquitectura está diseñada para permitir la transición a servicios locales cuando sea necesario.

La Etapa 4 del plan de desarrollo (actualmente pendiente) contempla la implementación de Ollama para ejecutar modelos de lenguaje localmente (Llama 3 o Mistral), eliminando la dependencia de servicios externos y garantizando el funcionamiento del sistema sin conexión a internet. Esta característica es fundamental para el despliegue en los servidores de la Universidad de Oriente, donde la conectividad puede ser limitada o intermitente.

### 2.6.2. Infraestructura de Despliegue

El sistema está diseñado para ejecutarse en servidores locales con los siguientes requisitos mínimos:

- Python 3.9+ con entorno virtual
- 8 GB de RAM mínimo (16 GB recomendado para embeddings)
- 10 GB de espacio en disco para vectorstore y documentos
- Sin conexión a internet (capacidad offline con Ollama una vez implementado)

La base de datos de usuarios (users.db), la memoria de conversaciones (checkpoints.db) y el índice vectorial (vectorstore_faiss/) se almacenan localmente, proporcionando persistencia entre ejecuciones del servidor sin necesidad de servicios externos de bases de datos.

---

## Resumen del Capítulo

Este capítulo ha presentado la arquitectura completa del sistema Agentic RAG desarrollado para la consulta de documentos históricos de la Universidad de Oriente. La implementación utiliza LangGraph para la orquestación del agente, FAISS para la búsqueda vectorial, Mistral OCR para el procesamiento de documentos escaneados, y una interfaz web basada en Vanilla JavaScript con el identity visual de la institución.

Las decisiones de diseño priorizaron la modularidad, permitiendo que cada componente evolucionara independientemente; la trazabilidad, garantizando que cada respuesta pueda rastrear sus fuentes; y la escalabilidad, facilitando la incorporación de nuevos formatos de documento y capacidades adicionales en fases futuras.

El siguiente capítulo abordará los aspectos metodológicos de la investigación y la validación experimental del sistema.