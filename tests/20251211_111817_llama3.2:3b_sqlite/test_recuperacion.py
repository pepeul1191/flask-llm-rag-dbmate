# test_recuperacion.py - Pruebas de recuperación con SQLite3

import os
import json
import sqlite3
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer

# =========================================================
# CONFIGURACIÓN
# =========================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

SQLITE_PATH = os.path.join(BASE_PATH, "rag_system.db")
RESULTS_DIR = os.path.join(CURRENT_DIR, "evaluation_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# =========================================================
# CLASE DE BÚSQUEDA VECTORIAL
# =========================================================

class VectorSearchSQLite:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.model = SentenceTransformer(EMBEDDING_MODEL)
    
    def cosine_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        vec1 = np.array(emb1)
        vec2 = np.array(emb2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def search(self, query_text: str, k: int = 10) -> List[Tuple[str, str, float, Dict]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query_embedding = self.model.encode(query_text).tolist()
        
        cursor.execute("""
            SELECT id, text, embedding, chunk_type, source_file, tables, relationship
            FROM chunks
        """)
        rows = cursor.fetchall()
        
        similarities = []
        for row in rows:
            chunk_id, chunk_text, embedding_bytes, chunk_type, source_file, tables, relationship = row
            chunk_embedding = np.frombuffer(embedding_bytes, dtype=np.float32).tolist()
            similarity = self.cosine_similarity(query_embedding, chunk_embedding)
            
            similarities.append({
                'id': chunk_id,
                'text': chunk_text,
                'similarity': similarity,
                'chunk_type': chunk_type,
                'source_file': source_file,
                'tables': tables,
                'relationship': relationship
            })
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        conn.close()
        
        results = []
        for item in similarities[:k]:
            results.append((
                item['id'],
                item['text'],
                item['similarity'],
                {
                    'chunk_type': item['chunk_type'],
                    'source_file': item['source_file'],
                    'tables': item['tables'],
                    'relationship': item['relationship']
                }
            ))
        
        return results


# =========================================================
# FUNCIÓN DE RELEVANCIA
# =========================================================

def is_relevant_chunk(
    chunk_text: str,
    metadata: Dict,
    required_tables: set,
    required_relationships: set
) -> bool:
    """Determina si un chunk es relevante"""
    text = chunk_text.lower()
    tables_field = metadata.get('tables', '').lower()
    
    for table in required_tables:
        if re.search(rf'create\s+table\s+{re.escape(table)}\b', text):
            return True
        if table in tables_field.split(','):
            return True
        if table in text and 'create table' in text:
            return True
    
    for a, b in required_relationships:
        if re.search(rf'foreign\s+key.*references\s+{re.escape(a)}', text):
            return True
        if re.search(rf'foreign\s+key.*references\s+{re.escape(b)}', text):
            return True
    
    return False


def get_relevance_vector(
    results: List[Tuple],
    required_tables: set,
    required_relationships: set
) -> List[int]:
    """Genera vector de relevancia"""
    relevance = []
    for chunk_id, chunk_text, similarity, metadata in results:
        if is_relevant_chunk(chunk_text, metadata, required_tables, required_relationships):
            relevance.append(1)
        else:
            relevance.append(0)
    return relevance


# =========================================================
# MÉTRICAS
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


def ndcg_at_k(relevance: List[int], k: int) -> float:
    if k <= 0 or not relevance:
        return 0.0
    
    dcg = 0.0
    for i in range(min(k, len(relevance))):
        gain = relevance[i]
        if gain > 0:
            dcg += gain / np.log2(i + 2)
    
    ideal = sorted(relevance, reverse=True)
    idcg = 0.0
    for i in range(min(k, len(ideal))):
        gain = ideal[i]
        if gain > 0:
            idcg += gain / np.log2(i + 2)
    
    return dcg / idcg if idcg > 0 else 0.0


def create_test_queries() -> List[Dict[str, Any]]:
    """Crea queries de prueba"""
    queries = []
    
    queries.append({
        "name": "✅ Tabla users",
        "text": "CREATE TABLE users con id, username, password, email",
        "required_tables": {"users"},
        "required_relationships": set(),
        "expected_min_relevant": 1
    })
    
    queries.append({
        "name": "✅ Tabla books",
        "text": "CREATE TABLE books con id, title, isbn, pages",
        "required_tables": {"books"},
        "required_relationships": set(),
        "expected_min_relevant": 1
    })
    
    queries.append({
        "name": "✅ Relación books-genres",
        "text": "tabla intermedia para libros y géneros con foreign keys",
        "required_tables": {"books_genres"},
        "required_relationships": {("books", "genres")},
        "expected_min_relevant": 1
    })
    
    queries.append({
        "name": "✅ Tabla reviews",
        "text": "tabla de reseñas con rating, comentario, foreign keys a users y books",
        "required_tables": {"reviews"},
        "required_relationships": set(),
        "expected_min_relevant": 1
    })
    
    queries.append({
        "name": "❌ Tabla inexistente",
        "text": "CREATE TABLE inventory con stock y location",
        "required_tables": {"inventory"},
        "required_relationships": set(),
        "expected_min_relevant": 0
    })
    
    queries.append({
        "name": "⚠️ Query ambigua - usuarios",
        "text": "guardar información de personas que usan el sistema",
        "required_tables": {"users"},
        "required_relationships": set(),
        "expected_min_relevant": 1
    })
    
    return queries


# =========================================================
# EVALUACIÓN PRINCIPAL
# =========================================================

def evaluate_system(k: int = 10) -> Dict[str, Any]:
    """Evalúa el sistema completo"""
    
    print(f"\n{'='*70}")
    print(f"📊 EVALUANDO SISTEMA RAG CON SQLITE3 (K={k})")
    print(f"{'='*70}\n")
    
    searcher = VectorSearchSQLite(SQLITE_PATH)
    queries = create_test_queries()
    results = []
    
    for query in queries:
        print(f"📝 {query['name']}")
        print(f"   Query: {query['text'][:80]}...")
        
        retrieved = searcher.search(query["text"], k)
        
        if not retrieved:
            print(f"   ❌ No se recuperaron chunks")
            results.append({
                "query_name": query["name"],
                "error": "No chunks retrieved"
            })
            continue
        
        relevance = get_relevance_vector(
            retrieved,
            query["required_tables"],
            query["required_relationships"]
        )
        
        total_relevant = sum(relevance)
        found_relevant = sum(relevance[:k])
        ap = average_precision(relevance)
        
        result = {
            "query_name": query["name"],
            "query_text": query["text"],
            "precision_at_k": precision_at_k(relevance, k),
            "recall_at_k": recall_at_k(relevance, total_relevant, k) if total_relevant > 0 else 1.0,
            "ap": ap,
            "ndcg": ndcg_at_k(relevance, k),
            "total_relevant": total_relevant,
            "found_relevant": found_relevant,
            "expected_min": query["expected_min_relevant"],
            "meets_expectation": found_relevant >= query["expected_min_relevant"],
            "relevance_vector": relevance[:k]
        }
        
        results.append(result)
        
        if result["meets_expectation"]:
            print(f"   ✅ OK: AP={result['ap']:.3f}, P@{k}={result['precision_at_k']:.3f}")
        else:
            print(f"   ⚠️ WARNING: Esperaba ≥{result['expected_min']}, obtuvo {result['found_relevant']}")
        print()
    
    # Métricas globales
    valid = [r for r in results if "error" not in r]
    positive = [r for r in valid if r["expected_min"] > 0]
    negative = [r for r in valid if r["expected_min"] == 0]
    
    global_metrics = {
        "k": k,
        "backend": "SQLite3",
        "total_queries": len(results),
        "valid_queries": len(valid),
        "mean_ap": np.mean([r["ap"] for r in valid]),
        "mean_precision": np.mean([r["precision_at_k"] for r in valid]),
        "mean_recall": np.mean([r["recall_at_k"] for r in valid]),
        "mean_ndcg": np.mean([r["ndcg"] for r in valid]),
        "positive_queries": len(positive),
        "positive_map": np.mean([r["ap"] for r in positive]) if positive else 0,
        "negative_queries": len(negative),
        "negative_false_positives": sum(1 for r in negative if r["found_relevant"] > 0),
        "expectation_rate": sum(1 for r in valid if r["meets_expectation"]) / len(valid) if valid else 0
    }
    
    return {
        "global_metrics": global_metrics,
        "per_query_results": results
    }


def print_report(evaluation: Dict[str, Any]):
    """Imprime reporte"""
    m = evaluation["global_metrics"]
    
    print(f"\n{'='*70}")
    print("📈 REPORTE DE RECUPERACIÓN - SQLITE3")
    print(f"{'='*70}\n")
    
    print(f"🎯 Backend: {m['backend']}")
    print(f"🎯 K={m['k']}")
    
    print(f"\n📊 MÉTRICAS GLOBALES:")
    print(f"   Mean Average Precision (MAP): {m['mean_ap']:.4f}")
    print(f"   Mean Precision@{m['k']}: {m['mean_precision']:.4f}")
    print(f"   Mean Recall@{m['k']}: {m['mean_recall']:.4f}")
    print(f"   Mean NDCG@{m['k']}: {m['mean_ndcg']:.4f}")
    
    print(f"\n📊 POR TIPO DE QUERY:")
    print(f"   Queries positivas ({m['positive_queries']}): MAP={m['positive_map']:.4f}")
    print(f"   Queries negativas ({m['negative_queries']}): False Positives={m['negative_false_positives']}")
    
    print(f"\n✅ Expectation Rate: {m['expectation_rate']:.2%}")


def save_results(evaluation: Dict[str, Any], timestamp: str, k: int):
    """Guarda resultados"""
    output = {
        "timestamp": timestamp,
        "k": k,
        "backend": "SQLite3",
        "global_metrics": {k: float(v) if isinstance(v, np.float64) else v 
                          for k, v in evaluation["global_metrics"].items()},
        "per_query_results": evaluation["per_query_results"]
    }
    
    filename = f"retrieval_sqlite_report_{timestamp}_k{k}.json"
    filepath = os.path.join(RESULTS_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados en: {filepath}")
    return filepath


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    import re
    
    print("\n" + "="*70)
    print("🔍 EVALUACIÓN DE RECUPERACIÓN CON SQLITE3")
    print("="*70)
    
    if not os.path.exists(SQLITE_PATH):
        print(f"❌ Base SQLite no existe: {SQLITE_PATH}")
        print("   Ejecute primero: python3 ingest_sqlite.py")
        exit(1)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for k in [5, 10, 20]:
        print(f"\n{'─'*70}")
        print(f"🔄 EVALUANDO CON K={k}")
        print(f"{'─'*70}")
        
        evaluation = evaluate_system(k=k)
        print_report(evaluation)
        save_results(evaluation, timestamp, k)
    
    print(f"\n✅ Evaluación completada")
    print(f"📁 Resultados en: {RESULTS_DIR}")