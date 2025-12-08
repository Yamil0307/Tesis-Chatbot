import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

# Importamos la lógica del agente que ya funciona
from agent_brain import app # 'app' es el grafo compilado de LangGraph

# --- 1. CONFIGURACIÓN DE FASTAPI ---
app_fastapi = FastAPI(
    title="Agentic RAG Chatbot API - Tesis UO",
    description="Backend para el chatbot de consulta histórica con LangGraph y Agentic RAG.",
    version="1.0.0"
)

# 2. Configuración CORS
# Esto es esencial para que tu frontend (HTML/JS) pueda llamar al backend (FastAPI)
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:5500" # Puerto común para VS Code Live Server
    # Puedes añadir la IP del servidor de la universidad aquí en el futuro
]

app_fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Por ahora, permitimos todos para el desarrollo fácil
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 3. MODELO DE DATOS (Lo que envía el usuario) ---
class ChatRequest(BaseModel):
    """Modelo de la solicitud de chat."""
    user_input: str

# --- 4. RUTA PRINCIPAL DE CHAT ---

@app_fastapi.post("/chat")
def run_chat(request: ChatRequest) -> Dict[str, Any]:
    """
    Endpoint para enviar una pregunta al Agente LangGraph y recibir una respuesta.
    """
    
    user_prompt = request.user_input
    
    # El estado inicial debe incluir 'context' y 'chat_history'
    initial_state = {
        "input": user_prompt, 
        "chat_history": [],
        "context": ""
    }
    
    try:
        # Invoca el agente de LangGraph
        final_state = app.invoke(initial_state)
        
        # Extrae la respuesta del agente (es el último elemento del historial)
        agent_response = final_state['chat_history'][-1].content
        
        return {
            "status": "success",
            "response": agent_response,
            "agent_used_tool": True if final_state['context'] else False
        }

    except Exception as e:
        print(f"Error durante la ejecución del agente: {e}")
        return {
            "status": "error",
            "response": f"Lo siento, ocurrió un error en el servidor. Intente de nuevo.",
            "error_detail": str(e)
        }

# --- 5. FUNCIÓN PARA CORRER EL SERVIDOR ---

if __name__ == "__main__":
    print("Iniciando servidor FastAPI...")
    uvicorn.run(app_fastapi, host="0.0.0.0", port=8000)
    print("Servidor detenido.")