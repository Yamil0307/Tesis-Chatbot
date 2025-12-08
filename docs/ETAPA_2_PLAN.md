# 🚀 ETAPA 2: CITACIÓN DE FUENTES - PLAN DE IMPLEMENTACIÓN

**Fecha**: Diciembre 8, 2025  
**Estado**: 🔄 EN PROGRESO  
**Criticidad**: 🔴 ALTA (rigor académico para forum)  
**Dependencias**: Etapa 1 ✅

---

## 📋 OBJETIVO

Implementar citaciones académicas formales en respuestas, mostrando:
- Nombre del documento consultado
- Página específica donde se encontró la información
- Formato académico profesional

**Por qué es crítico para el forum:**
- Demuestra rigor académico
- Valida que la información viene de documentos reales
- Requisito para presentación profesional

---

## 🎯 TAREAS A COMPLETAR (4)

### Tarea 2.1: Enriquecer metadatos en ingest_pdf.py
**Objetivo**: Asegurar que cada fragmento de documento tenga página y información completa  
**Archivo**: `ingest_pdf.py`  
**Líneas estimadas**: +15

```python
# ANTES - Metadatos básicos
metadata = {
    "source": pdf_path,
    "page": 0
}

# DESPUÉS - Metadatos completos
metadata = {
    "source": pdf_path,
    "page": doc.metadata.get("page", 0),  # ← Página actual
    "chunk_index": idx,                    # ← Índice de fragmento
    "file_name": os.path.basename(pdf_path),  # ← Nombre archivo
    "processed_date": datetime.now().isoformat()  # ← Cuándo se procesó
}
```

**Checklist**:
- [ ] Actualizar `process_documents()` para agregar metadatos
- [ ] Verificar que FAISS recupera metadatos
- [ ] Test: Buscar documento y verificar page/file_name

**Impacto**: Permite extraer información de página en respuestas

---

### Tarea 2.2: Usar MetadataHandler en search_university_history
**Objetivo**: Extraer y formatear metadatos al buscar  
**Archivo**: `agent_brain.py`  
**Líneas estimadas**: +20

```python
# ANTES - Solo contexto
@tool
def search_university_history(query: str) -> str:
    docs = rag_mgr.search(query, k=4)
    context = rag_mgr.format_context(docs)
    return context

# DESPUÉS - Contexto + fuentes
@tool
def search_university_history(query: str) -> str:
    docs = rag_mgr.search(query, k=4)
    context = rag_mgr.format_context(docs)
    
    # Extraer fuentes
    sources_info = []
    for doc in docs:
        metadata = MetadataHandler.extract_source_info(doc)
        sources_info.append(metadata)
    
    # Incluir fuentes en retorno
    sources_text = MetadataHandler.format_source_list(docs)
    return f"{context}\n\n{sources_text}"
```

**Checklist**:
- [ ] Importar MetadataHandler en agent_brain.py
- [ ] Usar `extract_source_info()` para cada documento
- [ ] Usar `format_source_list()` para formatear
- [ ] Test: Buscar y verificar que retorna fuentes

**Impacto**: Fuentes se incluyen en el contexto que recibe el LLM

---

### Tarea 2.3: Actualizar generate_response para formato académico
**Objetivo**: Instruir al LLM a generar respuesta + citaciones  
**Archivo**: `agent_brain.py`  
**Líneas estimadas**: +25

```python
# ANTES - Sin instrucción de fuentes
system_prompt = "Eres un chatbot experto..."

# DESPUÉS - Con instrucción de citaciones
system_prompt = (
    "Eres un chatbot experto en la Universidad de Oriente.\n"
    "IMPORTANTE - Instrucciones de citación:\n"
    "1. En tu respuesta, cita información de los documentos\n"
    "2. Al final, incluye sección: FUENTES CONSULTADAS:\n"
    "3. Formato: '- [Documento] (página X)'\n"
    "4. Si usaste RAG, SIEMPRE incluye fuentes\n"
    "5. Si respondiste sin RAG, indica: '(Conocimiento general)'\n"
    "\n--- CONTEXTO ---\n"
    f"{context}"
)
```

**Checklist**:
- [ ] Actualizar system_prompt con instrucciones de citación
- [ ] Agregar lógica para incluir "Conocimiento general" cuando no hay RAG
- [ ] Test: Respuesta incluye "FUENTES CONSULTADAS:"

**Impacto**: LLM generará respuestas formateadas con citaciones

---

### Tarea 2.4: Actualizar frontend para mostrar fuentes estilizadas
**Objetivo**: Mostrar fuentes visualmente separadas en interfaz  
**Archivo**: `frontend/script.js` y `frontend/styles.css`  
**Líneas estimadas**: +30 (JS) + +20 (CSS)

