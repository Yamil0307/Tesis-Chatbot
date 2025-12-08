"""
test_final_memory.py - Test final de memoria con contexto completo
Verifica que el modelo recibe el historial de conversación anterior
"""

from agent_brain import app
from memory_manager import get_memory_manager

def test_memory_with_context():
    """Test que verifica la memoria CON contexto para el modelo."""
    
    print("\n" + "="*70)
    print("🧪 TEST FINAL: MEMORIA CON CONTEXTO PARA EL MODELO")
    print("="*70)
    
    memory_mgr = get_memory_manager()
    
    # Crear nueva sesión
    thread_id = memory_mgr.create_session("context_test")
    config = memory_mgr.get_config_for_thread(thread_id)
    
    print(f"\n📌 Thread ID: {thread_id}")
    
    # PREGUNTA 1: Decirle mi nombre
    print("\n" + "-"*70)
    print("[1] PREGUNTA 1: Decir nombre")
    print("-"*70)
    
    last_state = memory_mgr.get_last_state(thread_id)
    initial_state_1 = {
        "input": "Mi nombre es Juan García",
        "chat_history": last_state.get("chat_history", []) if last_state else [],
        "context": ""
    }
    
    result_1 = app.invoke(initial_state_1, config=config)
    response_1 = result_1['chat_history'][-1].content
    print(f"Usuario: {initial_state_1['input']}")
    print(f"Bot: {response_1}\n")
    print(f"Historial size: {len(result_1['chat_history'])} mensajes")
    
    # PREGUNTA 2: Preguntarle si recuerda el nombre
    print("\n" + "-"*70)
    print("[2] PREGUNTA 2: Preguntar si recuerda el nombre")
    print("-"*70)
    
    last_state = memory_mgr.get_last_state(thread_id)
    initial_state_2 = {
        "input": "¿Cuál es mi nombre?",
        "chat_history": last_state.get("chat_history", []) if last_state else [],
        "context": ""
    }
    
    result_2 = app.invoke(initial_state_2, config=config)
    response_2 = result_2['chat_history'][-1].content
    print(f"Usuario: {initial_state_2['input']}")
    print(f"Bot: {response_2}\n")
    print(f"Historial size: {len(result_2['chat_history'])} mensajes")
    
    # PREGUNTA 3: Pregunta adicional para verificar contexto completo
    print("\n" + "-"*70)
    print("[3] PREGUNTA 3: Pregunta que requiere historial completo")
    print("-"*70)
    
    last_state = memory_mgr.get_last_state(thread_id)
    initial_state_3 = {
        "input": "¿Quién soy?",
        "chat_history": last_state.get("chat_history", []) if last_state else [],
        "context": ""
    }
    
    result_3 = app.invoke(initial_state_3, config=config)
    response_3 = result_3['chat_history'][-1].content
    print(f"Usuario: {initial_state_3['input']}")
    print(f"Bot: {response_3}\n")
    print(f"Historial size: {len(result_3['chat_history'])} mensajes")
    
    # ANÁLISIS
    print("\n" + "="*70)
    print("✅ VERIFICACIÓN FINAL")
    print("="*70)
    
    # Verificar si el modelo menciona el nombre
    if "Juan" in response_2 or "juan" in response_2.lower():
        print("✅ CORRECTO: El modelo RECUERDA el nombre (Juan)")
    else:
        print("❌ PROBLEMA: El modelo NO recuerda el nombre")
        print(f"   Respuesta: {response_2}")
    
    # Verificar si el modelo sabe quién es
    if "Juan" in response_3 or "juan" in response_3.lower() or "García" in response_3:
        print("✅ CORRECTO: El modelo SABE quién es el usuario")
    else:
        print("❌ PROBLEMA: El modelo NO sabe quién es el usuario")
        print(f"   Respuesta: {response_3}")
    
    # Historial
    print(f"\n📝 Historial completo ({len(result_3['chat_history'])} mensajes):")
    for i, msg in enumerate(result_3['chat_history']):
        role = "Usuario" if hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage' else "Bot"
        preview = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
        print(f"  [{i}] {role}: {preview}")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    test_memory_with_context()
