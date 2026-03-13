import requests

BASE_URL = "http://localhost:8000"

# 1. Registro de usuario
r = requests.post(f"{BASE_URL}/register", json={
    "username": "usuario1",
    "email": "usuario1@dominio.com",
    "password": "clave_segura"
})
print("Registro usuario1:", r.status_code, r.json())

# 2. Login
r = requests.post(f"{BASE_URL}/login", json={
    "username": "usuario1",
    "password": "clave_segura"
})
print("Login usuario1:", r.status_code, r.json())
assert r.status_code == 200 and "token" in r.json(), "Login fallido"
token1 = r.json()["token"]

# 3. Chat autenticado
r = requests.post(f"{BASE_URL}/chat", json={"user_input": "Hola, ¿quién eres?"}, headers={"Authorization": f"Bearer {token1}"})
print("Chat usuario1:", r.status_code, r.json())
assert r.status_code == 200 and r.json()["status"] == "success", "Chat fallido"
thread_id1 = r.json()["thread_id"]

# 4. Segundo usuario
r = requests.post(f"{BASE_URL}/register", json={
    "username": "usuario2",
    "email": "usuario2@dominio.com",
    "password": "clave_segura2"
})
print("Registro usuario2:", r.status_code, r.json())
r = requests.post(f"{BASE_URL}/login", json={
    "username": "usuario2",
    "password": "clave_segura2"
})
print("Login usuario2:", r.status_code, r.json())
assert r.status_code == 200 and "token" in r.json(), "Login usuario2 fallido"
token2 = r.json()["token"]

# 5. Chat usuario2
r = requests.post(f"{BASE_URL}/chat", json={"user_input": "Hola, soy el usuario2"}, headers={"Authorization": f"Bearer {token2}"})
print("Chat usuario2:", r.status_code, r.json())
assert r.status_code == 200 and r.json()["status"] == "success", "Chat usuario2 fallido"
thread_id2 = r.json()["thread_id"]

# 6. Intento de acceso cruzado (usuario2 usando thread_id1)
r = requests.post(f"{BASE_URL}/chat", json={"user_input": "Intento acceder a otro thread","thread_id": thread_id1}, headers={"Authorization": f"Bearer {token2}"})
print("Acceso cruzado:", r.status_code, r.json())
# Esperamos que la memoria esté vacía o el sistema no devuelva historial ajeno
