"""
rag_manager.py - Gestor centralizado de recuperación de documentos (RAG)

Este módulo encapsula toda la lógica relacionada con:
- Carga de embeddings
- Carga de la base de datos vectorial FAISS
- Búsqueda y recuperación de documentos
- Manejo de contexto

Objetivo: Separar la lógica de RAG del agente para que sea reutilizable y testeable.
"""

import os
from typing import List, Tuple
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# --- CONFIGURACIÓN ---
load_dotenv()
DB_FAISS_PATH = "vectorstore_faiss"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class RAGManager:
    """
    Gestor centralizado para recuperación de documentos.
    
    Responsabilidades:
    - Inicializar embeddings y cargar FAISS
    - Buscar documentos relevantes
    - Formatar contexto para el LLM
    - Recuperar metadatos de documentos
    """
    
    def __init__(self, db_path: str = DB_FAISS_PATH):
        """
        Inicializa el RAGManager cargando embeddings y FAISS.
        
        Args:
            db_path (str): Ruta a la base de datos FAISS
            
        Raises:
            Exception: Si no encuentra la base de datos FAISS
        """
        self.db_path = db_path
        self.embeddings = None
        self.vector_store = None
        self.retriever = None
        
        self._initialize()
    
    def _initialize(self):
        """Inicializa embeddings y carga la base de datos FAISS."""
        try:
            print("🧠 Inicializando embeddings...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL
            )
            
            print(f"📚 Cargando base de datos FAISS desde '{self.db_path}'...")
            self.vector_store = FAISS.load_local(
                self.db_path, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
            
            # Crear el retriever con parámetros por defecto
            # k=4 significa recuperar los 4 documentos más similares
            self.retriever = self.vector_store.as_retriever(
                search_kwargs={"k": 4}
            )
            
            print("✅ RAG Manager inicializado correctamente")
            
        except Exception as e:
            print(f"❌ ERROR al inicializar RAG Manager: {e}")
            print("   Por favor, ejecuta 'python ingest_data.py' primero")
            raise
    
    def search(self, query: str, k: int = 4) -> List[Document]:
        """
        Busca documentos relevantes para una consulta.
        
        Args:
            query (str): Pregunta o búsqueda del usuario
            k (int): Número de documentos a recuperar (default=4)
            
        Returns:
            List[Document]: Lista de documentos relevantes con metadatos
        """
        if not self.retriever:
            return []
        
        docs = self.retriever.invoke(query)
        return docs[:k]
    
    def format_context(self, docs: List[Document]) -> str:
        """
        Formatea una lista de documentos en un string de contexto.
        
        Args:
            docs (List[Document]): Documentos recuperados
            
        Returns:
            str: Contexto formateado para el LLM
        """
        if not docs:
            return ""
        
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            formatted_docs.append(f"[{i}] {doc.page_content}")
        
        return "\n---\n".join(formatted_docs)
    
    def search_and_format(self, query: str, k: int = 4) -> Tuple[str, List[Document]]:
        """
        Busca documentos y devuelve tanto el contexto formateado como los documentos originales.
        
        Esto es útil para recuperar metadatos después.
        
        Args:
            query (str): Pregunta del usuario
            k (int): Número de documentos a recuperar
            
        Returns:
            Tuple[str, List[Document]]: (contexto_formateado, documentos_originales)
        """
        docs = self.search(query, k)
        context = self.format_context(docs)
        return context, docs
    
    def get_document_metadata(self, doc: Document) -> dict:
        """
        Extrae los metadatos de un documento.
        
        Args:
            doc (Document): Documento de LangChain
            
        Returns:
            dict: Diccionario con metadatos (source, page, etc.)
        """
        return doc.metadata if hasattr(doc, 'metadata') else {}


# --- INSTANCIA GLOBAL (Lazy Singleton) ---
# Se inicializa SOLO cuando se llama get_rag_manager() (no al importar)
_rag_manager_instance = None

def get_rag_manager() -> RAGManager:
    """
    Obtiene la instancia global del RAGManager (inicialización lazy).
    Crea una nueva SOLO la primera vez que se llama.
    
    Returns:
        RAGManager: Instancia del gestor de RAG
    """
    global _rag_manager_instance
    if _rag_manager_instance is None:
        print("[RAG] Inicializando RAG Manager (primera vez)...")
        _rag_manager_instance = RAGManager()
    return _rag_manager_instance


if __name__ == "__main__":
    # --- PRUEBA SIMPLE ---
    print("\n=== Prueba de RAG Manager ===\n")
    
    mgr = get_rag_manager()
    
    # Prueba 1: Búsqueda simple
    print("📝 Prueba 1: Búsqueda simple")
    query = "¿Cuál es la historia de la Universidad de Oriente?"
    context, docs = mgr.search_and_format(query)
    print(f"Consulta: {query}")
    print(f"Documentos encontrados: {len(docs)}")
    print(f"Contexto (primeros 200 caracteres):\n{context[:200]}...\n")
    
    # Prueba 2: Acceso a metadatos
    print("📝 Prueba 2: Acceso a metadatos")
    if docs:
        metadata = mgr.get_document_metadata(docs[0])
        print(f"Metadatos del primer documento: {metadata}\n")
    
    print("✅ RAG Manager funcionando correctamente")
