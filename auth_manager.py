import sqlite3
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt

# Configuración de seguridad
SECRET_KEY = "CAMBIA_ESTA_CLAVE_POR_UNA_SECRETA"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class AuthManager:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    jwt_token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def register(self, username: str, email: str, password: str) -> bool:
        if not username or not email or not password:
            return False
        password_hash = self.pwd_context.hash(password)
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, password_hash)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate(self, username: str, password: str) -> Optional[int]:
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, password_hash FROM users WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
        if result and self.pwd_context.verify(password, result[1]):
            return result[0]
        return None

    def create_access_token(self, user_id: int) -> str:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {"sub": str(user_id), "exp": expire}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        # Guardar token en sesiones activas
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (user_id, jwt_token) VALUES (?, ?)",
                (user_id, token)
            )
            conn.commit()
        return token

    def verify_token(self, token: str) -> Optional[int]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = int(payload.get("sub"))
            # Verificar que el token esté en la tabla de sesiones
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM sessions WHERE user_id = ? AND jwt_token = ?",
                    (user_id, token)
                )
                result = cursor.fetchone()
            if result:
                return user_id
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Exception):
            pass
        return None
