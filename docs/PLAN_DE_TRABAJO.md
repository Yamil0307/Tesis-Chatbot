# 🗺️ PLAN DE TRABAJO INCREMENTAL - Tesis Agentic RAG

**Última actualización**: Diciembre 8, 2025  
**Estado actual**: Refactorización Etapa 0 completada ✅  
**Timeline**: Noviembre 2024 → Febrero 2025  
**Objetivo final**: Presentación en forum + Sistema multi-usuario en servidor UO

---

## 📋 TABLA DE CONTENIDOS

1. [Estado Actual](#estado-actual)
2. [Etapa 1: Memoria Conversacional](#etapa-1-memoria-conversacional)
3. [Etapa 2: Citación de Fuentes](#etapa-2-citación-de-fuentes)
4. [Etapa 3: OCR Avanzado](#etapa-3-ocr-avanzado)
5. [Etapa 4: Soberanía Total](#etapa-4-soberanía-total)
6. [Etapa 5: Sistema de Usuarios](#etapa-5-sistema-de-usuarios)
7. [Consideraciones Importantes](#consideraciones-importantes)

---

## 🎯 ESTADO ACTUAL

### ✅ Completado (Etapa 0: Refactorización Estructural)

**Módulos creados:**

- `rag_manager.py` - Gestor centralizado de RAG
- `metadata_handler.py` - Extracción de metadatos
- `ingest_pdf.py` - Ingesta modular de PDFs
- `ingest_utils.py` - Utilidades reutilizables

**Módulos refactorizados:**

- `agent_brain.py` - Uso de gestores centralizados
- `main.py` - Limpio, sin referencias a memoria
- `ingest_data.py` - Usa ingest_pdf.py

**Optimizaciones:**

- Lazy loading de embeddings ✅
- Código modular y testeable ✅
- Arquitectura escalable ✅
- Limpieza de archivos obsoletos ✅

**Status**: 🟢 PRODUCCIÓN LISTA

---

## 🚀 ETAPA 1: MEMORIA CONVERSACIONAL

**Objetivo**: El bot recuerda conversaciones dentro de una sesión  
**Duración estimada**: 1-2 semanas  
**Criticidad para forum**: MEDIA (mejora UX)  
**Dependencias**: Etapa 0 ✅

### Tareas

#### 1.1 Reactivar memory_manager.py

```python
# Recrear memory_manager.py (fue eliminado por ahora)
# - Clase MemoryManager con SqliteSaver
# - Métodos: create_session(), get_config_for_thread(), get_initial_state()
```

**Checklist:**

- [ ] Crear memory_manager.py con SqliteSaver
- [ ] Prueba: Crear sesión válida
- [ ] Prueba: get_config_for_thread() retorna config válida

**Archivos a modificar:**

- Crear: `memory_manager.py`

---

#### 1.2 Integrar SqliteSaver en agent_brain.py

```python
# En agent_brain.py
from memory_manager import get_memory_manager

memory_mgr = get_memory_manager()
saver = memory_mgr.get_saver()

# Compilar grafo CON checkpointer
app = workflow.compile(checkpointer=saver)
```

**Checklist:**

- [ ] Import memory_manager en agent_brain.py
- [ ] Obtener saver desde memory_manager
- [ ] Compilar workflow.compile(checkpointer=saver)
- [ ] Prueba: test_agent() con thread_id

**Archivos a modificar:**

- `agent_brain.py` - Agregar checkpointer

---

#### 1.3 Actualizar main.py para soportar thread_id

```python
# En main.py
class ChatRequest(BaseModel):
    user_input: str
    thread_id: Optional[str] = None  # ← NUEVO

@app_fastapi.post("/chat")
def run_chat(request: ChatRequest):
    memory_mgr = get_memory_manager()

    if not request.thread_id:
        thread_id = memory_mgr.create_session("user_default")
    else:
        thread_id = request.thread_id

    config = memory_mgr.get_config_for_thread(thread_id)
    final_state = app.invoke(initial_state, config=config)

    return {
        "status": "success",
        "response": response,
        "thread_id": thread_id  # ← Devolver para que frontend lo guarde
    }
```

**Checklist:**

- [ ] Agregar thread_id en ChatRequest
- [ ] Lógica de creación/obtención de sesión
- [ ] Pasar config a app.invoke()
- [ ] Retornar thread_id en respuesta
- [ ] Prueba: POST /chat sin thread_id (crea nuevo)
- [ ] Prueba: POST /chat con thread_id (mantiene conversación)

**Archivos a modificar:**

- `main.py` - Agregar thread_id en request y response

---

#### 1.4 Actualizar frontend para guardar thread_id

```javascript
// En script.js
let currentThreadId = null; // Guardar el thread_id de sesión

async function sendMessage(message) {
  const payload = {
    user_input: message,
    thread_id: currentThreadId,
  };

  const response = await fetch(API_URL, {
    method: "POST",
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  // IMPORTANTE: Guardar el thread_id de la sesión
  if (data.thread_id && !currentThreadId) {
    currentThreadId = data.thread_id;
    localStorage.setItem("threadId", currentThreadId);
  }

  displayMessage(data.response, "bot");
}
```

**Checklist:**

- [ ] Agregar currentThreadId en script.js
- [ ] Incluir thread_id en POST /chat
- [ ] Guardar thread_id en localStorage
- [ ] Cargar thread_id del localStorage al iniciar
- [ ] Prueba: Cerrar y abrir navegador - historial persiste

**Archivos a modificar:**

- `frontend/script.js` - Agregar manejo de thread_id

---

#### 1.5 Testing

```bash
# Test unitario
python -m pytest tests/test_memory_manager.py

# Test de integración
1. Abrir navegador → http://localhost:8000
2. Pregunta 1: "¿Cómo te llamas?"
3. Pregunta 2: "¿Recuerdas lo que preguntaste antes?"
   → Bot debe referenciar pregunta anterior
4. Cerrar navegador
5. Reabrir
   → Conversación anterior debe estar disponible
```

**Checklist:**

- [ ] Test unitario: create_session()
- [ ] Test unitario: get_config_for_thread()
- [ ] Test integración: conversación persiste en misma sesión
- [ ] Test integración: conversación persiste después de cerrar navegador

---

### Resultado esperado

✅ Conversaciones persistentes por sesión  
✅ Frontend guarda thread_id  
✅ Histórico disponible al reabrir navegador

---

## 📄 ETAPA 2: CITACIÓN DE FUENTES

**Objetivo**: Respuestas incluyen fuentes académicas formales  
**Duración estimada**: 2 semanas  
**Criticidad para forum**: 🔴 ALTA (credibilidad académica)  
**Dependencias**: Etapa 1 (opcional, pero recomendado)

### Tareas

#### 2.1 Enriquecer metadatos en ingest_pdf.py

```python
# En ingest_pdf.py - método process_documents()
def process_documents(self, documents, ...):
    texts = split_documents(documents)

    # Agregar metadatos completos
    for idx, doc in enumerate(texts):
        if not doc.metadata:
            doc.metadata = {}
        doc.metadata.update({
            "source": pdf_path,
            "page": doc.metadata.get("page", 0),
            "chunk_index": idx,
            "file_name": os.path.basename(pdf_path),
            "processed_date": datetime.now().isoformat()
        })

    return texts
```

**Checklist:**

- [ ] Agregar metadatos completos en process_documents()
- [ ] Verificar que FAISS almacena metadatos
- [ ] Prueba: Búsqueda recupera metadatos correctos

**Archivos a modificar:**

- `ingest_pdf.py` - Enriquecer metadatos

---

#### 2.2 Mejorar search_university_history en agent_brain.py

```python
@tool
def search_university_history(query: str) -> str:
    """..."""
    rag_mgr = get_rag_manager()
    docs = rag_mgr.search(query, k=4)

    # Extraer y guardar metadatos
    sources_info = []
    for doc in docs:
        metadata = MetadataHandler.extract_source_info(doc)
        sources_info.append(metadata)

    # Guardar en estado para generar_response
    context = rag_mgr.format_context(docs)
    sources_list = MetadataHandler.format_source_list(docs)

    # IMPORTANTE: Incluir info de fuentes en el contexto
    return f"{context}\n\n{sources_list}"
```

**Checklist:**

- [ ] Usar MetadataHandler.extract_source_info()
- [ ] Incluir fuentes en contexto
- [ ] Prueba: Búsqueda retorna contexto + fuentes

**Archivos a modificar:**

- `agent_brain.py` - Mejorar search_university_history

---

#### 2.3 Actualizar generate_response para incluir citaciones

```python
def generate_response(state: AgentState) -> Dict[str, Any]:
    """Genera respuesta con citaciones académicas"""

    context = state["context"]
    input_message = state["input"]

    system_prompt = (
        "Eres un chatbot experto en la Universidad de Oriente. "
        "IMPORTANTE: Al final de tu respuesta, incluye una sección de FUENTES "
        "con el siguiente formato:\n\n"
        "FUENTES CONSULTADAS:\n"
        "- [Nombre del documento] (página X)\n"
        "- [Nombre del documento] (página Y)\n\n"
        f"{context}"
    )

    response_chain = llm.bind(system=system_prompt)
    final_response = response_chain.invoke([HumanMessage(content=input_message)])

    return {"chat_history": [AIMessage(content=final_response.content)]}
```

**Checklist:**

- [ ] System prompt incluye instrucción de citaciones
- [ ] LLM genera respuesta + fuentes
- [ ] Prueba: Respuesta incluye sección "FUENTES CONSULTADAS"

**Archivos a modificar:**

- `agent_brain.py` - Mejorar generate_response

---

#### 2.4 Actualizar frontend para mostrar fuentes

```javascript
// En script.js - mejorar addMessage()
function addMessage(text, sender, isRag = false) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message");
  messageDiv.classList.add(sender === "user" ? "user-message" : "bot-message");

  // Separar contenido de fuentes
  const parts = text.split("FUENTES CONSULTADAS:");
  const response = parts[0].trim();
  const sources = parts[1] ? parts[1].trim() : null;

  let content = response.replace(/\n/g, "<br>");

  if (sources) {
    content += `<div class="sources"><strong>FUENTES:</strong><br>${sources}</div>`;
  }

  messageDiv.innerHTML = content;
  chatMessages.appendChild(messageDiv);
}
```

```css
/* En styles.css */
.sources {
  margin-top: 10px;
  padding: 10px;
  background-color: #f0f0f0;
  border-left: 3px solid #007bff;
  font-size: 0.9em;
  color: #555;
  font-style: italic;
}
```

**Checklist:**

- [ ] Agregar estilos CSS para sección de fuentes
- [ ] Parsear y mostrar fuentes en frontend
- [ ] Prueba: Fuentes se visualizan correctamente
- [ ] Prueba: Formato académico es clara

**Archivos a modificar:**

- `frontend/script.js` - Mostrar fuentes
- `frontend/styles.css` - Estilos para fuentes

---

#### 2.5 Testing

```bash
# Test: Pregunta sobre historia
Pregunta: "¿Cuál es la historia de la Universidad de Oriente?"

Resultado esperado:
- Respuesta con información del PDF
- Sección "FUENTES CONSULTADAS:" al final
- Formato: "- [Nombre documento] (página X)"
```

**Checklist:**

- [ ] Test manual: Pregunta genera fuentes
- [ ] Test manual: Formato académico correcto
- [ ] Test manual: Fuentes se visualizan en frontend

---

### Resultado esperado

✅ Respuestas con citaciones académicas  
✅ Referencia a páginas específicas  
✅ Sección de fuentes clara y visible  
✅ Cumple requisitos académicos de rigor

---

## 🔍 ETAPA 3: OCR AVANZADO

**Objetivo**: Soportar PDFs escaneados (imágenes)  
**Duración estimada**: 2-3 semanas  
**Criticidad para forum**: MEDIA (bonus feature)  
**Dependencias**: Etapa 2 (opcional)

### Tareas

#### 3.1 Crear ocr_ingest.py

```python
"""
ocr_ingest.py - Ingesta de PDFs escaneados con OCR

Soporta:
- PDFs digitales (fallback rápido a PyPDFLoader)
- PDFs escaneados (PaddleOCR)
- Detección automática
"""

class OCRIngestor:
    def __init__(self):
        self.ocr = PaddleOCR(use_gpu=False, lang=['en', 'es'])

    def ingest_pdf_with_ocr(self, pdf_path):
        """Intenta PyPDFLoader primero, fallback a OCR si es necesario"""

        # Intenta carga rápida primero
        docs = self._try_fast_load(pdf_path)

        if docs and self._has_content(docs):
            return docs  # Contenido digital detectado

        # Fallback a OCR para PDFs escaneados
        return self._ocr_extraction(pdf_path)

    def _try_fast_load(self, pdf_path):
        """Intenta PyPDFLoader"""
        try:
            loader = PyPDFLoader(pdf_path)
            return loader.load()
        except:
            return None

    def _has_content(self, docs):
        """Verifica si hay contenido significativo"""
        total_chars = sum(len(d.page_content) for d in docs)
        return total_chars > 500  # Mínimo 500 caracteres

    def _ocr_extraction(self, pdf_path):
        """Extrae texto con PaddleOCR"""
        from pdf2image import convert_from_path

        images = convert_from_path(pdf_path)
        documents = []

        for page_num, image in enumerate(images):
            result = self.ocr.ocr(image)
            text = "\n".join([line[0][1] for line in result[0] if result[0]])

            doc = Document(
                page_content=text,
                metadata={
                    "source": pdf_path,
                    "page": page_num + 1,
                    "ocr_processed": True
                }
            )
            documents.append(doc)

        return documents
```

**Checklist:**

- [ ] Crear ocr_ingest.py con OCRIngestor
- [ ] Implementar detección automática
- [ ] Implementar fallback a OCR

---

#### 3.2 Integrar en pipeline de ingest

```python
# En ingest_data.py
from ocr_ingest import OCRIngestor

def create_vector_db():
    # Intentar con OCR ingestor (que maneja ambos casos)
    ocr_ingestor = OCRIngestor()
    documents = ocr_ingestor.ingest_pdf_with_ocr(PDF_PATH)

    # Resto del pipeline igual
```

**Checklist:**

- [ ] Integrar OCRIngestor en ingest_data.py
- [ ] Mantener compatibilidad hacia atrás

---

#### 3.3 Testing

```bash
# Test 1: PDF digital
python ingest_data.py
# → Debe usar fast load

# Test 2: PDF escaneado
# (Necesita PDF escaneado de prueba)
python ingest_data.py
# → Debe usar OCR, detectar texto en imagen
```

**Checklist:**

- [ ] Test con PDF digital
- [ ] Test con PDF escaneado
- [ ] Verificar metadata "ocr_processed"

---

### Resultado esperado

✅ Soporta PDFs digitales (rápido)  
✅ Soporta PDFs escaneados (OCR)  
✅ Detección automática  
✅ Metadata indica si fue OCR

---

## 🔐 ETAPA 4: SOBERANÍA TOTAL

**Objetivo**: Ejecutar sin dependencias de internet (Ollama + Llama 3)  
**Duración estimada**: 1-2 semanas  
**Criticidad para forum**: BAJA (pero importante para despliegue final)  
**Dependencias**: Etapa 3 (opcional)

### Tareas

#### 4.1 Instalación de Ollama

```bash
# En el servidor de la Universidad
# Descargar Ollama desde https://ollama.ai

# Descargar modelo Llama 3
ollama pull llama3:7b

# Verificar
ollama list
# → Debe mostrar: NAME           ID              SIZE      MODIFIED
#   llama3:7b    8c2e06607d7e   3.8 GB   2 minutes ago
```

**Checklist:**

- [ ] Ollama instalado en servidor UO
- [ ] Modelo llama3:7b descargado
- [ ] Verificar: `ollama list`
- [ ] Verificar: API disponible en http://localhost:11434

---

#### 4.2 Cambiar LLM en agent_brain.py

```python
# ANTES: Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# DESPUÉS: Ollama
from langchain_ollama import ChatOllama
llm = ChatOllama(
    model="llama3:7b",
    temperature=0,
    base_url="http://localhost:11434"
)
```

**Cambios necesarios**: SOLO 2 LÍNEAS

**Checklist:**

- [ ] Cambiar import en agent_brain.py
- [ ] Cambiar inicialización de llm
- [ ] Prueba: test_agent() funciona con Ollama
- [ ] Prueba: Respuestas similares en calidad

**Archivos a modificar:**

- `agent_brain.py` - Solo 2 líneas

---

#### 4.3 Crear script de configuración

```python
# config.py - Nueva
class LLMConfig:
    # Opciones disponibles
    PROVIDERS = {
        "gemini": {
            "class": "ChatGoogleGenerativeAI",
            "model": "gemini-2.0-flash"
        },
        "ollama": {
            "class": "ChatOllama",
            "model": "llama3:7b",
            "base_url": "http://localhost:11434"
        }
    }

    @staticmethod
    def get_llm(provider="ollama"):
        """Obtiene el LLM configurado"""
        if provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
        elif provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model="llama3:7b",
                temperature=0,
                base_url="http://localhost:11434"
            )
```

**Checklist:**

- [ ] Crear config.py
- [ ] Configuración de múltiples proveedores
- [ ] Usar en agent_brain.py

---

#### 4.4 Testing

```bash
# Test 1: Verificar Ollama funciona
ollama serve  # En terminal separada

# Test 2: Test agent con Ollama
python agent_brain.py
# → Debe responder sin API de Google

# Test 3: Comparar respuestas
# Gemini vs Ollama - ¿Calidad similar?
```

**Checklist:**

- [ ] Ollama responde correctamente
- [ ] Agent funciona sin Gemini API
- [ ] Calidad de respuestas aceptable

---

### Resultado esperado

✅ Sistema funciona sin conexión a internet  
✅ Independencia de Gemini API  
✅ Modelo local (Llama 3)  
✅ Escalable a otro hardware

---

## 👥 ETAPA 5: SISTEMA DE USUARIOS

**Objetivo**: Multi-usuario con login/registro  
**Duración estimada**: 3-4 semanas  
**Criticidad para forum**: BAJA (pero esencial para despliegue UO)  
**Dependencias**: Etapa 1 (memoria) + Etapa 4 (soberanía)

### Tareas

#### 5.1 Crear auth_manager.py

```python
# auth_manager.py - Gestión de usuarios

from passlib.context import CryptContext
import sqlite3
from datetime import datetime

class AuthManager:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.pwd_context = CryptContext(schemes=["bcrypt"])
        self._init_db()

    def _init_db(self):
        """Crea tablas si no existen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                thread_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        conn.close()

    def register(self, username: str, email: str, password: str) -> bool:
        """Registra nuevo usuario"""
        try:
            password_hash = self.pwd_context.hash(password)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            """, (username, email, password_hash))

            conn.commit()
            conn.close()
            return True
        except:
            return False

    def login(self, username: str, password: str) -> int:
        """Valida usuario, retorna user_id o None"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        user_id, password_hash = result
        if self.pwd_context.verify(password, password_hash):
            return user_id
        return None
```

**Checklist:**

- [ ] Crear auth_manager.py
- [ ] Implementar register()
- [ ] Implementar login()
- [ ] Implementar sesiones de usuario

---

#### 5.2 Crear auth_middleware en main.py

```python
# En main.py
from auth_manager import AuthManager
from fastapi.security import HTTPBearer

auth_manager = AuthManager()
security = HTTPBearer()

@app_fastapi.post("/register")
async def register(username: str, email: str, password: str):
    success = auth_manager.register(username, email, password)
    if success:
        return {"status": "success", "message": "Usuario registrado"}
    return {"status": "error", "message": "Usuario o email ya existe"}

@app_fastapi.post("/login")
async def login(username: str, password: str):
    user_id = auth_manager.login(username, password)
    if user_id:
        return {
            "status": "success",
            "user_id": user_id,
            "message": "Login exitoso"
        }
    return {"status": "error", "message": "Credenciales inválidas"}

@app_fastapi.post("/chat")
def run_chat(request: ChatRequest, token: str = Depends(security)):
    # Validar token
    # user_id = obtener del token

    # Crear thread_id asociado a usuario
    # thread_id = f"user_{user_id}_{conversacion_id}"

    # Resto igual...
```

**Checklist:**

- [ ] Endpoints /register y /login
- [ ] Token validation en /chat
- [ ] Thread_id asociado a usuario

---

#### 5.3 Actualizar frontend con login

```html
<!-- En index.html -->
<div id="login-container">
  <input id="username-input" placeholder="Usuario" />
  <input id="password-input" type="password" placeholder="Contraseña" />
  <button id="login-btn">Entrar</button>
  <button id="register-btn">Registrarse</button>
</div>

<div id="chat-container" style="display: none;">
  <!-- Chat actual -->
</div>
```

```javascript
// En script.js
let currentUser = null;
let currentToken = null;

async function login() {
  const username = document.getElementById("username-input").value;
  const password = document.getElementById("password-input").value;

  const response = await fetch(API_URL + "login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

  const data = await response.json();
  if (data.status === "success") {
    currentUser = data.user_id;
    currentToken = data.token;

    // Mostrar chat, ocultar login
    document.getElementById("login-container").style.display = "none";
    document.getElementById("chat-container").style.display = "block";
  }
}
```

**Checklist:**

- [ ] Interfaz de login/registro
- [ ] Flujo de autenticación
- [ ] Almacenamiento seguro de token

---

#### 5.4 Testing

```bash
# Test 1: Registro
POST /register
{
    "username": "alumno_001",
    "email": "alumno@uo.edu.cu",
    "password": "secure_pass"
}
# → {"status": "success"}

# Test 2: Login
POST /login
{
    "username": "alumno_001",
    "password": "secure_pass"
}
# → {"status": "success", "user_id": 1, "token": "..."}

# Test 3: Chat autenticado
POST /chat con token
# → Funciona correctamente
```

**Checklist:**

- [ ] Test registro exitoso
- [ ] Test login exitoso
- [ ] Test chat con token
- [ ] Test threads por usuario

---

### Resultado esperado

✅ Sistema de usuarios completo  
✅ Autenticación segura (bcrypt)  
✅ Sesiones aisladas por usuario  
✅ Preparado para despliegue en servidor UO

---

## 📊 CONSIDERACIONES IMPORTANTES

### Timeline Recomendado

```
NOVIEMBRE 2024
├─ Semana 1-2: Etapa 1 (Memoria)
├─ Semana 3-4: Etapa 2 (Citaciones)

DICIEMBRE 2024
├─ Semana 1-2: Etapa 3 (OCR) - OPCIONAL
├─ Semana 3-4: Etapa 4 (Ollama)

ENERO 2025
├─ Semana 1-2: Etapa 5 (Usuarios)
├─ Semana 3-4: Testing + Buffer

FEBRERO 2025
├─ Semana 1-2: Presentación forum
├─ Semana 3-4: Despliegue servidor UO
```

### Priorización para Forum

**CRÍTICO (Debe estar listo):**

1. ✅ Etapa 0 - Refactorización (DONE)
2. 🔴 Etapa 2 - Citaciones (ALTA PRIORIDAD)
3. 🟡 Etapa 1 - Memoria (MEDIA PRIORIDAD)

**BONUS (Si hay tiempo):** 4. 🟢 Etapa 4 - Ollama (BUENO para demo) 5. 🟢 Etapa 3 - OCR (FEATURE bonus)

**POST-FORUM (Para servidor UO):** 6. Etapa 5 - Usuarios (ESENCIAL para producción)

### Dependencias Entre Etapas

```
Etapa 0 (Refactorización) ✅
    ↓
Etapa 1 (Memoria) 🔲
    ↓
Etapa 2 (Citaciones) 🔲
    ↓
Etapa 4 (Ollama) 🔲
    ↓
Etapa 5 (Usuarios) 🔲

Etapa 3 (OCR) - Independiente, puede hacerse en paralelo
```

### Checklist de Despliegue Final

Para que el sistema esté listo para servidor UO:

- [ ] Etapa 0: Refactorización ✅
- [ ] Etapa 1: Memoria Conversacional
- [ ] Etapa 2: Citación de Fuentes
- [ ] Etapa 4: Soberanía (Ollama)
- [ ] Etapa 5: Sistema de Usuarios
- [ ] Testing end-to-end
- [ ] Documentación completa
- [ ] Configuración de despliegue
- [ ] Backups y recuperación
- [ ] Monitoreo y logs

---

## 🎓 OBSERVACIONES FINALES

### Metodología

- **Incremental**: Cada etapa agrega valor
- **Testeable**: Cada etapa tiene tests claros
- **Reversible**: Cambios pueden deshacerse
- **Documentada**: Cada paso queda documentado

### Calidad

- No hacemos cambios sin tests
- Validamos con usuario (tutora) después de Etapa 1 y 2
- Pruebas en servidor real antes de forum

### Flexibilidad

- Si Etapa 1 o 3 toman más tiempo, podemos saltarlas para forum
- Etapa 2 es **no negociable** (rigor académico)
- Etapa 4 se puede hacer en paralelo con Etapa 5

---

**Fecha de inicio**: Noviembre 8, 2025  
**Próxima reunión**: Revisar progreso Etapa 1  
**Contacto para dudas**: [Integración con tutora]
