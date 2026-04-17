# 🚀 ETAPA 4: SOBERANÍA TOTAL (OLLAMA) - PLAN

**Fecha**: Abril 2026  
**Estado**: ❌ **PENDIENTE**  
**Objetivo**: Implementar LLM local para independencia de internet  

---

## 🎯 OBJETIVO

Sustituir el LLM externo (Google Gemini) por un modelo local (Ollama) para permitir que el sistema funcione sin conexión a internet, requisito importante para el despliegue en el servidor de la Universidad de Oriente.

---

## 📋 REQUISITOS

### Hardware mínimo (servidor UO)
- **RAM**: 8 GB mínimo, 16 GB recomendado
- **ESPACIO**: 4-8 GB para modelo
- **GPU**: Opcional pero recomendado (acelera inferencia)

### Software
- **Ollama**: https://ollama.ai
- **Modelo**: llama3:8b o mistral:7b

---

## 🎯 TAREA 4.1: INSTALACIÓN DE OLLAMA

### Instalación en servidor

```bash
# Descargar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar modelo
ollama pull llama3:8b
# o
ollama pull mistral:7b

# Verificar
ollama list
```

### Verificación esperada

```
NAME           MODEL              ID          SIZE      MODIFIED
llama3:8b    65c2e18f7d7e    4.7GB     2 minutes ago
```

---

## 🎯 TAREA 4.2: INTEGRAR OLLAMA EN AGENT_BRAIN.PY

### Cambio de LLM

**ANTES (Gemini)**:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(
    model="gemma-3-4b-it",
    temperature=0.0
)
```

**DESPUÉS (Ollama)**:
```python
from langchain_ollama import ChatOllama
llm = ChatOllama(
    model="llama3:8b",
    temperature=0.0,
    base_url="http://localhost:11434"
)
```

### Checklist
- [ ] Instalar Ollama en servidor
- [ ] Descargar modelo
- [ ] Actualizar imports en agent_brain.py
- [ ] Cambiar inicialización de LLM
- [ ] Test de integración

---

## 🎯 TAREA 4.3: CONFIG.PY (MULTI-PROVEEDOR)

### Objetivo
Permitir cambiar entre Gemini y Ollama fácilmente.

```python
# config.py
class LLMConfig:
    PROVIDERS = {
        "gemini": {
            "class": "ChatGoogleGenerativeAI",
            "model": "gemma-3-4b-it"
        },
        "ollama": {
            "class": "ChatOllama",
            "model": "llama3:8b",
            "base_url": "http://localhost:11434"
        }
    }
    
    @staticmethod
    def get_llm(provider="gemini"):
        # Cargar según provider
```

### Checklist
- [ ] Crear config.py
- [ ] Implementar switch de provider
- [ ] Test con ambos providers

---

## 📊 COMPARATIVA

| Aspecto | Gemini | Ollama |
|--------|-------|-------|
| **Internet** | Requiere | No |
| **Calidad** | Alta | Media-Alta |
| **Velocidad** | variable | variable |
| **Costo** | API | Hardware |
| **Privacidad** | Parcial | Total |

---

## ⚠️ CONSIDERACIONES

### Para el Forum
- **NO es crítico**: El sistema actual con Gemini funciona bien
- **Recomendación**: Mantener Gemini para demo, agregar Ollama después

### Para producción UO
- **CRÍTICO**: Ollama permite funcionar offline
- **Post-forum**: Implementar y desplegar

---

## 📝 ARCHIVOS A MODIFICAR

| Archivo | Cambio |
|---------|--------|
| `agent_brain.py` | Cambiar LLM (2 líneas) |
| `config.py` | ✅ Crear (nuevo) |

---

## ✅ CRITERIOS DE ÉXITO

- [ ] Ollama responde sin internet
- [ ]-agent_brain.py funciona con Ollama
- [ ] Calidad de respuestas aceptable
- [ ] Sistema completamente offline

---

## 🔲 ETAPA ANTERIOR

**Etapa 3**: OCR Avanzado ✅ (completada)

---

## 🔲 SIGUIENTE ETAPA

**Etapa 5**: Sistema de Usuarios (partial) → Admin, Perfiles

---

**Status**: ❌ PENDIENTE  
**Prioridad**: Baja (para después del forum)