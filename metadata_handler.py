"""
metadata_handler.py - Gestor de metadatos y preparación para citaciones

Este módulo encapsula la lógica para:
- Extraer metadatos de documentos
- Formatear citaciones académicas
- Preparar información de fuentes para la respuesta del LLM
- Validar y limpiar metadatos

Objetivo: Centralizar la gestión de metadatos para la Etapa 2 (Citación de Fuentes)
"""

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document


class MetadataHandler:
    """
    Gestor centralizado para metadatos de documentos.
    
    Responsabilidades:
    - Extraer información de fuente de un documento
    - Formatear citaciones académicas
    - Crear etiquetas de fuente para las respuestas
    """
    
    @staticmethod
    def extract_source_info(doc: Document) -> Dict[str, Any]:
        """
        Extrae información de fuente de un documento LangChain.
        
        **ETAPA 2.1: Extraer información completa de metadatos**
        
        Args:
            doc (Document): Documento con metadatos
            
        Returns:
            Dict[str, Any]: Diccionario con información de fuente completa:
                - source: Ruta original del archivo
                - file_name: Nombre del archivo (sin ruta)
                - page: Número de página
                - chunk_index: Índice del fragmento
                - processed_date: Cuándo se procesó
        """
        if not hasattr(doc, 'metadata') or not doc.metadata:
            return {
                "source": "Desconocido",
                "file_name": None,
                "page": None,
                "chunk_index": None,
                "processed_date": None,
                "title": None,
                "author": None,
            }
        
        metadata = doc.metadata
        
        return {
            "source": metadata.get("source", "Desconocido"),
            "file_name": metadata.get("file_name"),  # ← Nuevo en Etapa 2.1
            "page": metadata.get("page"),
            "chunk_index": metadata.get("chunk_index"),
            "processed_date": metadata.get("processed_date"),  # ← Nuevo en Etapa 2.1
            # Otros metadatos disponibles
            "title": metadata.get("title"),
            "author": metadata.get("author"),
            "creator": metadata.get("creator"),
            "total_pages": metadata.get("total_pages"),
        }
    
    @staticmethod
    def format_source_citation(source_info: Dict[str, Any]) -> str:
        """
        Formatea una cita académica a partir de metadatos.
        
        **ETAPA 2.2: Formato académico para citaciones**
        
        Genera citaciones en formato:
        - "Historia de la Universidad (página 42)"
        - "Reglamento Académico"
        - "Documento desconocido"
        
        Args:
            source_info (Dict[str, Any]): Información de fuente extraída
            
        Returns:
            str: Cita formateada para Etapa 2
        """
        file_name = source_info.get("file_name", "Documento desconocido")
        page = source_info.get("page")
        
        # Limpiar nombre de archivo
        if file_name and file_name != "Documento desconocido":
            # Remover extensión .pdf si existe
            display_name = file_name.replace(".pdf", "").replace(".txt", "")
            # Capitalizar correctamente
            display_name = " ".join(word.capitalize() for word in display_name.split("_"))
        else:
            display_name = "Documento desconocido"
        
        # Construir la cita en formato académico
        if page is not None and page != "None":
            return f"{display_name} (página {page})"
        else:
            return display_name
    
    @staticmethod
    def format_source_list(docs: List[Document]) -> str:
        """
        Formatea una lista de documentos como fuentes citadas.
        
        **ETAPA 2.2: Lista de fuentes en formato académico**
        
        Ejemplo de salida:
        ```
        FUENTES CONSULTADAS:
        - Historia de la Universidad (página 54)
        - Reglamento Docente (página 23)
        ```
        
        Args:
            docs (List[Document]): Lista de documentos recuperados
            
        Returns:
            str: Lista de fuentes formateada para académico
        """
        if not docs:
            return "FUENTES CONSULTADAS:\n- (Conocimiento general)"
        
        sources = []  # Lista para preservar orden y permitir duplicados controlados
        seen = set()  # Para detectar duplicados exactos
        
        for doc in docs:
            source_info = MetadataHandler.extract_source_info(doc)
            citation = MetadataHandler.format_source_citation(source_info)
            
            # Evitar duplicados exactos
            if citation not in seen:
                sources.append(citation)
                seen.add(citation)
        
        if not sources:
            sources = ["(Conocimiento general)"]
        
        # Formato académico
        sources_text = "\n".join([f"- {source}" for source in sources])
        return f"\nFUENTES CONSULTADAS:\n{sources_text}"
    
    @staticmethod
    def create_source_annotation(doc: Document) -> str:
        """
        Crea una anotación de fuente para marcar fragmentos.
        
        Útil para que el LLM vea claramente de dónde viene cada fragmento.
        
        Ejemplo: "[Fuente: Historia de la Universidad, página 23]"
        
        Args:
            doc (Document): Documento individual
            
        Returns:
            str: Anotación de fuente formateada
        """
        source_info = MetadataHandler.extract_source_info(doc)
        file_name = source_info.get("file_name", "Desconocido")
        page = source_info.get("page")
        
        if page is not None and page != "None":
            return f"[Fuente: {file_name}, página {page}]"
        else:
            return f"[Fuente: {file_name}]"
    
    @staticmethod
    def format_context_with_annotations(docs: List[Document]) -> str:
        """
        Formatea contexto CON anotaciones de fuente en cada fragmento.
        
        Útil para que el LLM vea claramente de dónde viene cada información.
        
        Args:
            docs (List[Document]): Documentos recuperados
            
        Returns:
            str: Contexto con anotaciones
        """
        if not docs:
            return ""
        
        handler = MetadataHandler()
        formatted_docs = []
        
        for i, doc in enumerate(docs, 1):
            annotation = handler.create_source_annotation(doc)
            formatted_docs.append(f"[{i}] {doc.page_content}\n{annotation}")
        
        return "\n---\n".join(formatted_docs)


# --- FUNCIONES AUXILIARES ---

def clean_file_path(path: str) -> str:
    """
    Limpia una ruta de archivo para mostrar al usuario.
    
    Ejemplo:
        "./data/documento_tesis.pdf" → "documento_tesis.pdf"
    
    Args:
        path (str): Ruta del archivo
        
    Returns:
        str: Nombre del archivo limpio
    """
    return path.split("/")[-1] if "/" in path else path


if __name__ == "__main__":
    # --- PRUEBA DE METADATA HANDLER ---
    from rag_manager import get_rag_manager
    
    print("\n=== Prueba de Metadata Handler ===\n")
    
    mgr = get_rag_manager()
    query = "¿Cuál es la historia de la Universidad de Oriente?"
    context, docs = mgr.search_and_format(query)
    
    print("📝 Prueba 1: Extracción de metadatos")
    if docs:
        source_info = MetadataHandler.extract_source_info(docs[0])
        print(f"Metadatos del primer documento:")
        for key, value in source_info.items():
            print(f"  {key}: {value}")
    
    print("\n📝 Prueba 2: Citación formateada")
    citation = MetadataHandler.format_source_citation(source_info)
    print(f"Cita: {citation}")
    
    print("\n📝 Prueba 3: Lista de fuentes")
    sources_list = MetadataHandler.format_source_list(docs)
    print(f"Fuentes:\n{sources_list}")
    
    print("\n📝 Prueba 4: Contexto con anotaciones")
    annotated_context = MetadataHandler.format_context_with_annotations(docs)
    print(f"Contexto anotado (primeros 300 caracteres):\n{annotated_context[:300]}...\n")
    
    print("✅ Metadata Handler funcionando correctamente")
