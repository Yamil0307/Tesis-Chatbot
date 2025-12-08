"""
ingest_utils.py - Utilidades para ingesta de documentos

Este módulo contiene funciones auxiliares reutilizables para:
- Cargar embeddings
- Crear bases de datos vectoriales
- Validar archivos
- Configuración de parámetros
"""

import os
from typing import Dict, List
from datetime import datetime
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# --- CONFIGURACIÓN GLOBAL ---
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Parámetros de fragmentación (se pueden ajustar según necesidades)
CHUNK_CONFIG = {
    "chunk_size": 1000,      # Tamaño de cada fragmento en caracteres
    "chunk_overlap": 200     # Superposición entre fragmentos
}


def load_embeddings(model_name: str = EMBEDDING_MODEL) -> HuggingFaceEmbeddings:
    """
    Carga el modelo de embeddings.
    
    Args:
        model_name (str): Nombre del modelo de HuggingFace a usar
        
    Returns:
        HuggingFaceEmbeddings: Modelo de embeddings inicializado
    """
    try:
        print(f"🧠 Cargando embeddings: {model_name}")
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        print("   ✅ Embeddings cargados correctamente")
        return embeddings
    except Exception as e:
        print(f"❌ ERROR al cargar embeddings: {e}")
        raise


def create_text_splitter(
    chunk_size: int = CHUNK_CONFIG["chunk_size"],
    chunk_overlap: int = CHUNK_CONFIG["chunk_overlap"]
) -> RecursiveCharacterTextSplitter:
    """
    Crea un fragmentador de texto configurado.
    
    Args:
        chunk_size (int): Tamaño de cada fragmento
        chunk_overlap (int): Superposición entre fragmentos
        
    Returns:
        RecursiveCharacterTextSplitter: Fragmentador configurado
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )


def split_documents(
    documents: List[Document],
    chunk_size: int = CHUNK_CONFIG["chunk_size"],
    chunk_overlap: int = CHUNK_CONFIG["chunk_overlap"]
) -> List[Document]:
    """
    Fragmenta una lista de documentos.
    
    Args:
        documents (List[Document]): Documentos a fragmentar
        chunk_size (int): Tamaño de cada fragmento
        chunk_overlap (int): Superposición entre fragmentos
        
    Returns:
        List[Document]: Documentos fragmentados
    """
    print("✂️  Fragmentando texto...")
    
    splitter = create_text_splitter(chunk_size, chunk_overlap)
    texts = splitter.split_documents(documents)
    
    print(f"   ✅ Se crearon {len(texts)} fragmentos")
    return texts


def add_chunk_metadata(
    documents: List[Document],
    source_name: str = "desconocido"
) -> List[Document]:
    """
    Agrega metadatos completos a los documentos para citación académica.
    
    **ETAPA 2.1: Enriquecer metadatos**
    
    Agrega los siguientes metadatos a cada fragmento:
    - chunk_index: Índice secuencial del fragmento
    - source: Ruta original del archivo
    - file_name: Nombre del archivo (sin ruta)
    - processed_date: Fecha/hora de procesamiento
    - page: Número de página (del metadata original)
    
    Estos metadatos permiten generar citaciones académicas como:
    "- Historia de la Universidad (página 42)"
    
    Args:
        documents (List[Document]): Documentos a actualizar
        source_name (str): Nombre de la fuente (para identificar fragmentos)
        
    Returns:
        List[Document]: Documentos con metadatos enriquecidos
    """
    processed_date = datetime.now().isoformat()
    
    for idx, doc in enumerate(documents):
        if not hasattr(doc, 'metadata') or doc.metadata is None:
            doc.metadata = {}
        
        # 1. AGREGAR ÍNDICE DE FRAGMENTO
        doc.metadata["chunk_index"] = idx
        
        # 2. AGREGAR FUENTE SI NO EXISTE
        if "source" not in doc.metadata:
            doc.metadata["source"] = source_name
        
        # 3. EXTRAER NOMBRE DE ARCHIVO (sin ruta)
        source_path = doc.metadata.get("source", "")
        if source_path:
            file_name = os.path.basename(source_path)
            # Remover extensión si es muy larga
            if len(file_name) > 50:
                file_name = file_name[:47] + "..."
            doc.metadata["file_name"] = file_name
        else:
            doc.metadata["file_name"] = "Documento sin nombre"
        
        # 4. AGREGAR FECHA DE PROCESAMIENTO
        doc.metadata["processed_date"] = processed_date
        
        # 5. ASEGURAR QUE EXISTE "page" (PyPDFLoader lo agrega automáticamente)
        if "page" not in doc.metadata:
            doc.metadata["page"] = 0
    
    print(f"   ✅ Metadatos enriquecidos en {len(documents)} fragmentos")
    print(f"      - file_name: ✅")
    print(f"      - page: ✅")
    print(f"      - chunk_index: ✅")
    print(f"      - processed_date: ✅")
    
    return documents


def validate_file(file_path: str, file_type: str = "PDF") -> bool:
    """
    Valida que un archivo exista y tenga la extensión correcta.
    
    Args:
        file_path (str): Ruta del archivo
        file_type (str): Tipo de archivo esperado (ej: "PDF")
        
    Returns:
        bool: True si el archivo es válido
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: No se encuentra el archivo en {file_path}")
        return False
    
    if not file_path.lower().endswith(file_type.lower()):
        print(f"❌ Error: Se esperaba un archivo .{file_type.lower()}")
        return False
    
    return True


if __name__ == "__main__":
    print("\n=== Prueba de ingest_utils ===\n")
    
    # Prueba: cargar embeddings
    try:
        embeddings = load_embeddings()
        print(f"Embeddings cargados: {type(embeddings).__name__}\n")
    except Exception as e:
        print(f"Error en prueba de embeddings: {e}\n")
    
    # Prueba: validar archivo
    is_valid = validate_file("./data/documento_tesis.pdf", "PDF")
    print(f"Archivo válido: {is_valid}\n")
    
    print("✅ ingest_utils funcionando correctamente")
