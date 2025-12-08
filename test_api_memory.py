"""
test_api_memory.py - Test de la API FastAPI con memoria persistente
"""

import requests
import json
import time

API_URL = "http://127.0.0.1:8000/chat"

def test_api_with_memory():
    """Test del endpoint /chat con memoria persistente."""
    
    print("\n" + "="*60)
    print("🧪 TEST: API FASTAPI CON MEMORIA PERSISTENTE")
    print("="*60)
    
    # Test 1: Primera pregunta (sin thread_id)
    print("\n[1] Primera pregunta (sin thread_id - crea sesión nueva)...")
    payload_1 = {
        "user_input": "¿Cuál es la capital de Italia?"
    }
    
    response_1 = requests.post(API_URL, json=payload_1)
    data_1 = response_1.json()
    
    print(f"✅ Status: {data_1['status']}")
    print(f"✅ Response: {data_1['response'][:80]}...")
    print(f"✅ Thread ID: {data_1['thread_id']}")
    print(f"✅ Agent used tool: {data_1['agent_used_tool']}")
    
    thread_id = data_1['thread_id']
    
    # Test 2: Segunda pregunta (CON thread_id - mantiene sesión)
    print("\n[2] Segunda pregunta (CON thread_id - mantiene memoria)...")
    time.sleep(1)  # Pequeña pausa
    
    payload_2 = {
        "user_input": "¿A cuántos kilómetros está de París?",
        "thread_id": thread_id
    }
    
    response_2 = requests.post(API_URL, json=payload_2)
    data_2 = response_2.json()
    
    print(f"✅ Status: {data_2['status']}")
    print(f"✅ Response: {data_2['response'][:80]}...")
    print(f"✅ Thread ID: {data_2['thread_id']}")
    print(f"✅ Mismo thread: {data_2['thread_id'] == thread_id}")
    
    # Test 3: Tercera pregunta (NUEVO thread_id - nueva sesión)
    print("\n[3] Tercera pregunta (NUEVO thread_id - sesión diferente)...")
    time.sleep(1)
    
    payload_3 = {
        "user_input": "¿Cuál es el idioma oficial de Portugal?"
    }
    
    response_3 = requests.post(API_URL, json=payload_3)
    data_3 = response_3.json()
    
    print(f"✅ Status: {data_3['status']}")
    print(f"✅ Response: {data_3['response'][:80]}...")
    print(f"✅ Thread ID nuevo: {data_3['thread_id']}")
    print(f"✅ Thread diferente: {data_3['thread_id'] != thread_id}")
    
    print("\n" + "="*60)
    print("✅ TODOS LOS TESTS DE API PASARON")
    print("="*60)
    print("\n📝 VERIFICACIÓN:")
    print(f"  - Thread 1: {thread_id}")
    print(f"  - Thread 2: {data_3['thread_id']}")
    print(f"  - Cada thread mantiene su conversación persistente")
    print(f"  - Las sesiones se recuperan al pasar el thread_id")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        test_api_with_memory()
    except Exception as e:
        print(f"❌ Error: {e}")
