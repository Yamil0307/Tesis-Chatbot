"""
memory_manager.py - Gestor centralizado de memoria conversacional con SqliteSaver
Mantiene conversaciones persistentes por sesión usando LangGraph checkpointer.
"""

from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import uuid

class MemoryManager:
    """Gestor de memoria para conversaciones persistentes."""
    
    _instance = None
    
    def __init__(self, db_path: str = "checkpoints.db"):
        """
        Inicializa el gestor de memoria.
        
        Args:
            db_path: Ruta al archivo SQLite de checkpoints
        """
        # Crear conexión a SQLite
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # Crear el SqliteSaver con la conexión
        self.saver = SqliteSaver(self.conn)
        self.session_counter = 0
    
    @staticmethod
    def get_instance():
        """Obtiene la instancia singleton del MemoryManager."""
        if MemoryManager._instance is None:
            MemoryManager._instance = MemoryManager()
        return MemoryManager._instance
    

    def create_session(self, user_id: str = "default") -> str:
        """
        Crea una nueva sesión de conversación y la asocia al usuario.
        """
        # Usar UUID para garantizar unicidad
        thread_id = f"user_{user_id}_{uuid.uuid4().hex[:8]}"
        # Persistir thread_id y user_id en tabla threads
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    thread_id TEXT UNIQUE NOT NULL,
                    cancelled BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Migración: Agregar columna 'cancelled' si no existe
            cursor.execute("PRAGMA table_info(threads)")
            columns = [col[1] for col in cursor.fetchall()]
            if "cancelled" not in columns:
                try:
                    cursor.execute("ALTER TABLE threads ADD COLUMN cancelled BOOLEAN DEFAULT 0")
                    print("[MemoryManager] ✅ Migración: Columna 'cancelled' agregada a tabla 'threads'")
                except Exception as mig_e:
                    print(f"[MemoryManager] Nota sobre migración: {mig_e}")
            
            cursor.execute(
                "INSERT INTO threads (user_id, thread_id) VALUES (?, ?)",
                (user_id, thread_id)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[MemoryManager] Error creando thread: {e}")
        return thread_id

    def get_user_threads(self, user_id: str):
        """
        Recupera todos los thread_id asociados a un user_id.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT thread_id FROM threads WHERE user_id = ?", (user_id,))
            threads = [row[0] for row in cursor.fetchall()]
            conn.close()
            return threads
        except Exception as e:
            print(f"[MemoryManager] Error recuperando threads: {e}")
            return []

    def get_last_state(self, thread_id: str, user_id: str = None):
        """
        Recupera el último estado guardado de un thread, validando que pertenezca al user_id si se provee.
        """
        if user_id:
            # Validar que el thread_id pertenece al user_id
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM threads WHERE thread_id = ? AND user_id = ?", (thread_id, user_id))
                result = cursor.fetchone()
                conn.close()
                if not result:
                    return None
            except Exception as e:
                print(f"[MemoryManager] Error validando thread/user: {e}")
                return None
        # Lógica original
        try:
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint_tuple = self.saver.get_tuple(config)
            if checkpoint_tuple is not None:
                channel_values = checkpoint_tuple.checkpoint.get("channel_values", {})
                return channel_values
            return None
        except Exception as e:
            print(f"Error recuperando estado anterior: {e}")
            return None
    
    def get_config_for_thread(self, thread_id: str) -> dict:
        """
        Obtiene la configuración para un thread específico.
        
        Args:
            thread_id: Identificador del thread
            
        Returns:
            dict: Configuración a pasar a app.invoke()
        """
        return {"configurable": {"thread_id": thread_id}}
    
    def get_last_state(self, thread_id: str):
        """
        Recupera el último estado guardado de un thread.
        CRÍTICO: Permite recuperar el historial de chat anterior.
        
        Args:
            thread_id: Identificador del thread
            
        Returns:
            dict: Último estado guardado o None si no existe
        """
        try:
            # Obtener el último checkpoint usando get_tuple()
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint_tuple = self.saver.get_tuple(config)
            
            if checkpoint_tuple is not None:
                # Acceder al estado del checkpoint
                channel_values = checkpoint_tuple.checkpoint.get("channel_values", {})
                return channel_values
            return None
        except Exception as e:
            print(f"Error recuperando estado anterior: {e}")
            return None
    
    def cancel_thread(self, thread_id: str) -> bool:
        """
        Marca un thread como cancelado.
        
        Args:
            thread_id: Identificador del thread a cancelar
            
        Returns:
            bool: True si se canceló exitosamente, False si hubo error
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE threads SET cancelled = 1 WHERE thread_id = ?",
                (thread_id,)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[MemoryManager] Error cancelando thread: {e}")
            return False
    
    def reset_cancellation(self, thread_id: str) -> bool:
        """
        Resetea el flag de cancelación de un thread para permitir nuevas consultas.
        
        Args:
            thread_id: Identificador del thread a resetear
            
        Returns:
            bool: True si se reseteó exitosamente, False si hubo error
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE threads SET cancelled = 0 WHERE thread_id = ?",
                (thread_id,)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[MemoryManager] Error reseteando cancelación: {e}")
            return False
    
    def is_cancelled(self, thread_id: str) -> bool:
        """
        Chequea si un thread ha sido marcado como cancelado.
        
        Args:
            thread_id: Identificador del thread
            
        Returns:
            bool: True si está cancelado, False si no
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT cancelled FROM threads WHERE thread_id = ?",
                (thread_id,)
            )
            result = cursor.fetchone()
            conn.close()
            if result:
                return bool(result[0])
            return False
        except Exception as e:
            print(f"[MemoryManager] Error chequeando cancelación: {e}")
            return False
    
    def get_saver(self):
        """
        Obtiene el SqliteSaver para compilar el workflow.
        
        Returns:
            SqliteSaver: Checkpointer para LangGraph
        """
        return self.saver


def get_memory_manager() -> MemoryManager:
    """Función de conveniencia para obtener el MemoryManager singleton."""
    return MemoryManager.get_instance()
