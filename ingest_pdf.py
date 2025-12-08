"""
ingest_pdf.py - Ingesta de documentos PDF

Este módulo encapsula la lógica para:
- Cargar archivos PDF
- Fragmentar y procesar contenido
- Crear bases de datos vectoriales FAISS
- Gestionar metadatos de documentos

Objetivo: Modularizar la ingesta para soportar múltiples formatos (OCR, imágenes, etc.)
"""

import os
from typing import List, Optional
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from ingest_utils import (
    load_embeddings,
    split_documents,
    add_chunk_metadata,
    add_document_summary,
    validate_file
)

# --- CONFIGURACIÓN ---
load_dotenv()


class PDFIngestor:
    """
    Ingestor especializado en archivos PDF.
    
    Responsabilidades:
    - Cargar PDF con PyPDFLoader
    - Procesar documentos
    - Crear base de datos vectorial
    """
    
    def __init__(self, db_path: str = "vectorstore_faiss"):
        """
        Inicializa el ingestor PDF.
        
        Args:
            db_path (str): Ruta donde se guardará la base de datos FAISS
        """
        self.db_path = db_path
        self.embeddings = None
    
    def load_pdf(self, pdf_path: str) -> Optional[List[Document]]:
        """
        Carga un archivo PDF.
        
        Args:
            pdf_path (str): Ruta del archivo PDF
            
        Returns:
            Optional[List[Document]]: Lista de documentos o None si falla
        """
        # Validar archivo
        if not validate_file(pdf_path, "PDF"):
            return None
        
        try:
            print(f"📄 Cargando documento PDF: {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            print(f"   ✅ Se cargaron {len(documents)} páginas")
            return documents
            
        except Exception as e:
            print(f"❌ ERROR al cargar PDF: {e}")
            return None
    
    def process_documents(
        self,
        documents: List[Document],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        add_metadata: bool = True,
        add_summaries: bool = True
    ) -> Optional[List[Document]]:
        """
        Procesa documentos (fragmenta, agrega metadatos y resúmenes).
        
        **ETAPA 2: Mejora de Ingestión - Resúmenes automáticos**
        
        Args:
            documents (List[Document]): Documentos cargados
            chunk_size (int): Tamaño de fragmento
            chunk_overlap (int): Superposición
            add_metadata (bool): Si agregar metadatos de chunk_index
            add_summaries (bool): Si generar resúmenes automáticos
            
        Returns:
            Optional[List[Document]]: Documentos procesados
        """
        try:
            # Fragmentar
            texts = split_documents(documents, chunk_size, chunk_overlap)
            
            # Agregar metadatos de chunk
            if add_metadata:
                texts = add_chunk_metadata(texts)
            
            # **NUEVO: Agregar resúmenes para mejorar contexto**
            if add_summaries:
                texts = add_document_summary(texts, use_ai_summary=True)
            
            return texts
            
        except Exception as e:
            print(f"❌ ERROR al procesar documentos: {e}")
            return None
    
    def create_vectorstore(self, documents: List[Document]) -> Optional[FAISS]:
        """
        Crea una base de datos vectorial FAISS.
        
        Args:
            documents (List[Document]): Documentos a vectorizar
            
        Returns:
            Optional[FAISS]: Vectorstore creado o None si falla
        """
        try:
            # Cargar embeddings si no están cargados
            if not self.embeddings:
                self.embeddings = load_embeddings()
            
            print("💾 Creando base de datos vectorial FAISS...")
            vectorstore = FAISS.from_documents(documents, self.embeddings)
            print(f"   ✅ Base de datos creada con {len(documents)} fragmentos")
            
            return vectorstore
            
        except Exception as e:
            print(f"❌ ERROR al crear vectorstore: {e}")
            return None
    
    def save_vectorstore(self, vectorstore: FAISS) -> bool:
        """
        Guarda la base de datos vectorial en disco.
        
        Args:
            vectorstore (FAISS): Base de datos a guardar
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            print(f"💾 Guardando base de datos en '{self.db_path}'...")
            vectorstore.save_local(self.db_path)
            print(f"✅ ¡ÉXITO! Base de datos guardada correctamente")
            return True
            
        except Exception as e:
            print(f"❌ ERROR al guardar base de datos: {e}")
            return False
    
    def ingest_pdf(
        self,
        pdf_path: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> bool:
        """
        Pipeline completo de ingesta de PDF.
        
        Realiza:
        1. Carga del PDF
        2. Fragmentación y procesamiento
        3. Generación de resúmenes automáticos (NUEVO)
        4. Creación de vectorstore
        5. Guardado en disco
        
        **ETAPA 2: Mejora de Ingestión - Resúmenes automáticos**
        Los resúmenes mejoran la búsqueda al proporcionar contexto de alto nivel.
        
        Args:
            pdf_path (str): Ruta del PDF
            chunk_size (int): Tamaño de fragmento
            chunk_overlap (int): Superposición
            
        Returns:
            bool: True si todo fue exitoso
        """
        print(f"\n{'='*60}")
        print(f"INGESTA DE PDF: {pdf_path}")
        print(f"{'='*60}\n")
        
        # Paso 1: Cargar PDF
        documents = self.load_pdf(pdf_path)
        if not documents:
            return False
        
        # Paso 2: Procesar documentos (fragmentar, metadatos, resúmenes)
        processed_docs = self.process_documents(documents, chunk_size, chunk_overlap)
        if not processed_docs:
            return False
        
        # Paso 3: Crear vectorstore
        vectorstore = self.create_vectorstore(processed_docs)
        if not vectorstore:
            return False
        
        # Paso 4: Guardar
        success = self.save_vectorstore(vectorstore)
        
        return success


def ingest_pdf_simple(
    pdf_path: str,
    db_path: str = "vectorstore_faiss"
) -> bool:
    """
    Función simplificada para ingesta de PDF.
    
    Usa valores por defecto para compatibilidad con ingest_data.py original.
    
    Args:
        pdf_path (str): Ruta del PDF
        db_path (str): Ruta de la base de datos FAISS
        
    Returns:
        bool: True si exitoso
    """
    ingestor = PDFIngestor(db_path=db_path)
    return ingestor.ingest_pdf(pdf_path)


if __name__ == "__main__":
    print("\n=== Prueba de PDF Ingestor ===\n")
    
    pdf_path = "./data/info_prueba.pdf"
    
    # Crear ingestor
    ingestor = PDFIngestor()
    
    # Ejecutar pipeline
    success = ingestor.ingest_pdf(pdf_path)
    
    if success:
        print("\n✅ Ingesta completada exitosamente")
    else:
        print("\n❌ Ingesta falló")
