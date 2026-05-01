# tests.py
import os
import json
import re
import numpy as np
from typing import List, Tuple, Dict, Any
import chromadb

# =========================================================
# 1. RUTAS ABSOLUTAS
# =========================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_DIR = CURRENT_DIR
BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CHROMA_PATH = os.path.join(BASE_PATH, "chroma_db")
SCHEMA_PATH = os.path.join(RUN_DIR, "schema.puml")
MIGRATIONS_PATH = os.path.join(RUN_DIR, "migrations")

# =========================================================
# 2. CHROMA CLIENT
# =========================================================

client = chromadb.PersistentClient(path=CHROMA_PATH)
try:
    collection = client.get_collection("migrations")
except:
    print("❌ Colección 'migrations' no existe. Ejecute test_v2.py primero.")
    exit(1)

# =========================================================
# 3. FUNCIÓN DE RELEVANCIA MEJORADA
# =========================================================

def is_relevant_chunk(chunk, required_tables, required_relationships):
    text = chunk.lower()
    
    # Para queries negativas (required_tables vacío o tabla inexistente)
    if required_tables and list(required_tables)[0] not in text:
        # Si la tabla requerida NO está en el chunk, no es relevante
        return False
    
    # Resto de la lógica...
    for table in required_tables:
        if re.search(rf'create\s+table\s+{re.escape(table)}\b', text):
            return True
    
    return False


def get_all_relevant_chunks(
    chunks: List[str],
    required_tables: set,
    required_relationships: set
) -> List[int]:
    """Genera vector de relevancia"""
    return [
        1 if is_relevant_chunk(chunk, required_tables, required_relationships) 
        else 0 
        for chunk in chunks
    ]


# =========================================================
# 4. MÉTRICAS DE EVALUACIÓN
# =========================================================

def precision_at_k(relevance: List[int], k: int) -> float:
    if k <= 0 or not relevance:
        return 0.0
    return sum(relevance[:k]) / k


def recall_at_k(relevance: List[int], total_relevant: int, k: int) -> float:
    if total_relevant <= 0:
        return 0.0
    return sum(relevance[:k]) / total_relevant


def average_precision(relevance: List[int]) -> float:
    hits = 0
    sum_precisions = 0.0
    for i, rel in enumerate(relevance):
        if rel == 1:
            hits += 1
            sum_precisions += hits / (i + 1)
    return sum_precisions / hits if hits > 0 else 0.0


def mean_reciprocal_rank(relevance: List[int]) -> float:
    for i, rel in enumerate(relevance):
        if rel == 1:
            return 1.0 / (i + 1)
    return 0.0


def hit_rate(relevance_list: List[List[int]], k: int = 1) -> float:
    if not relevance_list:
        return 0.0
    hits = sum(1 for rel in relevance_list if sum(rel[:k]) > 0)
    return hits / len(relevance_list)


# =========================================================
# 5. QUERIES DE PRUEBA MEJORADAS
# =========================================================

