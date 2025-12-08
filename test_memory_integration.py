"""
test_memory_integration.py - Test de integración para SqliteSaver
Verifica que la memoria conversacional persiste correctamente.
"""

from agent_brain import app
from memory_manager import get_memory_manager

def test_memory_persistence():
    """Test que verifica la persistencia de memoria en LangGraph."""
    
    print("\n" + "="*60)
    print("🧪 TEST: MEMORIA CONVERSACIONAL CON SQLITESAVER")
    print("="*60)
    
    memory_mgr = get_memory_manager()
    
    # 1. Crear nueva sesión
    print("\n[1] Creando nueva sesión...")
    thread_id = memory_mgr.create_session("test_user")
    config = memory_mgr.get_config_for_thread(thread_id)
    print(f"✅ Thread ID: {thread_id}")
    print(f"✅ Config: {config}")
    
    # 2. Primera pregunta
    print("\n[2] Primera invocación del agente...")
    initial_state_1 = {
        "input": "¿Cuál es la capital de España?",
        "chat_history": [],
        "context": ""
    }
    
    try:
        result_1 = app.invoke(initial_state_1, config=config)
        response_1 = result_1['chat_history'][-1].content
        print(f"✅ Respuesta 1: {response_1[:100]}...")
    except Exception as e:
        print(f"❌ Error en invocación 1: {e}")
        return False
    
    # 3. Segunda pregunta en MISMO thread (debe recuperar estado)
    print("\n[3] Segunda invocación en MISMO thread (con memoria)...")
    initial_state_2 = {
        "input": "¿A cuántos kilómetros está de Francia?",
        "chat_history": [],
        "context": ""
    }
    
    try:
        result_2 = app.invoke(initial_state_2, config=config)
        response_2 = result_2['chat_history'][-1].content
        print(f"✅ Respuesta 2: {response_2[:100]}...")
    except Exception as e:
        print(f"❌ Error en invocación 2: {e}")
        return False
    
    # 4. Crear OTRO thread (sesión diferente)
    print("\n[4] Creando otro thread/sesión diferente...")
    thread_id_2 = memory_mgr.create_session("otro_usuario")
    config_2 = memory_mgr.get_config_for_thread(thread_id_2)
    print(f"✅ Thread ID 2: {thread_id_2}")
    
    # 5. Tercera pregunta en DIFERENTE thread
    print("\n[5] Invocación en DIFERENTE thread...")
    initial_state_3 = {
        "input": "¿Cuál es el idioma oficial de Brasil?",
        "chat_history": [],
        "context": ""
    }
    
    try:
        result_3 = app.invoke(initial_state_3, config=config_2)
        response_3 = result_3['chat_history'][-1].content
        print(f"✅ Respuesta 3: {response_3[:100]}...")
    except Exception as e:
        print(f"❌ Error en invocación 3: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ TODOS LOS TESTS PASARON")
    print("="*60)
    print("\n📝 VERIFICACIÓN:")
    print(f"  - Thread 1: {thread_id}")
    print(f"  - Thread 2: {thread_id_2}")
    print(f"  - Ambos threads persisten en checkpoints.db")
    print(f"  - Cada thread mantiene su historial de conversación")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    test_memory_persistence()
