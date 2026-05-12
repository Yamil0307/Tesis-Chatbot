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
            
            # --- CONFIGURACIÓN: Similarity (Relevancia) ---
            # search_type="similarity": Busca los documentos más similares a la query.
            # Este modo es ideal para datos históricos donde queremos precisión, no diversidad.
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 10  # Número de documentos a recuperar
                }
            )
            
            print("✅ RAG Manager inicializado correctamente (Modo Similarity Activado)")
            
        except Exception as e:
            print(f"❌ ERROR al inicializar RAG Manager: {e}")
            print("   Por favor, ejecuta 'python ingest_data.py' primero")
            raise
    
    def search(self, query: str, k: int = 10, debug: bool = False) -> List[Document]:
        """
        Busca documentos relevantes usando Similarity con scores.
        Permite ajustar k dinámicamente.
        
        Args:
            query: Texto de búsqueda
            k: Número de documentos a recuperar
            debug: Si True, muestra información de debug (scores)
        
        Returns:
            List[Document]: Lista de documentos (sin scores para compatibilidad)
        """
        if not self.vector_store:
            return []
        
        # Ejecutar búsqueda con scores
        try:
            # similarity_search_with_score devuelve [(doc, score), ...]
            docs_and_scores = self.vector_store.similarity_search_with_score(query, k=k)
            
            # DEBUG: Mostrar scores
            if debug:
                print(f"\n🔍 DEBUG - Scores para query: '{query}'")
                for i, (doc, score) in enumerate(docs_and_scores[:5]):
                    filename = doc.metadata.get("file_name", "desconocido")
                    preview = doc.page_content[:80].replace("\n", " ")
                    print(f"  [{i+1}] Score: {score:.4f} | {filename}")
                    print(f"      Preview: {preview}...")
            
            # Devolver solo los documentos (para compatibilidad)
            docs = [doc for doc, score in docs_and_scores]
            
            # Guardar scores en los metadatos para debugging
            for i, (doc, score) in enumerate(docs_and_scores):
                doc.metadata["search_score"] = score
            
            # Aplicar boost por nombre (prioriza docs con palabras del query)
            docs = self.boost_by_name(docs, query)
            
            return docs
        except Exception as e:
            print(f"⚠️ Error en búsqueda: {type(e).__name__}: {e}")
            return []
    
    def search_with_scores(self, query: str, k: int = 10) -> List[tuple]:
        """
        Busca documentos relevantes Y devuelve los scores.
        Útil para debugging y filtrado.
        
        Returns:
            List[tuple]: Lista de (Document, score)
        """
        if not self.vector_store:
            return []
        
        try:
            docs_and_scores = self.vector_store.similarity_search_with_score(query, k=k)
            return docs_and_scores
        except Exception as e:
            print(f"⚠️ Error en búsqueda con scores: {e}")
            return []
    
    def boost_by_name(self, docs: List[Document], query: str) -> List[Document]:
        """
        Boost: Prioriza documentos que contienen palabras del query (especialmente nombres).
        
        Esto es útil cuando el usuario busca una persona específica - 
        los documentos con ese nombre aparecen primero.
        """
        if not docs or not query:
            return docs
        
        # Extraer palabras del query (excluyendo palabras comunes)
        common_words = {'de', 'la', 'el', 'en', 'que', 'es', 'por', 'para', 'con', 'una', 'un', 'del', 'al', 'los', 'las', 'se', 'su', 'su'}
        query_words = [word.lower() for word in query.split() if word.lower() not in common_words]
        
        if not query_words:
            return docs
        
        def get_boost_score(doc: Document) -> float:
            """Mayor score = más relevante"""
            content = doc.page_content.lower()
            # Contar cuántas palabras del query aparecen en el documento
            matches = sum(1 for word in query_words if word in content)
            # Por cada coincidencia, agregar el score base del metadata
            base_score = doc.metadata.get("search_score", 0)
            return matches + base_score
        
        # Ordenar por boost score (descendente)
        return sorted(docs, key=get_boost_score, reverse=True)
    
    def format_context(self, docs: List[Document]) -> str:
        """
        Formatea una lista de documentos en un string de contexto numerado.
        Incluye explícitamente el número de página para ayudar al LLM.
        Limita a máximo 6 documentos para evitar saturación.
        """
        if not docs:
            return ""
        
        # Limitar a 6 documentos máximo para evitar saturación del modelo
        docs = docs[:6]
        
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