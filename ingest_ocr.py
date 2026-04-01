# ingest_ocr.py
"""
OCRIngestor: Pipeline de ingesta de imágenes escaneadas (OCR) al vectorstore, alineado a la arquitectura de ingest_pdf.py.
"""
import os
from typing import List, Optional
from langchain_core.documents import Document
# from PIL import Image  # Se usará si el modelo OCR lo requiere
# import requests  # Para llamada a API Mistral OCR
from ingest_utils import (
    validate_file,
    split_documents,
    add_chunk_metadata,
    add_document_summary,
    load_embeddings,
)

class OCRIngestor:
    def __init__(self, db_path: str = "vectorstore_faiss", embedding_model: str = None):
        self.db_path = db_path
        self.embedding_model = embedding_model or "sentence-transformers/all-MiniLM-L6-v2"
        self.embeddings = load_embeddings(self.embedding_model)

    def load_ocr_image(self, image_path: str) -> Optional[List[Document]]:
        """
        Carga una imagen, ejecuta OCR (Mistral OCR API), retorna List[Document] igual que load_pdf().
        """
        MISTRAL_OCR_MODEL = "mistral-ocr-latest"
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY") or os.getenv("MISTRAL_OCR_API_KEY")
        if not MISTRAL_API_KEY:
            print("❌ ERROR: No se encontró la variable MISTRAL_API_KEY en el entorno (.env)")
            return None
        if not validate_file(image_path, "IMG"):
            print(f"❌ Error: Archivo de imagen no válido: {image_path}")
            return None
        try:
            print(f"🖼️  Cargando imagen para OCR: {image_path}")
            import base64
            from mistralai.client import Mistral
            client = Mistral(api_key=MISTRAL_API_KEY)
            with open(image_path, "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
            ext = os.path.splitext(image_path)[1].lower().replace('.', '')
            mime = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else ext}"
            image_url = f"data:{mime};base64,{img_b64}"
            ocr_response = client.ocr.process(
                document={
                    "type": "image_url",
                    "image_url": image_url
                },
                model=MISTRAL_OCR_MODEL,
                include_image_base64=False
            )
            print("\n===== ATRIBUTOS DE OCRResponse =====\n")
            print(f"type: {type(ocr_response)}")
            print(f"dir: {dir(ocr_response)}")
            print("\n===== ocr_response.pages =====\n")
            print(ocr_response.pages)
            print("\n===== ocr_response.document_annotation =====\n")
            print(ocr_response.document_annotation)
            print("\n===== FIN ATRIBUTOS OCRResponse =====\n")

            # Extraer texto de pages usando 'markdown'
            text = ""
            if hasattr(ocr_response, 'pages') and ocr_response.pages:
                try:
                    text = "\n".join([getattr(p, "markdown", "") for p in ocr_response.pages if getattr(p, "markdown", None)])
                except Exception as e:
                    print(f"❌ ERROR al extraer texto de pages.markdown: {e}")
            if not text and hasattr(ocr_response, 'document_annotation') and ocr_response.document_annotation:
                text = str(ocr_response.document_annotation)
            if not text:
                print(f"❌ ERROR: OCR no devolvió texto")
                return None
            doc = Document(
                page_content=text,
                metadata={
                    "source": image_path,
                    "file_name": os.path.basename(image_path)[:50],
                    "page": 0,
                    "processed_date": None,  # Se agrega en add_chunk_metadata
                }
            )
            print(f"   ✅ OCR exitoso, texto extraído")
            return [doc]
        except Exception as e:
            print(f"❌ ERROR al extraer OCR: {e}")
            return None

    def process_documents(self, documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> Optional[List[Document]]:
        try:
            print(f"✂️  Fragmentando y enriqueciendo metadatos...")
            texts = split_documents(documents, chunk_size, chunk_overlap)
            texts = add_chunk_metadata(texts, documents[0].metadata["file_name"])
            texts = add_document_summary(texts, use_ai_summary=True)
            print(f"   ✅ Procesamiento completo: {len(texts)} fragmentos")
            return texts
        except Exception as e:
            print(f"❌ ERROR en procesamiento de documentos: {e}")
            return None

    def create_vectorstore(self, documents: List[Document]):
        try:
            from langchain_community.vectorstores import FAISS
            import os
            print(f"🧠 Generando embeddings y vectorstore...")
            db_path = self.db_path
            index_path = os.path.join(db_path, "index.faiss")
            store_path = os.path.join(db_path, "index.pkl")
            if os.path.exists(index_path) and os.path.exists(store_path):
                print(f"🔄 Vectorstore existente encontrado, cargando y agregando nuevos documentos...")
                vectorstore = FAISS.load_local(db_path, self.embeddings, allow_dangerous_deserialization=True)
                vectorstore.add_documents(documents)
            else:
                print(f"🆕 No existe vectorstore, creando uno nuevo...")
                vectorstore = FAISS.from_documents(documents, self.embeddings)
            return vectorstore
        except Exception as e:
            print(f"❌ ERROR creando vectorstore: {e}")
            return None

    def save_vectorstore(self, vectorstore) -> bool:
        try:
            print(f"💾 Guardando vectorstore en disco...")
            vectorstore.save_local(self.db_path)
            print(f"   ✅ Vectorstore guardado en {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ ERROR guardando vectorstore: {e}")
            return False

    def ingest_ocr(self, image_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> bool:
        # Pipeline lineal igual a ingest_pdf
        documents = self.load_ocr_image(image_path)
        if not documents:
            return False
        processed_docs = self.process_documents(documents, chunk_size, chunk_overlap)
        if not processed_docs:
            return False
        vectorstore = self.create_vectorstore(processed_docs)
        if not vectorstore:
            return False
        return self.save_vectorstore(vectorstore)

# Wrapper CLI/test

def ingest_ocr_simple(image_path: str, db_path: str = "vectorstore_faiss") -> bool:
    ingestor = OCRIngestor(db_path=db_path)
    return ingestor.ingest_ocr(image_path)
