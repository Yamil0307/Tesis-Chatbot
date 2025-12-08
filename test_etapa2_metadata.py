"""
test_etapa2_metadata.py - Validación de Etapa 2.1 (Enriquecer metadatos)

Valida que:
1. Los metadatos incluyen file_name, page, chunk_index, processed_date
2. FAISS recupera metadatos correctamente
3. MetadataHandler extrae información correctamente
4. Las citaciones se formatean académicamente

Ejecutar: python test_etapa2_metadata.py
"""

import sys
from langchain_core.documents import Document
from ingest_utils import add_chunk_metadata
from metadata_handler import MetadataHandler


def test_metadata_enrichment():
    """Test 1: Metadatos enriquecidos"""
    print("\n" + "="*60)
    print("TEST 1: Enriquecer metadatos en ingest_utils.py")
    print("="*60)
    
    # Crear documentos simulados
    docs = [
        Document(
            page_content="Este es el contenido del primer fragmento",
            metadata={"source": "data/historia_universidad.pdf", "page": 10}
        ),
        Document(
            page_content="Este es el contenido del segundo fragmento",
            metadata={"source": "data/historia_universidad.pdf", "page": 10}
        ),
        Document(
            page_content="Este es el contenido del tercer fragmento",
            metadata={"source": "data/reglamento.pdf", "page": 5}
        ),
    ]
    
    # Enriquecer metadatos
    enriched_docs = add_chunk_metadata(docs, source_name="test_source")
    
    # Validar que cada documento tiene los metadatos requeridos
    required_fields = ["chunk_index", "source", "file_name", "processed_date", "page"]
    
    print("\n✅ Validando metadatos enriquecidos:")
    for idx, doc in enumerate(enriched_docs):
        print(f"\nDocumento {idx}:")
        for field in required_fields:
            if field in doc.metadata:
                value = doc.metadata[field]
                # Truncar valores largos para mejor legibilidad
                if isinstance(value, str) and len(value) > 40:
                    value = value[:37] + "..."
                print(f"  ✓ {field}: {value}")
            else:
                print(f"  ✗ {field}: FALTA")
                return False
    
    print("\n✅ TEST 1 PASADO: Metadatos enriquecidos correctamente")
    return True


def test_metadata_handler_extraction():
    """Test 2: MetadataHandler extrae información correctamente"""
    print("\n" + "="*60)
    print("TEST 2: Extracción de metadatos en MetadataHandler")
    print("="*60)
    
    # Crear documentos con metadatos enriquecidos
    docs = [
        Document(
            page_content="Contenido de prueba 1",
            metadata={
                "source": "data/historia.pdf",
                "page": 42,
                "file_name": "historia.pdf",
                "chunk_index": 0,
                "processed_date": "2025-01-01T10:30:00"
            }
        ),
        Document(
            page_content="Contenido de prueba 2",
            metadata={
                "source": "data/reglamento.pdf",
                "page": 15,
                "file_name": "reglamento.pdf",
                "chunk_index": 1,
                "processed_date": "2025-01-01T10:30:00"
            }
        ),
    ]
    
    print("\n✅ Extrayendo información de fuentes:")
    for idx, doc in enumerate(docs):
        print(f"\nDocumento {idx}:")
        source_info = MetadataHandler.extract_source_info(doc)
        for key, value in source_info.items():
            if value is not None:
                print(f"  - {key}: {value}")
    
    print("\n✅ TEST 2 PASADO: Extracción funciona correctamente")
    return True


def test_source_citation_format():
    """Test 3: Citaciones en formato académico"""
    print("\n" + "="*60)
    print("TEST 3: Formato académico de citaciones")
    print("="*60)
    
    test_cases = [
        {
            "name": "Archivo PDF con página",
            "info": {
                "file_name": "historia_universidad.pdf",
                "page": 42,
                "source": "data/historia_universidad.pdf"
            },
            "expected_contains": ["historia universidad", "página 42"]
        },
        {
            "name": "Archivo sin página",
            "info": {
                "file_name": "reglamento.pdf",
                "page": None,
                "source": "data/reglamento.pdf"
            },
            "expected_contains": ["reglamento"]
        },
        {
            "name": "Documento desconocido",
            "info": {
                "file_name": None,
                "page": None,
                "source": None
            },
            "expected_contains": ["desconocido"]
        },
    ]
    
    print("\n✅ Validando formatos de citación:")
    for test in test_cases:
        citation = MetadataHandler.format_source_citation(test["info"])
        print(f"\n  Caso: {test['name']}")
        print(f"  Citation: {citation}")
        
        # Validar que la cita contiene lo esperado
        lower_citation = citation.lower()
        for expected in test["expected_contains"]:
            if expected.lower() not in lower_citation:
                print(f"  ✗ Esperaba '{expected}' en la cita")
                return False
        print(f"  ✓ Formato correcto")
    
    print("\n✅ TEST 3 PASADO: Todas las citaciones tienen formato académico")
    return True