```javascript
// ANTES - Texto plano
addMessage(data.response, "bot")

// DESPUÉS - Separar contenido de fuentes
function addMessage(text, sender, isRag = false) {
    const parts = text.split("FUENTES CONSULTADAS:");
    const response = parts[0].trim();
    const sources = parts[1] ? parts[1].trim() : null;
    
    let content = response.replace(/\n/g, "<br>");
    
    if (sources) {
        content += `
            <div class="sources-section">
                <h4>📚 FUENTES CONSULTADAS:</h4>
                <ul class="sources-list">
                    ${sources.split("\n")
                        .filter(s => s.trim().startsWith("-"))
                        .map(s => `<li>${s.substring(1).trim()}</li>`)
                        .join("")}
                </ul>
            </div>
        `;
    } else if (sender === "bot") {
        content += `<div class="sources-section"><p>📖 Respuesta basada en conocimiento general</p></div>`;
    }
    
    messageDiv.innerHTML = content;
    chatMessages.appendChild(messageDiv);
}
```

```css
/* styles.css */
.sources-section {
    margin-top: 15px;
    padding: 12px;
    background-color: #f8f9fa;
    border-left: 4px solid #007bff;
    border-radius: 4px;
    font-size: 0.9em;
}

.sources-section h4 {
    margin: 0 0 8px 0;
    color: #0056b3;
    font-weight: 600;
}

.sources-list {
    margin: 0;
    padding-left: 20px;
    list-style-type: none;
}

.sources-list li {
    margin: 4px 0;
    color: #555;
    padding-left: 20px;
    position: relative;
}

.sources-list li:before {
    content: "📄";
    position: absolute;
    left: 0;
}
```

**Checklist**:
- [ ] Actualizar `addMessage()` para parsear "FUENTES CONSULTADAS:"
- [ ] Crear estilos CSS para `.sources-section`
- [ ] Mostrar lista de fuentes formateada
- [ ] Test: Fuentes se muestran visualmente en chat

**Impacto**: Usuarios ven claramente de dónde viene la información

---

## 📊 RESUMEN DE CAMBIOS

| Archivo | Cambios | Complejidad |
|---------|---------|------------|
| ingest_pdf.py | +15 líneas | ⭐ Fácil |
| agent_brain.py | +45 líneas | ⭐⭐ Media |
| script.js | +30 líneas | ⭐⭐ Media |
| styles.css | +20 líneas | ⭐ Fácil |
| **TOTAL** | **~110 líneas** | **⭐⭐ Media** |

**Tiempo estimado**: 1-2 horas

---

## 🧪 TESTING PLAN

### Test 1: Metadatos en FAISS
```python
# test_metadata_enrichment.py
rag_mgr = get_rag_manager()
docs = rag_mgr.search("historia universidad", k=1)
assert docs[0].metadata["file_name"] != None
assert docs[0].metadata["page"] >= 0
```

### Test 2: Búsqueda retorna fuentes
```python
# test_sources_in_search.py
result = search_university_history("¿Cuándo se fundó?")
assert "FUENTES CONSULTADAS:" in result or "fuentes" in result.lower()
assert "[" in result  # Tiene nombre de documento
assert "página" in result.lower() or "pag" in result.lower()
```

### Test 3: Frontend parsea fuentes
```javascript
// En browser console
// Hacer pregunta que usa RAG
// Verificar que hay div.sources-section
// Verificar que hay lista de documentos
```

---

## 🔄 ORDEN DE IMPLEMENTACIÓN

1. **2.1 - Enriquecer metadatos** (fácil, sin dependencias)
2. **2.2 - search_university_history** (depende de 2.1)
3. **2.3 - generate_response** (independiente)
4. **2.4 - Frontend** (depende de 2.3)

---

## ✅ CRITERIOS DE ÉXITO

- ✅ Metadatos incluyen página y nombre archivo
- ✅ RAG retorna contexto + fuentes
- ✅ LLM genera respuesta con citaciones académicas
- ✅ Frontend muestra fuentes visualmente
- ✅ Formato: "- [Documento] (página X)"
- ✅ Tests unitarios pasados
- ✅ Presentable en forum

---

## 📝 NOTAS

### Formato de Citación
```
FUENTES CONSULTADAS:
- Historia de la Universidad de Oriente (página 42)
- Reglamento Académico 2023 (página 15)
- Informe Anual 2024 (página 8)
```

### Casos Especiales
1. **Sin RAG**: Indicar "(Conocimiento general)"
2. **Múltiples fuentes**: Listar todas
3. **Misma fuente, diferentes páginas**: "- [Doc] (páginas 15, 42)"

---

¿Comenzamos con la implementación?