def create_test_queries() -> List[Dict[str, Any]]:
    """Crea queries más efectivas para retrieval"""
    queries = []
    
    # Queries positivas con términos que coinciden mejor con el SQL
    queries.append({
        "name": "✅ Tabla users",
        "text": "CREATE TABLE users con id INT PRIMARY KEY, username VARCHAR, password VARCHAR, email VARCHAR",
        "required_tables": {"users"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "easy"
    })
    
    queries.append({
        "name": "✅ Tabla books",
        "text": "CREATE TABLE books con id, title VARCHAR, isbn VARCHAR, pages INT",
        "required_tables": {"books"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "easy"
    })
    
    queries.append({
        "name": "✅ Tabla genres",
        "text": "CREATE TABLE genres con id INT, name VARCHAR",
        "required_tables": {"genres"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "easy"
    })
    
    queries.append({
        "name": "✅ Relación books-genres",
        "text": "CREATE TABLE books_genres con book_id INT, genre_id INT, FOREIGN KEY",
        "required_tables": {"books_genres"},
        "required_relationships": {("books", "genres")},
        "expected_min_relevant": 1,
        "difficulty": "medium"
    })
    
    queries.append({
        "name": "✅ Tabla books_authors",
        "text": "CREATE TABLE books_authors con book_id INT, author_id INT",
        "required_tables": {"books_authors"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "medium"
    })
    
    queries.append({
        "name": "✅ Múltiples tablas",
        "text": "CREATE TABLE books, CREATE TABLE authors, CREATE TABLE books_authors con book_id y author_id",
        "required_tables": {"books", "authors", "books_authors"},
        "required_relationships": {("books", "authors")},
        "expected_min_relevant": 2,
        "difficulty": "hard"
    })
    
    queries.append({
        "name": "✅ Tabla reviews",
        "text": "CREATE TABLE reviews con rating INT, comment TEXT, review_date DATETIME, FOREIGN KEY user_id, book_id",
        "required_tables": {"reviews"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "easy"
    })
    
    # Queries negativas
    queries.append({
        "name": "❌ Tabla inexistente",
        "text": "CREATE TABLE inventory con stock INT, location VARCHAR",
        "required_tables": {"inventory"},
        "required_relationships": set(),
        "expected_min_relevant": 0,
        "difficulty": "negative"
    })
    
    queries.append({
        "name": "❌ Tabla shopping_cart",
        "text": "CREATE TABLE shopping_cart con user_id INT, product_id INT",
        "required_tables": {"shopping_cart"},
        "required_relationships": set(),
        "expected_min_relevant": 0,
        "difficulty": "negative"
    })
    
    queries.append({
        "name": "⚠️ Query ambigua",
        "text": "tabla para guardar información de personas que usan el sistema con email y contraseña",
        "required_tables": {"users"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "hard"
    })
    
    return queries


# =========================================================
# 6. FUNCIONES DE EVALUACIÓN
# =========================================================

def retrieve_chunks(query_text: str, k: int = 10) -> List[str]:
    """Recupera chunks desde ChromaDB"""
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=k
        )
        return results["documents"][0] if results["documents"] else []
    except Exception as e:
        print(f"Error en retrieve: {e}")
        return []


def evaluate_single_query(query: Dict[str, Any], k: int = 10) -> Dict[str, Any]:
    """Evalúa una única query"""
    chunks = retrieve_chunks(query["text"], k)
    
    if not chunks:
        return {
            "query_name": query["name"],
            "precision@k": 0.0,
            "recall@k": 0.0,
            "ap": 0.0,
            "mrr": 0.0,
            "found_relevant": 0,
            "expected_min": query.get("expected_min_relevant", 0),
            "meets_expectation": False,
            "error": "No chunks retrieved"
        }
    
    relevance = get_all_relevant_chunks(
        chunks,
        query["required_tables"],
        query["required_relationships"]
    )
    
    total_relevant = sum(relevance)
    found_relevant = sum(relevance[:k])
    
    return {
        "query_name": query["name"],
        "query_text": query["text"],
        "difficulty": query.get("difficulty", "unknown"),
        "precision@k": precision_at_k(relevance, k),
        "recall@k": recall_at_k(relevance, total_relevant, k) if total_relevant > 0 else 1.0,
        "ap": average_precision(relevance),
        "mrr": mean_reciprocal_rank(relevance),
        "total_relevant": total_relevant,
        "found_relevant": found_relevant,
        "expected_min": query.get("expected_min_relevant", 0),
        "meets_expectation": found_relevant >= query.get("expected_min_relevant", 0),
    }


def evaluate_system(k: int = 10) -> Dict[str, Any]:
    """Evalúa el sistema completo"""
    test_queries = create_test_queries()
    results = []
    
    print(f"\n{'='*70}")
    print(f"📊 EVALUANDO SISTEMA RAG (K={k})")
    print(f"{'='*70}\n")
    
    for query in test_queries:
        print(f"📝 {query['name']}")
        print(f"   Query: {query['text'][:80]}...")
        
        result = evaluate_single_query(query, k)
        results.append(result)
        
        if result.get("error"):
            print(f"   ❌ ERROR: {result['error']}")
        elif result["meets_expectation"]:
            print(f"   ✅ OK: AP={result['ap']:.3f}, Precision@{k}={result['precision@k']:.3f}")
        else:
            print(f"   ⚠️ WARNING: Esperaba ≥{result['expected_min']}, obtuvo {result['found_relevant']}")
        print()
    
    # Métricas globales
    positive_results = [r for r in results if r["expected_min"] > 0 and not r.get("error")]
    negative_results = [r for r in results if r["expected_min"] == 0 and not r.get("error")]
    
    global_metrics = {
        "total_queries": len(results),
        "mean_ap": np.mean([r["ap"] for r in results if not r.get("error")]),
        "mean_precision": np.mean([r["precision@k"] for r in results if not r.get("error")]),
        "mrr": np.mean([r["mrr"] for r in results if not r.get("error")]),
        "positive_queries_count": len(positive_results),
        "positive_mean_ap": np.mean([r["ap"] for r in positive_results]) if positive_results else 0,
        "negative_false_positives": sum(1 for r in negative_results if r["found_relevant"] > 0),
        "expectations_met": sum(1 for r in results if r.get("meets_expectation", False)),
        "expectation_rate": sum(1 for r in results if r.get("meets_expectation", False)) / len(results) if results else 0,
    }
    
    return {"global_metrics": global_metrics, "per_query_results": results}


def print_report(evaluation: Dict[str, Any], k: int):
    """Imprime reporte"""
    metrics = evaluation["global_metrics"]
    
    print(f"\n{'='*70}")
    print(f"📈 REPORTE DETALLADO (K={k})")
    print(f"{'='*70}\n")
    
    print("🎯 MÉTRICAS GLOBALES:")
    print(f"   Mean Average Precision (MAP): {metrics['mean_ap']:.4f}")
    print(f"   Mean Precision@{k}: {metrics['mean_precision']:.4f}")
    print(f"   MRR: {metrics['mrr']:.4f}")
    print(f"   Expectation Rate: {metrics['expectation_rate']:.2%}")
    
    print(f"\n📊 POR TIPO DE QUERY:")
    print(f"   Positivas ({metrics['positive_queries_count']}):")
    print(f"     - MAP: {metrics['positive_mean_ap']:.4f}")
    
    print(f"\n   Negativas:")
    print(f"     - False Positives: {metrics['negative_false_positives']}")
    
    print(f"\n⚠️ QUERIES PROBLEMÁTICAS:")
    for res in evaluation["per_query_results"]:
        if not res.get("meets_expectation", True) and not res.get("error"):
            print(f"   - {res['query_name']}: Esperaba ≥{res['expected_min']}, obtuvo {res['found_relevant']}")


# =========================================================
# 7. MAIN
# =========================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔍 DIAGNÓSTICO Y EVALUACIÓN DEL SISTEMA RAG")
    print("="*70)
    
    # Verificar chunks en ChromaDB
    all_docs = collection.get()
    total_chunks = len(all_docs['documents']) if all_docs and all_docs['documents'] else 0
    print(f"\n💾 Total de chunks en ChromaDB: {total_chunks}")
    
    if total_chunks == 0:
        print("❌ No hay chunks en ChromaDB. Ejecute test_v2.py primero.")
        exit(1)
    
    # Evaluar con diferentes K
    for k in [5, 10, 20]:
        print(f"\n{'─'*70}")
        print(f"🔄 EVALUANDO CON K={k}")
        print(f"{'─'*70}")
        
        evaluation = evaluate_system(k=k)
        print_report(evaluation, k)
    
    print("\n✅ Diagnóstico y evaluación completados")