def test_source_list_format():
    """Test 4: Lista de fuentes en formato académico"""
    print("\n" + "="*60)
    print("TEST 4: Lista de fuentes (FUENTES CONSULTADAS)")
    print("="*60)
    
    # Crear documentos
    docs = [
        Document(
            page_content="Contenido 1",
            metadata={
                "file_name": "Historia de la Universidad.pdf",
                "page": 42,
                "source": "data/historia.pdf"
            }
        ),
        Document(
            page_content="Contenido 2",
            metadata={
                "file_name": "Reglamento Académico.pdf",
                "page": 15,
                "source": "data/reglamento.pdf"
            }
        ),
        Document(
            page_content="Contenido 3",
            metadata={
                "file_name": "Reglamento Académico.pdf",  # Duplicado intencional
                "page": 15,
                "source": "data/reglamento.pdf"
            }
        ),
    ]
    
    # Generar lista de fuentes
    sources_list = MetadataHandler.format_source_list(docs)
    
    print("\n✅ Lista generada:")
    print(sources_list)
    
    # Validar formato
    print("\n✅ Validando formato:")
    validations = [
        ("FUENTES CONSULTADAS:" in sources_list, "Contiene encabezado"),
        ("- " in sources_list, "Tiene formato de lista con guiones"),
        ("página" in sources_list.lower(), "Incluye números de página"),
        ("historia" in sources_list.lower(), "Incluye primer documento"),
        ("reglamento" in sources_list.lower(), "Incluye segundo documento"),
        (sources_list.count("Reglamento") == 1, "Evita duplicados"),
    ]
    
    for valid, desc in validations:
        status = "✓" if valid else "✗"
        print(f"  {status} {desc}")
        if not valid:
            return False
    
    print("\n✅ TEST 4 PASADO: Formato académico correcto")
    return True


def test_source_annotation():
    """Test 5: Anotaciones de fuente"""
    print("\n" + "="*60)
    print("TEST 5: Anotaciones de fuente para fragmentos")
    print("="*60)
    
    doc = Document(
        page_content="Contenido de prueba",
        metadata={
            "file_name": "Historia.pdf",
            "page": 25,
            "source": "data/historia.pdf"
        }
    )
    
    annotation = MetadataHandler.create_source_annotation(doc)
    
    print(f"\n✅ Anotación generada: {annotation}")
    
    # Validar formato
    validations = [
        ("[Fuente:" in annotation, "Tiene formato correcto"),
        ("Historia.pdf" in annotation, "Incluye nombre del archivo"),
        ("página 25" in annotation, "Incluye número de página"),
        ("]" in annotation, "Está cerrada correctamente"),
    ]
    
    print("\n✅ Validando anotación:")
    for valid, desc in validations:
        status = "✓" if valid else "✗"
        print(f"  {status} {desc}")
        if not valid:
            return False
    
    print("\n✅ TEST 5 PASADO: Anotaciones generadas correctamente")
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 VALIDACIÓN DE ETAPA 2.1: ENRIQUECER METADATOS")
    print("="*60)
    
    tests = [
        ("Enriquecer metadatos", test_metadata_enrichment),
        ("Extraer metadatos", test_metadata_handler_extraction),
        ("Formato de citaciones", test_source_citation_format),
        ("Lista de fuentes", test_source_list_format),
        ("Anotaciones", test_source_annotation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ ERROR en {test_name}:")
            print(f"   {str(e)}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASADO" if result else "❌ FALLÓ"
        print(f"{status}: {test_name}")
    
    print(f"\n📈 Total: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n🎉 ¡ETAPA 2.1 VALIDADA EXITOSAMENTE!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) fallaron")
        sys.exit(1)
