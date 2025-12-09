"""
rag_manager.py - Gestor centralizado de recuperación de documentos (RAG)

Este módulo encapsula toda la lógica relacionada con:
- Carga de embeddings
- Carga de la base de datos vectorial FAISS
- Búsqueda y recuperación de documentos usando MMR (Diversidad)
- Manejo de contexto

Objetivo: Optimizar la recuperación para encontrar datos específicos.
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
    Utiliza MMR (Maximal Marginal Relevance) para evitar redundancia.
    """
    
    def __init__(self, db_path: str = DB_FAISS_PATH):
        """
        Inicializa el RAGManager.
        Args:
            db_path (str): Ruta a la base de datos FAISS
        """
        self.db_path = db_path
        self.embeddings = None
        self.vector_store = None
        self.retriever = None
        
        self._initialize()
    
    def _initialize(self):
        """Inicializa embeddings y carga la base de datos FAISS con configuración MMR."""
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
            
            # --- CONFIGURACIÓN CRÍTICA: MMR (Diversidad) ---
            # search_type="mmr": Busca diversidad en lugar de similitud pura.
            # fetch_k: Número de documentos iniciales a analizar (antes de filtrar).
            self.retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": 10,           # Valor base (se sobreescribe en search)
                    "fetch_k": 50,     # Leemos 50 candidatos para encontrar la aguja en el pajar
                    "lambda_mult": 0.6 # Balancea relevancia (1.0) vs diversidad (0.0)
                }
            )
            
            print("✅ RAG Manager inicializado correctamente (Modo MMR Activado)")
            
        except Exception as e:
            print(f"❌ ERROR al inicializar RAG Manager: {e}")
            print("   Por favor, ejecuta 'python ingest_data.py' primero")
            raise
    
    def search(self, query: str, k: int = 10) -> List[Document]:
        """
        Busca documentos relevantes usando MMR.
        Permite ajustar k dinámicamente.
        """
        if not self.retriever:
            return []
        
        # Actualizamos dinámicamente k y fetch_k en el retriever
        self.retriever.search_kwargs["k"] = k
        # Aseguramos que fetch_k sea siempre mayor que k para que MMR funcione
        if self.retriever.search_type == "mmr":
            self.retriever.search_kwargs["fetch_k"] = max(k * 3, 50)
        
        # Ejecutar búsqueda
        try:
            docs = self.retriever.invoke(query)
            return docs
        except Exception as e:
            print(f"⚠️ Error en búsqueda: {e}")
            return []
    
    def format_context(self, docs: List[Document]) -> str:
        """
        Formatea una lista de documentos en un string de contexto numerado.
        Incluye explícitamente el número de página para ayudar al LLM.
        """
        if not docs:
            return ""
        
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            # Limpiamos saltos de línea excesivos para ahorrar tokens
            content = doc.page_content.replace("\n", " ").strip()
            # Añadimos referencia de página si existe
            page = doc.metadata.get("page", "?")
            formatted_docs.append(f"FRAGMENTO [{i}] (Pág {page}):\n{content}")
        
        return "\n\n".join(formatted_docs)
    
    def search_and_format(self, query: str, k: int = 10) -> Tuple[str, List[Document]]:
        """Busca documentos y devuelve contexto + lista original."""
        docs = self.search(query, k)
        context = self.format_context(docs)
        return context, docs


# --- INSTANCIA GLOBAL (Lazy Singleton) ---
_rag_manager_instance = None

def get_rag_manager() -> RAGManager:
    """Obtiene la instancia global del RAGManager."""
    global _rag_manager_instance
    if _rag_manager_instance is None:
        _rag_manager_instance = RAGManager()
    return _rag_manager_instance