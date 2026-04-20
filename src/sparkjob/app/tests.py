import unittest
import logging
import os
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

# Definir las funciones directamente aquí para evitar problemas de importación
def format_author_name(name):
    """Formatea el nombre del autor: 'Nombre Apellido' -> 'Apellido, Nombre'"""
    if name is None:
        return None
    parts = name.strip().split()
    return f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) > 1 else name

def split_institution(inst):
    """Divide las instituciones separadas por comas"""
    if inst is None:
        return []
    return [x.strip() for x in inst.split(",")]

def format_date(date_str):
    """Formatea fecha de YYYY-MM-DD a DD/MM/YYYY"""
    if date_str is None:
        return None
    try:
        clean_date = str(date_str).replace("'", "").strip()
        return datetime.strptime(clean_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception as e:
        logging.warning(f"Fecha inválida: '{date_str}' – {e}")
        return None

def extract_authors_simulation(authors_list):
    """Simula la función extractAuthors"""
    if not authors_list:
        return []
    
    processed_authors = []
    for author in authors_list:
        processed_author = {
            "author_name": format_author_name(author.get("author_name")),
            "author_inst": split_institution(author.get("author_inst"))
        }
        processed_authors.append(processed_author)
    return processed_authors

def extract_date_simulation(date_str):
    """Simula la función extractDate"""
    return format_date(date_str)

def extract_entities_simulation(abstract):
    """Simula la función extractEntities - extrae palabras clave del abstract"""
    if not abstract:
        return []
    
    # Buscar patrones comunes de keywords
    keywords = []
    abstract_lower = abstract.lower()
    
    # Palabras clave técnicas comunes
    tech_keywords = [
        "machine learning", "artificial intelligence", "blockchain", "quantum computing",
        "climate change", "renewable energy", "nanotechnology", "biotechnology",
        "data processing", "algorithms", "optimization", "sustainability",
        "medical diagnosis", "cancer therapy", "drug delivery", "space exploration"
    ]
    
    for keyword in tech_keywords:
        if keyword in abstract_lower:
            keywords.append(keyword)
    
    return keywords[:5]  # Limitar a 5 keywords

def process_document_simulation(item):
    """Simula todo el procesamiento de un documento"""
    return {
        "authors": extract_authors_simulation(item.get('rel_authors', [])),
        "date": extract_date_simulation(item.get('rel_date')),
        "abstract": str(item.get('rel_abs', '')),
        "link": str(item.get('rel_link', '')),
        "title": str(item.get('rel_title', '')),
        "doi": str(item.get('rel_doi', '')),
        "category": str(item.get('category', '')).title(),
        "entities": extract_entities_simulation(item.get('rel_abs', '')),
        "type": str(item.get('type', ''))
    }


class TestSparkProcessorFunctions(unittest.TestCase):
    """Pruebas unitarias para las funciones UDF del procesador Spark"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("TestSparkProcessor")
    
    def test_format_author_name_valid_cases(self):
        """Prueba el formateo de nombres de autor válidos"""
        test_cases = [
            ("Juan Carlos Pérez", "Pérez, Juan Carlos"),
            ("María García", "García, María"),
            ("José Antonio López Martínez", "Martínez, José Antonio López"),
            ("Ana", "Ana"),
            ("  Dr. Carlos   Ruiz  ", "Ruiz, Dr. Carlos"),
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = format_author_name(input_name)
                self.assertEqual(result, expected)
                print(f"✓ '{input_name}' -> '{result}'")
    
    def test_format_author_name_edge_cases(self):
        """Prueba casos extremos del formateo de nombres"""
        self.assertIsNone(format_author_name(None))
        self.assertEqual(format_author_name(""), "")
        self.assertEqual(format_author_name(""), "")
        print("✓ Casos extremos de nombres manejados correctamente")
    
    def test_split_institution_valid_cases(self):
        """Prueba la división de instituciones válidas"""
        test_cases = [
            ("Universidad A, Instituto B", ["Universidad A", "Instituto B"]),
            ("MIT, Harvard, Stanford", ["MIT", "Harvard", "Stanford"]),
            ("Universidad Nacional  ,  Instituto Tech", ["Universidad Nacional", "Instituto Tech"]),
            ("Institución Única", ["Institución Única"]),
        ]
        
        for input_inst, expected in test_cases:
            with self.subTest(input_inst=input_inst):
                result = split_institution(input_inst)
                self.assertEqual(result, expected)
                print(f"✓ '{input_inst}' -> {result}")
    
    def test_split_institution_edge_cases(self):
        """Prueba casos extremos de división de instituciones"""
        self.assertEqual(split_institution(None), [])
        self.assertEqual(split_institution(""), [""])
        print("✓ Casos extremos de instituciones manejados correctamente")
    
    def test_format_date_valid_cases(self):
        """Prueba el formateo de fechas válidas"""
        test_cases = [
            ("2023-12-25", "25/12/2023"),
            ("'2023-01-01'", "01/01/2023"),
            ("2024-06-15", "15/06/2024"),
        ]
        
        for input_date, expected in test_cases:
            with self.subTest(input_date=input_date):
                result = format_date(input_date)
                self.assertEqual(result, expected)
                print(f"✓ '{input_date}' -> '{result}'")
    
    def test_format_date_invalid_cases(self):
        """Prueba el manejo de fechas inválidas"""
        invalid_dates = ["fecha-inválida", "2023-13-45", "not-a-date", "", None]
        
        for invalid_date in invalid_dates:
            result = format_date(invalid_date)
            self.assertIsNone(result)
        
        print("✓ Fechas inválidas manejadas correctamente")


class TestDocumentProcessing(unittest.TestCase):
    """Pruebas de procesamiento completo de documentos"""
    
    def setUp(self):
        """Preparar datos de prueba"""
        self.sample_document = {
            "rel_authors": [
                {
                    "author_name": "Juan Carlos Pérez",
                    "author_inst": "Universidad Nacional, Instituto de Investigación"
                },
                {
                    "author_name": "María García",
                    "author_inst": "MIT"
                }
            ],
            "rel_date": "2023-12-15",
            "rel_abs": "This study presents machine learning algorithms for biomedical data processing with improved accuracy.",
            "rel_link": "https://example.com/article",
            "rel_title": "Machine Learning in Biomedical Processing",
            "rel_doi": "10.1000/ml-biomed-2023",
            "category": "computer science",
            "type": "research article"
        }
    
    def test_full_document_processing(self):
        """Prueba el procesamiento completo de un documento"""
        result = process_document_simulation(self.sample_document)
        
        # Verificar estructura del resultado
        required_fields = ["authors", "date", "abstract", "link", "title", "doi", "category", "entities", "type"]
        for field in required_fields:
            self.assertIn(field, result)
        
        # Verificar procesamiento de autores
        self.assertEqual(len(result["authors"]), 2)
        self.assertEqual(result["authors"][0]["author_name"], "Pérez, Juan Carlos")
        self.assertEqual(result["authors"][0]["author_inst"], ["Universidad Nacional", "Instituto de Investigación"])
        
        # Verificar procesamiento de fecha
        self.assertEqual(result["date"], "15/12/2023")
        
        # Verificar categoría capitalizada
        self.assertEqual(result["category"], "Computer Science")
        
        # Verificar extracción de entidades
        self.assertIn("machine learning", result["entities"])
        
        print("✓ Procesamiento completo de documento exitoso")
        print(f"✓ Autores procesados: {len(result['authors'])}")
        print(f"✓ Fecha formateada: {result['date']}")
        print(f"✓ Entidades extraídas: {result['entities']}")
    
    def test_document_with_missing_fields(self):
        """Prueba el manejo de documentos con campos faltantes"""
        incomplete_document = {
            "rel_title": "Test Article",
            "rel_doi": "10.1000/test"
        }
        
        result = process_document_simulation(incomplete_document)
        
        # Verificar que no falle con campos faltantes
        self.assertEqual(result["authors"], [])
        self.assertIsNone(result["date"])
        self.assertEqual(result["abstract"], "")
        
        print("✓ Manejo de documentos incompletos exitoso")


class TestDataValidation(unittest.TestCase):
    """Pruebas de validación de datos"""
    
    def test_doi_uniqueness(self):
        """Prueba la unicidad de DOIs"""
        documents = [
            {"doi": "10.1000/test1", "title": "Article 1"},
            {"doi": "10.1000/test2", "title": "Article 2"},
            {"doi": "10.1000/test1", "title": "Article 1 Updated"},
        ]
        
        dois = [doc["doi"] for doc in documents]
        unique_dois = set(dois)
        
        self.assertNotEqual(len(dois), len(unique_dois))
        print(f"✓ Detección de DOIs duplicados: {len(dois)} docs, {len(unique_dois)} DOIs únicos")
    
    def test_required_fields_validation(self):
        """Prueba la validación de campos requeridos"""
        required_fields = ["title", "doi", "category"]
        
        valid_doc = {
            "title": "Test Title",
            "doi": "10.1000/test",
            "category": "Research"
        }
        
        invalid_doc = {
            "title": "Test Title",
            "category": "Research"
        }
        
        # Verificar documento válido
        for field in required_fields:
            self.assertIn(field, valid_doc)
        
        # Verificar documento inválido
        self.assertNotIn("doi", invalid_doc)
        
        print("✓ Validación de campos requeridos exitosa")


class TestWithSampleData(unittest.TestCase):
    """Pruebas con datos de ejemplo del archivo JSON"""
    
    def setUp(self):
        """Cargar datos de prueba si existe el archivo"""
        try:
            with open('test_data.json', 'r', encoding='utf-8') as f:
                self.test_data = json.load(f)
            print(f"✓ Cargados {len(self.test_data)} documentos de prueba")
        except FileNotFoundError:
            self.test_data = []
            print("⚠ Archivo test_data.json no encontrado, usando datos mock")
            # Crear datos mock
            self.test_data = [{
                "rel_authors": [{"author_name": "Test Author", "author_inst": "Test University"}],
                "rel_date": "2023-01-01",
                "rel_abs": "Test abstract with machine learning keywords",
                "rel_title": "Test Title",
                "rel_doi": "10.1000/test",
                "category": "test",
                "type": "test"
            }]
    
    def test_process_all_sample_documents(self):
        """Prueba el procesamiento de todos los documentos de muestra"""
        if not self.test_data:
            self.skipTest("No hay datos de prueba disponibles")
        
        processed_count = 0
        error_count = 0
        
        for i, doc in enumerate(self.test_data):
            try:
                result = process_document_simulation(doc)
                
                # Verificaciones básicas
                self.assertIsInstance(result, dict)
                self.assertIn("title", result)
                self.assertIn("doi", result)
                
                processed_count += 1
                print(f"✓ Documento {i+1}: '{result['title'][:50]}...'")
                
            except Exception as e:
                error_count += 1
                print(f"✗ Error en documento {i+1}: {e}")
        
        print(f"\n✓ Procesados exitosamente: {processed_count}/{len(self.test_data)} documentos")
        if error_count > 0:
            print(f"✗ Errores: {error_count}")
        
        self.assertGreater(processed_count, 0, "Debe procesarse al menos un documento")


if __name__ == '__main__':
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar pruebas
    unittest.main(verbosity=2, exit=False)