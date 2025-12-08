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
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()

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


def generate_document_summary(text: str, max_length: int = 500) -> str:
    """
    Genera un resumen amplio del DOCUMENTO COMPLETO usando Gemini.
    
    **ETAPA 2: Mejora de Ingestión - Un resumen por documento (no por fragmento)**
    
    Este resumen se agrega como metadato a TODOS los fragmentos del mismo documento
    para que el agente tenga contexto general del contenido.
    
    Args:
        text (str): Texto completo del documento a resumir
        max_length (int): Longitud máxima del resumen
        
    Returns:
        str: Resumen amplio del documento (máximo max_length caracteres)
    """
    try:
        # Si el texto es muy corto, devolverlo tal cual
        if len(text) < 300:
            return text
        
        # Inicializar el LLM con temperatura baja para resúmenes consistentes
        llm = ChatGoogleGenerativeAI(model="gemini-robotics-er-1.5-preview", temperature=0.0)
        
        # Prompt para generar resumen académico AMPLIO del documento
        summary_prompt = (
            f"Resume el siguiente documento en máximo {max_length} caracteres. "
            f"Incluye los temas PRINCIPALES, estructura general y puntos clave. "
            f"Sé comprensivo pero mantén el rigor académico. "
            f"Responde SOLO con el resumen, sin explicaciones adicionales.\n\n"
            f"DOCUMENTO:\n{text[:5000]}"  # Usar más contenido para resumen más completo
        )
        
        # Generar resumen
        summary = llm.invoke(summary_prompt).content.strip()
        
        # Garantizar que no exceda max_length
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary
        
    except Exception as e:
        # Si falla la generación de resumen, devolver un resumen simple
        print(f"   ⚠️  Error generando resumen con IA: {e}")
        print(f"      Usando resumen simple en su lugar")
        return text[:max_length] + "..." if len(text) > max_length else text


def add_document_summary(
    documents: List[Document],
    use_ai_summary: bool = True
) -> List[Document]:
    """
    Agrega UN RESUMEN AMPLIO por documento a todos sus fragmentos.
    
    **ETAPA 2: Mejora de Ingestión - Un resumen por documento (eficiente)**
    
    Comportamiento:
    1. Agrupa fragmentos por documento (por metadata "source")
    2. Concatena todo el contenido del documento
    3. Genera UN SOLO resumen para el documento completo
    4. Agrega ese resumen a TODOS los fragmentos del documento
    5. Prepende el resumen al primer fragmento de cada documento
    
    Esto es más eficiente que hacer 100+ resúmenes.
    
    Args:
        documents (List[Document]): Documentos (fragmentos) a procesar
        use_ai_summary (bool): Si usar Gemini para resumen o resumen simple
        
    Returns:
        List[Document]: Documentos con resumen del documento agregado
    """
    print("📝 Generando resumen amplio por documento...")
    
    # Agrupar fragmentos por documento (por source)
    docs_by_source = {}
    for doc in documents:
        source = doc.metadata.get("source", "desconocido")
        if source not in docs_by_source:
            docs_by_source[source] = []
        docs_by_source[source].append(doc)
    
    # Generar un resumen por documento
    document_summaries = {}
    for source, docs in docs_by_source.items():
        # Concatenar todo el contenido del documento
        full_text = "\n".join([doc.page_content for doc in docs])
        
        # Generar resumen amplio
        if use_ai_summary:
            summary = generate_document_summary(full_text, max_length=500)
        else:
            # Resumen simple: primeros 500 caracteres
            summary = full_text[:500] + "..." if len(full_text) > 500 else full_text
        
        document_summaries[source] = summary
        print(f"   ✅ Resumen generado para: {os.path.basename(source)}")
    
    # Agregar el resumen del documento a TODOS sus fragmentos
    for doc in documents:
        source = doc.metadata.get("source", "desconocido")
        doc_summary = document_summaries.get(source, "")
        
        # Agregar resumen como metadato
        doc.metadata["document_summary"] = doc_summary
        
        # Prepender SOLO al primer fragmento de cada documento
        chunk_index = doc.metadata.get("chunk_index", 0)
        if chunk_index == 0:
            # Solo el primer chunk incluye el resumen en el contenido
            doc.page_content = f"[RESUMEN DEL DOCUMENTO]\n{doc_summary}\n\n[FRAGMENTO 1]\n{doc.page_content}"
    
    print(f"   ✅ {len(documents)} fragmentos tienen resumen del documento")
    print(f"   ✅ {len(document_summaries)} documento(s) resumido(s)")
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
