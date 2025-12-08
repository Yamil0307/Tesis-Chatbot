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
        Crea una nueva sesión de conversación.
        
        Args:
            user_id: Identificador del usuario (default: "default")
            
        Returns:
            thread_id: Identificador único de la sesión
        """
        thread_id = f"user_{user_id}_{self.session_counter}"
        self.session_counter += 1
        return thread_id
    
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
