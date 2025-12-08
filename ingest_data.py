"""
ingest_data.py - Script principal para ingesta de documentos

NOTA: Este script ahora es una interfaz simplificada hacia ingest_pdf.py
      para mantener compatibilidad hacia atrás.

Uso:
    python ingest_data.py
"""

import os
from dotenv import load_dotenv
from ingest_pdf import ingest_pdf_simple

# Cargar variables de entorno
load_dotenv()

# Rutas
PDF_PATH = "./data/documento_tesis.pdf"
DB_FAISS_PATH = "vectorstore_faiss"


def create_vector_db():
    """
    Crea la base de datos vectorial FAISS usando ingest_pdf.py
    
    Esta función mantiene compatibilidad con el código anterior.
    Internamente usa la clase PDFIngestor para la ingesta.
    """
    success = ingest_pdf_simple(PDF_PATH, DB_FAISS_PATH)
    
    if not success:
        print(f"\n❌ La ingesta falló. Verifica que el archivo exista en: {PDF_PATH}")


if __name__ == "__main__":
    create_vector_db()