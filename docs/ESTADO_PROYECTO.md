# 📊 ESTADO DEL PROYECTO - Tesis Agentic RAG

**Universidad de Oriente** - Chatbot Agentic RAG para Consulta de Fondos Patrimoniales  
**Última actualización**: Abril 2026  
**Estado**: 🟢 EN DESARROLLO ACTIVO

---

## 📋 TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Estado de Etapas](#estado-de-etapas)
4. [Stack Tecnológico](#stack-tecnológico)
5. [Base de Conocimiento](#base-de-conocimiento)
6. [Frontend](#frontend)
7. [API Endpoints](#api-endpoints)
8. [Pendiente](#pendiente)
9. [Próximos Pasos](#próximos-pasos)

---

## 🎯 RESUMEN EJECUTIVO

**Objetivo**: Chatbot conversacional con metodología Agentic RAG paraConsulta de documentos históricos de la Universidad de Oriente.

**Características principales**:
- Agentic RAG con LangGraph (3 nodos: contextualize → search → respond)
- Memoria conversacional persistente por sesión
- Citación académica de fuentes
- Anti-hallucination robusto
- OCR para documentos escaneados
- Sistema multi-usuario básico

**Estado general**: ~85-90% completo

---

## 🏗️ ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (HTML/JS/CSS)                      │
│              Diseño a pantalla completa                      │
│            Colores: Azul UO #00308F, Rojo UO #C81F1F         │
└──────────────────────────────┬────────────────────────────────┘
                               │ HTTP JSON
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│                       Puerto: 8000                                 │
└──────────────────────────────┬────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
│   Auth Manager    │  │Memory Manager│  │  Agent Brain     │
│  (JWT + bcrypt)  │  │(SqliteSaver) │  │  (LangGraph)     │
└──────────────────┘  └──────────────┘  └──────────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  FAISS      │  │  SQLite      │  │  LangGraph Checkpoints│  │
│  │ (vectores)  │  │ (usuarios)  │  │    (memoria)         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📑 ESTADO DE ETAPAS

| Etapa | Estado | Descripción | Prioridad Forum |
|------|--------|-------------|---------------|
| **Etapa 0** | ✅ | Refactorización modular | Media |
| **Etapa 1** | ✅ | Memoria conversacional | Alta |
| **Etapa 2** | ✅ | Citación de fuentes | Alta |
| **Etapa 3** | ✅ | OCR avanzado | Media |
| **Etapa 4** | ❌ | Ollama (soberanía) | Baja |
| **Etapa 5** | 🔶 | Sistema multi-usuario (básico) | Media |
| **Frontend** | ✅ | Diseño UO | Alta |

### Detalle de Etapas Completadas

#### ✅ Etapa 0: Refactorización Estructural
- Módulos separados: rag_manager, metadata_handler, ingest_pdf, ingest_utils
- Código modular y escalable

#### ✅ Etapa 1: Memoria Conversacional
- SqliteSaver de LangGraph
- checkpoints.db para persistencia
- thread_id por sesión de usuario
- Recuperación de estado entre invocaciones

#### ✅ Etapa 2: Citación de Fuentes
- Metadatos enriquecidos (page, file_name, chunk_index, summary)
- Resúmenes AI automáticos para mejor embedding
- Formato académico "FUENTES CONSULTADAS:"
- Anti-hallucination:
  - Temperatura 0.0
  - Búsqueda obligatoria
  - System prompt con prohibiciones explícitas

#### ✅ Etapa 3: OCR Avanzado
- Mistral OCR API (mistral-ocr-latest)
- Soporte para imágenes escaneadas

#### 🔶 Etapa 5: Sistema de Usuarios (PARCIAL)
- Registro de usuarios ✅
- Login con JWT ✅
-bcrypt password hashing ✅
- Sesiones por usuario ✅
- Sin perfil de usuario ❌
- Sin cambio de contraseña ❌

---

## 🛠️ STACK TECNOLÓGICO

| Capa | Tecnología |
|------|-----------|
| **Backend** | FastAPI + Uvicorn |
| **Agent** | LangGraph (StateGraph) |
| **LLM** | Google Gemini (gemma-3-4b-it) |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 |
| **Vector DB** | FAISS (local) |
| **Memory** | SqliteSaver (LangGraph) |
| **Auth** | JWT + bcrypt |
| **OCR** | Mistral OCR API |
| **Frontend** | Vanilla JS + CSS3 |

---

## 📚 BASE DE CONOCIMIENTO

**Archivos cargados en FAISS**:
- `data/info_prueba.pdf`
- `data/documento_tesis.pdf`

**Metadatos por chunk**:
- source (ruta del archivo)
- page (número de página)
- file_name
- chunk_index
- processed_date
- summary (resumen IA)

**Estrategia de recuperación**:
- MMR (Maximal Marginal Relevance) con λ=0.6
- k=40 resultados
- Priorización de páginas 1-5 (portadas)

---

## 💻 FRONTEND

**Diseño**: Pantalla completa con dos paneles

### Pantalla de Login/Registro
- Dos columnas: info institucional + formulario
- Colores: Azul UO (#00308F) / Rojo UO (#C81F1F)

### Pantalla Principal (Chat)
- Sidebar izquierda: Información de la Universidad de Oriente
- Área derecha: Chat con mensajes
- Estado de conexión en tiempo real
- Dropdown de fuentes consultadas

### Funcionalidades
- Login/Registro
- Persistencia de sesión (localStorage)
- thread_id por conversación
- Spinner de carga
- Fuentes en dropdown

---

## 🔌 API ENDPOINTS

| Endpoint | Método | Descripción | Auth |
|----------|--------|------------|------|
| `/` | GET | Health check | ❌ |
| `/register` | POST | Registrar usuario | ❌ |
| `/login` | POST | Login → JWT token | ❌ |
| `/chat` | POST | Enviar mensaje al agente | ✅ JWT |

### Formato de `/chat`

**Request**:
```json
{
  "user_input": "¿Cuándo se fundó la UO?",
  "thread_id": "user_1_20250417_001"
}
```

**Response**:
```json
{
  "status": "success",
  "response": "La Universidad de Oriente fue fundada en 1968...",
  "thread_id": "user_1_20250417_001",
  "agent_used_tool": true
}
```

---

## 🔲 PENDIENTE

### Alto Prioridad (para Forum)
- [ ] Testing integral del sistema
- [ ] Documentación técnica
- [ ] Slides de presentación

### Media Prioridad (Post-Forum)
- [ ] Perfil de usuario
- [ ] Cambio de contraseña
- [ ] Sistema de admin
- [ ] Recuperación de contraseña

### Bajo Prioridad
- [ ] Ollama (independencia offline)
- [ ] Rate limiting
- [ ] PostgreSQL para producción

---

## 🚀 PRÓXIMOS PASOS

1. **Testing**: Verificar que todo el sistema funcione integrado
2. **Documentación**: Redactar memoria y documentación técnica
3. **Presentación**: Preparar slides para el forum
4. **Correcciones**: Ajustes basados en testing

---

## 📁 ESTRUCTURA DE ARCHIVOS

```
Tesis_Agentic_RAG/
├── main.py                      # FastAPI entry point
├── agent_brain.py               # Agent LangGraph
├── rag_manager.py              # FAISS + RAG
├── memory_manager.py           # Persistencia
├── auth_manager.py            # Auth JWT
├── metadata_handler.py        # Citas
├── ingest_*.py               # Pipeline ingestión
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── styles.css
├── docs/
│   ├── PLAN_DE_TRABAJO.md
│   ├── ETAPA_1_COMPLETADA.md
│   ├── ETAPA_2_*.md
│   └── OPCIONES_MEMORIA.md
├── data/
│   ├── info_prueba.pdf
│   └── documento_tesis.pdf
├── vectorstore_faiss/        # Índice FAISS
├── checkpoints.db           # Memoria LangGraph
└── users.db                 # Usuarios
```

---

**Estado**: 🟢 Desarrollo activo - ~85-90% completo

**Última actualización**: Abril 2026