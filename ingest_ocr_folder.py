# ingest_ocr_folder.py
"""
OCR Folder Ingestor: Procesa múltiples imágenes de una carpeta mediante OCR.

Este módulo permite ingestar todas las imágenes de una carpeta directamente,
procesándolas con Mistral OCR y agregándolas al vectorstore existente
(o creándolo si no existe).

Uso:
    python ingest_ocr_folder.py data/imagenes/
    python ingest_ocr_folder.py ./mis_documentos
"""
import os
import sys
from typing import List

# Importar desde los módulos existentes
from ingest_ocr import OCRIngestor


class OCRFolderIngestor:
    """Procesador de múltiples imágenes para OCR."""
    
    def __init__(self, db_path: str = "vectorstore_faiss"):
        self.db_path = db_path
        self.ingestor = OCRIngestor(db_path=db_path)
    
    def get_image_files(self, folder_path: str) -> List[str]:
        """
        Obtiene todas las imágenes de una carpeta.
        
        Args:
            folder_path: Ruta a la carpeta con imágenes
            
        Returns:
            Lista de rutas de imágenes encontradas
        """
        # Extensiones de imagen soportadas
        image_extensions = ('.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp')
        
        if not os.path.isdir(folder_path):
            print(f"❌ La ruta no es una carpeta: {folder_path}")
            return []
        
        imagenes = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(image_extensions):
                full_path = os.path.join(folder_path, filename)
                imagenes.append(full_path)
        
        return sorted(imagenes)
    
    def ingest_folder(self, folder_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> bool:
        """
        Procesa todas las imágenes de una carpeta mediante OCR y las agrega al vectorstore.
        
        Args:
            folder_path: Ruta a la carpeta con imágenes
            chunk_size: Tamaño de fragmento de texto
            chunk_overlap: Superposición entre fragmentos
            
        Returns:
            True si fue exitoso, False en caso contrario
        """
        # 1. Encontrar todas las imágenes
        imagenes = self.get_image_files(folder_path)
        
        if not imagenes:
            print(f"❌ No se encontraron imágenes en: {folder_path}")
            print(f"   Extensiones soportadas: jpg, jpeg, png, tiff, bmp, gif, webp")
            return False
        
        print(f"\n🖼️  === PROCESANDO CARPETA ===")
        print(f"📁 Carpeta: {folder_path}")
        print(f"📊 Imágenes encontradas: {len(imagenes)}")
        print(f"=" * 40)
        
        # 2. Procesar cada imagen y acumular documentos
        todos_documentos = []
        errores = 0
        exitos = 0
        
        for idx, img_path in enumerate(imagenes, 1):
            print(f"\n[{idx}/{len(imagenes)}] Procesando: {os.path.basename(img_path)}")
            
            docs = self.ingestor.load_ocr_image(img_path)
            
            if docs:
                todos_documentos.extend(docs)
                exitos += 1
                print(f"   ✅ OCR exitoso")
            else:
                errores += 1
                print(f"   ❌ Error en OCR")
        
        if not todos_documentos:
            print(f"\n❌ No se pudieron procesar documentos")
            return False
        
        print(f"\n📊 === RESUMEN ===")
        print(f"   Imágenes procesadas: {exitos}/{len(imagenes)}")
        print(f"   Documentos totales: {len(todos_documentos)}")
        print(f"   Errores: {errores}")
        print(f"=" * 40)
        
        # 3. Procesar documentos (fragmentar, metadatos, resúmenes)
        print(f"\n✂️  Fragmentando texto y agregando metadatos...")
        processed_docs = self.ingestor.process_documents(
            todos_documentos, 
            chunk_size, 
            chunk_overlap
        )
        
        if not processed_docs:
            print(f"❌ Error al procesar documentos")
            return False
        
        print(f"   ✅ Total fragmentos: {len(processed_docs)}")
        
        # 4. Crear/actualizar vectorstore
        print(f"\n🧠 Generando embeddings...")
        vectorstore = self.ingestor.create_vectorstore(processed_docs)
        
        if not vectorstore:
            print(f"❌ Error al crear vectorstore")
            return False
        
        # 5. Guardar
        print(f"\n💾 Guardando vectorstore...")
        resultado = self.ingestor.save_vectorstore(vectorstore)
        
        if resultado:
            print(f"\n" + "=" * 40)
            print(f"✅ === PROCESO COMPLETADO ===")
            print(f"   ✅ Vectorstore actualizado")
            print(f"   📁 Ubicación: {self.db_path}")
            print(f"=" * 40)
        else:
            print(f"\n❌ Error al guardar vectorstore")
        
        return resultado


def main():
    """Entry point para uso desde CLI."""
    
    # Obtener ruta de carpeta
    if len(sys.argv) < 2:
        print("Usage: python ingest_ocr_folder.py <carpeta>")
        print("Example: python ingest_ocr_folder.py data/imagenes/")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    # Validar que existe
    if not os.path.exists(folder_path):
        print(f"❌ La carpeta no existe: {folder_path}")
        sys.exit(1)
    
    if not os.path.isdir(folder_path):
        print(f"❌ La ruta no es una carpeta: {folder_path}")
        sys.exit(1)
    
    # Ejecutar ingestión
    print(f"\n🚀 Iniciando ingestión de carpeta...")
    print(f"=" * 50)
    
    ingestor = OCRFolderIngestor(db_path="vectorstore_faiss")
    resultado = ingestor.ingest_folder(folder_path)
    
    if resultado:
        print(f"\n🎉 ¡Éxito! Carpet procesada correctamente")
        sys.exit(0)
    else:
        print(f"\n💥 Error en el procesamiento")
        sys.exit(1)


if __name__ == "__main__":
    main()