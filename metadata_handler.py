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
        
        Args:
            doc (Document): Documento con metadatos
            
        Returns:
            Dict[str, Any]: Diccionario con información de fuente:
                - source: Nombre del archivo
                - page: Número de página
                - chunk_index: Índice del fragmento (si existe)
        """
        if not hasattr(doc, 'metadata') or not doc.metadata:
            return {
                "source": "Desconocido",
                "page": None,
                "chunk_index": None
            }
        
        metadata = doc.metadata
        
        return {
            "source": metadata.get("source", "Desconocido"),
            "page": metadata.get("page"),
            "chunk_index": metadata.get("chunk_index"),
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
        
        Ejemplo:
            "El principito (pp. 54-55)"
            "Documento desconocido"
        
        Args:
            source_info (Dict[str, Any]): Información de fuente extraída
            
        Returns:
            str: Cita formateada
        """
        source = source_info.get("source", "Desconocido")
        page = source_info.get("page")
        title = source_info.get("title")
        
        # Si tenemos título, usarlo; si no, usar nombre del archivo
        display_name = title if title else source.split("/")[-1]
        
        # Construir la cita
        if page is not None:
            return f"{display_name} (p. {page})"
        else:
            return display_name
    
    @staticmethod
    def format_source_list(docs: List[Document]) -> str:
        """
        Formatea una lista de documentos como fuentes citadas.
        
        Ejemplo de salida:
            "📄 FUENTES:
            - El principito (p. 54)
            - Reglamento Docente (pp. 23-24)"
        
        Args:
            docs (List[Document]): Lista de documentos recuperados
            
        Returns:
            str: Lista de fuentes formateada para el usuario
        """
        if not docs:
            return ""
        
        handler = MetadataHandler()
        sources = set()  # Para evitar duplicados
        
        for doc in docs:
            source_info = handler.extract_source_info(doc)
            citation = handler.format_source_citation(source_info)
            sources.add(citation)
        
        if not sources:
            return ""
        
        sources_str = "\n".join([f"  - {source}" for source in sorted(sources)])
        return f"\n\n📄 FUENTES:\n{sources_str}"
    
    @staticmethod
    def create_source_annotation(doc: Document) -> str:
        """
        Crea una anotación de fuente para un fragmento individual.
        
        Útil para marcar fragmentos en el contexto.
        
        Args:
            doc (Document): Documento individual
            
        Returns:
            str: Anotación de fuente (ejemplo: "[Fuente: Documento, p. 23]")
        """
        handler = MetadataHandler()
        source_info = handler.extract_source_info(doc)
        citation = handler.format_source_citation(source_info)
        return f"[Fuente: {citation}]"
    
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
