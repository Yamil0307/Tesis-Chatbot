"""
test_debug_memory.py - Debug detallado de la memoria con SqliteSaver
"""

from agent_brain import app
from memory_manager import get_memory_manager

def test_memory_debug():
    """Debug detallado del flujo de memoria."""
    
    print("\n" + "="*70)
    print("🔍 DEBUG: VERIFICAR CÓMO SQLITESAVER MANEJA EL ESTADO")
    print("="*70)
    
    memory_mgr = get_memory_manager()
    
    # Crear sesión
    thread_id = memory_mgr.create_session("debug_user")
    config = memory_mgr.get_config_for_thread(thread_id)
    
    print(f"\n📌 Thread ID: {thread_id}")
    print(f"📌 Config: {config}")
    
    # PRIMERA INVOCACIÓN
    print("\n" + "-"*70)
    print("[1] PRIMERA INVOCACIÓN")
    print("-"*70)
    
    # Recuperar estado anterior (será None la primera vez)
    last_state = memory_mgr.get_last_state(thread_id)
    print(f"Estado anterior guardado: {last_state}")
    
    initial_state_1 = {
        "input": "¿Cuál es mi nombre?",
        "chat_history": last_state.get("chat_history", []) if last_state else [],
        "context": ""
    }
    
    print(f"Estado inicial (antes): input='{initial_state_1['input']}', chat_history len={len(initial_state_1['chat_history'])}")
    
    result_1 = app.invoke(initial_state_1, config=config)
    
    print(f"Estado final (después):")
    print(f"  - input: {result_1['input']}")
    print(f"  - chat_history length: {len(result_1['chat_history'])}")
    print(f"  - chat_history[-1]: {result_1['chat_history'][-1].content[:60]}...")
    
    # SEGUNDA INVOCACIÓN - MISMO THREAD
    print("\n" + "-"*70)
    print("[2] SEGUNDA INVOCACIÓN (MISMO THREAD)")
    print("-"*70)
    
    # IMPORTANTE: Recuperar el estado anterior ANTES de invocar
    last_state = memory_mgr.get_last_state(thread_id)
    last_state_info = f'{len(last_state.get("chat_history", []))} mensajes' if last_state else 'Ninguno'
    print(f"Estado anterior guardado: {last_state_info}")
    
    initial_state_2 = {
        "input": "¿Qué acabas de decir?",
        "chat_history": last_state.get("chat_history", []) if last_state else [],
        "context": ""
    }
    
    print(f"Estado inicial (antes): input='{initial_state_2['input']}', chat_history len={len(initial_state_2['chat_history'])}")
    print(f"✅ Ahora recuperamos el historial del checkpointer")
    
    result_2 = app.invoke(initial_state_2, config=config)
    
    print(f"Estado final (después):")
    print(f"  - input: {result_2['input']}")
    print(f"  - chat_history length: {len(result_2['chat_history'])}")
    print(f"  - chat_history[-1]: {result_2['chat_history'][-1].content[:60]}...")
    
    # ANÁLISIS
    print("\n" + "="*70)
    print("✅ ANÁLISIS DE MEMORIA")
    print("="*70)
    print(f"Invocación 1: {len(result_1['chat_history'])} mensajes en historial")
    print(f"Invocación 2: {len(result_2['chat_history'])} mensajes en historial")
    
    if len(result_2['chat_history']) > len(result_1['chat_history']):
        print("✅ MEMORIA FUNCIONANDO - El historial creció")
        print("\nDetalle del historial en invocación 2:")
        for i, msg in enumerate(result_2['chat_history']):
            print(f"  [{i}] {type(msg).__name__}: {msg.content[:50]}...")
    else:
        print("❌ MEMORIA NO FUNCIONA - El historial no creció")

if __name__ == "__main__":
    test_memory_debug()

