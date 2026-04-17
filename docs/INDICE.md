# 📋 RESUMEN DEL PROYECTO

**Proyecto**: Chatbot Agentic RAG para Consulta de Documentos Históricos  
**Institución**: Universidad de Oriente  
**Tipo**: Tesis de grado

---

## 🎯 Objetivo

Desarrollar un chatbot conversacional basado en metodologías Agentic RAG para permitir consultas sobre los documentos históricos y patrimoniales de la Universidad de Oriente.

---

## 📊 Estado del Proyecto

| Componente | Estado | Descripción |
|------------|--------|-------------|
| Backend (FastAPI) | ✅ Completo | API REST en puerto 8000 |
| Agentic RAG | ✅ Completo | LangGraph con 3 nodos |
| Memoria Conversacional | ✅ Completo | Persistencia por sesión |
| Citación de Fuentes | ✅ Completo | Formato académico |
| Anti-Hallucination | ✅ Completo | Temp 0.0 + restricciones |
| OCR | ✅ Completo | Mistral OCR API |
| Frontend | ✅ Completo | Diseño UO pantalla completa |
| Sistema de Usuarios | 🔶 Parcial | Login/registro básico |

**Progreso total**: ~85-90%

---

## 📚 Documentación del Proyecto

### Documentos Generales
| Documento | Descripción |
|-----------|-------------|
| `ESTADO_PROYECTO.md` | Estado general completo del proyecto |
| `INDICE.md` | Este índice general |

### Etapas Completadas
| Documento | Descripción |
|-----------|-------------|
| `ETAPA_0_COMPLETADA.md` | Refactorización modular |
| `ETAPA_1_COMPLETADA.md` | Memoria conversacional |
| `ETAPA_2_CORRECCIONES_INICIALES.md` | Correcciones iniciales |
| `ETAPA_2_ANTI_ALUCINACION.md` | Sistema anti-alucinación |
| `ETAPA_2_MEJORA_INGESTION.md` | Resúmenes automáticos |
| `ETAPA_3_COMPLETADA.md` | OCR avanzado (Mistral) + carpeta |
| `ETAPA_5_COMPLETADA.md` | Sistema multi-usuario |

### Etapas Pendientes
| Documento | Descripción |
|-----------|-------------|
| `ETAPA_4_PLAN.md` | Ollama (soberanía offline) |

### Documentos Históricos
| Documento | Descripción |
|-----------|-------------|
| `OPCIONES_MEMORIA.md` | Decisiones de arquitectura (histórico) |

---

## 🏗️ Arquitectura

```
Usuario → Frontend (HTML/JS) → FastAPI → Agent (LangGraph) → FAISS
                                              ↓
                                    memory_manager (SQLite)
```

---

## 🚀 Guía de Uso

### Iniciar el Servidor
```bash
python main.py
```

### Acceder al Chat
```
http://localhost:8000
```

### Cargar Documentos
```bash
python ingest_data.py
```

---

## 📁 Estructura de Archivos

```
Tesis_Agentic_RAG/
├── main.py                    # FastAPI entry point
├── agent_brain.py             # Agent LangGraph
├── rag_manager.py             # FAISS + RAG
├── memory_manager.py         # Persistencia
├── auth_manager.py           # Autenticación JWT
├── metadata_handler.py       # Citas académicas
├── ingest_*.py              # Pipeline de ingestión
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── styles.css
├── docs/                    # Documentación
├── data/                     # PDFs a procesar
├── vectorstore_faiss/        # Índice FAISS
├── checkpoints.db           # Memoria LangGraph
└── users.db                  # Usuarios
```

---

## 🔧 Tecnologías

- **Backend**: FastAPI + Uvicorn
- **Agent**: LangGraph
- **LLM**: Google Gemini (gemma-3-4b-it)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Vector DB**: FAISS
- **Auth**: JWT + bcrypt
- **OCR**: Mistral OCR API

---

## 📞 Soporte

Para dudas o problemas, consultar la documentación específica de cada etapa en `docs/`.

---

**Universidad de Oriente** - Santiago de Cuba  
**Última actualización**: Abril 2026