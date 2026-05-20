import uvicorn

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
from auth_manager import AuthManager


# Importamos la lógica del agente que ya funciona
from agent_brain import app # 'app' es el grafo compilado de LangGraph
from memory_manager import get_memory_manager

# --- 1. CONFIGURACIÓN DE FASTAPI ---
app_fastapi = FastAPI(
    title="Agentic RAG Chatbot API - Tesis UO",
    description="Backend para el chatbot de consulta histórica con LangGraph y Agentic RAG.",
    version="1.0.0"
)

# --- AUTENTICACIÓN ---
auth_manager = AuthManager()
security = HTTPBearer()

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


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    user_input: str
    thread_id: Optional[str] = None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    token = credentials.credentials
    user_id = auth_manager.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return user_id



# --- 3.5 ENDPOINT DE SALUD (Health Check) ---
@app_fastapi.get("/")
def health_check():
    return {"status": "ok"}

# --- 4. ENDPOINTS DE AUTENTICACIÓN ---
@app_fastapi.post("/register")
def register(req: RegisterRequest):
    result = auth_manager.register(req.username.strip(), req.email.strip(), req.password)
    if not result["success"]:
        if result["error"] == "missing_fields":
            raise HTTPException(status_code=400, detail="Completa todos los campos.")
        elif result["error"] == "username_exists":
            raise HTTPException(status_code=400, detail="El nombre de usuario ya existe.")
        elif result["error"] == "email_exists":
            raise HTTPException(status_code=400, detail="El email ya está registrado.")
        elif result["error"] == "db_error":
            raise HTTPException(status_code=500, detail="Error interno de base de datos.")
        else:
            raise HTTPException(status_code=400, detail="Error desconocido en el registro.")
    return {"status": "success", "message": "Usuario registrado correctamente"}

@app_fastapi.post("/login")
def login(req: LoginRequest):
    user_id = auth_manager.authenticate(req.username.strip(), req.password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = auth_manager.create_access_token(user_id)
    return {"status": "success", "user_id": user_id, "token": token}


# --- 5. RUTA PRINCIPAL DE CHAT (PROTEGIDA) ---
@app_fastapi.post("/chat")
def run_chat(request: ChatRequest, user_id: int = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Endpoint para enviar una pregunta al Agente LangGraph con memoria persistente.
    Soporta thread_id para mantener conversaciones entre sesiones.
    """
    user_prompt = request.user_input
    memory_mgr = get_memory_manager()
    # Crear o usar sesión existente
    if not request.thread_id:
        thread_id = memory_mgr.create_session(str(user_id))
    else:
        thread_id = request.thread_id
    # Obtener configuración para el thread
    config = memory_mgr.get_config_for_thread(thread_id)
    # CRÍTICO: Recuperar el estado anterior del checkpointer
    last_state = memory_mgr.get_last_state(thread_id)
    # Mezclar estado anterior con estado nuevo
    # LIMITAR historial a últimos 4 mensajes para evitar contaminación
    if last_state:
        full_history = last_state.get("chat_history", [])
        # Solo tomar los últimos 4 mensajes
        limited_history = full_history[-4:] if len(full_history) > 4 else full_history
        initial_state = {
            "input": user_prompt,
            "chat_history": limited_history,
            "context": ""
        }
    else:
        initial_state = {
            "input": user_prompt,
            "chat_history": [],
            "context": ""
        }
    try:
        final_state = app.invoke(initial_state, config=config)
        agent_response = final_state['chat_history'][-1].content
        return {
            "status": "success",
            "response": agent_response,
            "thread_id": thread_id,
            "agent_used_tool": True if final_state['context'] else False
        }
    except Exception as e:
        print(f"Error durante la ejecución del agente: {e}")
        return {
            "status": "error",
            "response": f"Lo siento, ocurrió un error en el servidor. Intente de nuevo.",
            "thread_id": thread_id,
            "error_detail": str(e)
        }

# --- 5. FUNCIÓN PARA CORRER EL SERVIDOR ---

if __name__ == "__main__":
    print("Iniciando servidor FastAPI...")
    uvicorn.run(app_fastapi, host="0.0.0.0", port=8000)
    print("Servidor detenido.")