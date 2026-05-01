# test_recuperacion_postgres_schema.py - Versión corregida

import os
import json
import re
import psycopg2
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer

# =========================================================
# CONFIGURACIÓN
# =========================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

RESULTS_DIR = os.path.join(CURRENT_DIR, "evaluation_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

POSTGRES_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123',
    'database': 'rag_system',
    'port': 5432
}

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

TARGET_TABLES = ['users', 'systems', 'roles', 'permissions', 'systems_users', 'systems_users_permissions']


# =========================================================
# FUNCIONES DE UTILIDAD
# =========================================================

def cosine_similarity(emb1: List[float], emb2: List[float]) -> float:
    """Calcula similitud coseno entre dos vectores"""
    vec1 = np.array(emb1)
    vec2 = np.array(emb2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def get_all_chunks():
    """Obtiene todos los chunks de la base de datos"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, text, embedding, chunk_type, source_file, tables, relationship FROM chunks")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"❌ Error obteniendo chunks: {e}")
        return []


# =========================================================
# CLASE DE BÚSQUEDA VECTORIAL
# =========================================================

class VectorSearchPostgreSQL:
    def __init__(self, db_config: Dict, embedding_model: str = EMBEDDING_MODEL):
        self.db_config = db_config
        self.model = SentenceTransformer(embedding_model)
        self.cached_chunks = None
    
    def _get_chunks(self):
        """Obtiene chunks cacheados"""
        if self.cached_chunks is None:
            self.cached_chunks = get_all_chunks()
        return self.cached_chunks
    
    def search(self, query_text: str, k: int = 10) -> List[Tuple[str, str, float, Dict]]:
        """Busca chunks similares usando similitud coseno"""
        try:
            # Generar embedding de la query
            query_embedding = self.model.encode(query_text).tolist()
            
            # Obtener todos los chunks
            chunks = self._get_chunks()
            
            if not chunks:
                print(f"   ⚠️ No hay chunks en la base de datos")
                return []
            
            # Calcular similitudes
            similarities = []
            for row in chunks:
                chunk_id, chunk_text, embedding_jsonb, chunk_type, source_file, tables, relationship = row
                
                # Convertir JSONB a lista
                if isinstance(embedding_jsonb, str):
                    chunk_embedding = json.loads(embedding_jsonb)
                else:
                    chunk_embedding = embedding_jsonb
                
                similarity = cosine_similarity(query_embedding, chunk_embedding)
                
                similarities.append({
                    'id': chunk_id,
                    'text': chunk_text,
                    'similarity': similarity,
                    'chunk_type': chunk_type,
                    'source_file': source_file,
                    'tables': tables,
                    'relationship': relationship
                })
            
            # Ordenar por similitud
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Retornar top k
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
            
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
            import traceback
            traceback.print_exc()
            return []


# =========================================================
# FUNCIÓN DE RELEVANCIA
# =========================================================

def is_relevant_chunk(
    chunk_text: str,
    metadata: Dict,
    required_tables: set
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
        if f'tabla {table}' in text or f'{table}:' in text:
            return True
    
    return False


def get_relevance_vector(
    results: List[Tuple],
    required_tables: set
) -> List[int]:
    """Genera vector de relevancia"""
    relevance = []
    for chunk_id, chunk_text, similarity, metadata in results:
        if is_relevant_chunk(chunk_text, metadata, required_tables):
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
    """Crea queries para evaluar el esquema"""
    queries = []
    
    queries.append({
        "name": "✅ Tabla users",
        "text": "tabla de usuarios con username password email",
        "required_tables": {"users"},
        "expected_min_relevant": 1
    })
    
    queries.append({
        "name": "✅ Tabla systems",
        "text": "tabla de sistemas con nombre descripcion",
        "required_tables": {"systems"},
        "expected_min_relevant": 1
    })
    
    queries.append({
        "name": "✅ Tabla roles",
        "text": "tabla de roles con foreign key a systems",
        "required_tables": {"roles"},
        "expected_min_relevant": 1
    })
    
    queries.append({
        "name": "✅ Tabla permissions",
        "text": "tabla de permisos con foreign key a roles",
        "required_tables": {"permissions"},
        "expected_min_relevant": 1
    })
    
    queries.append({
        "name": "✅ Relación systems_users",
        "text": "tabla intermedia entre usuarios y sistemas",
        "required_tables": {"systems_users"},
        "expected_min_relevant": 1
    })
    
    queries.append({
        "name": "✅ Tabla systems_users_permissions",
        "text": "tabla de permisos especiales por usuario y sistema",
        "required_tables": {"systems_users_permissions"},
        "expected_min_relevant": 1
    })
    
    queries.append({
        "name": "❌ Tabla inexistente",
        "text": "tabla de logs de auditoria",
        "required_tables": {"logs", "audit_logs"},
        "expected_min_relevant": 0
    })
    
    return queries


# =========================================================
# EVALUACIÓN PRINCIPAL
# =========================================================

def evaluate_system(k: int = 10) -> Dict[str, Any]:
    """Evalúa el sistema completo"""
    
    print(f"\n{'='*70}")
    print(f"📊 EVALUANDO SISTEMA RAG CON POSTGRESQL (K={k})")
    print(f"{'='*70}\n")
    
    searcher = VectorSearchPostgreSQL(POSTGRES_CONFIG)
    queries = create_test_queries()
    results = []
    
    for query in queries:
        print(f"📝 {query['name']}")
        print(f"   Query: {query['text']}")
        
        retrieved = searcher.search(query["text"], k)
        
        if not retrieved:
            print(f"   ❌ No se recuperaron chunks")
            results.append({"query_name": query["name"], "error": "No chunks retrieved"})
            continue
        
        print(f"   Recuperados: {len(retrieved)} chunks")
        
        relevance = get_relevance_vector(retrieved, query["required_tables"])
        
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
        
        print(f"   Total relevantes: {total_relevant}, Encontrados: {found_relevant}")
        print(f"   AP: {ap:.3f}, P@{k}: {result['precision_at_k']:.3f}")
        print()
    
    valid = [r for r in results if "error" not in r]
    positive = [r for r in valid if r["expected_min"] > 0]
    negative = [r for r in valid if r["expected_min"] == 0]
    
    global_metrics = {
        "k": k,
        "backend": "PostgreSQL",
        "schema": list(TARGET_TABLES),
        "total_queries": len(results),
        "valid_queries": len(valid),
        "mean_ap": np.mean([r["ap"] for r in valid]) if valid else 0,
        "mean_precision": np.mean([r["precision_at_k"] for r in valid]) if valid else 0,
        "mean_recall": np.mean([r["recall_at_k"] for r in valid]) if valid else 0,
        "mean_ndcg": np.mean([r["ndcg"] for r in valid]) if valid else 0,
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
    print("📈 REPORTE DE RECUPERACIÓN - PostgreSQL")
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
        "backend": "PostgreSQL",
        "schema": TARGET_TABLES,
        "global_metrics": {k: float(v) if isinstance(v, np.float64) else v 
                          for k, v in evaluation["global_metrics"].items()},
        "per_query_results": evaluation["per_query_results"]
    }
    
    filename = f"retrieval_postgres_schema_report_{timestamp}_k{k}.json"
    filepath = os.path.join(RESULTS_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados en: {filepath}")
    return filepath


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🔍 EVALUACIÓN DE RECUPERACIÓN - PostgreSQL")
    print("=" * 70)
    
    try:
        import psycopg2
        print(f"✅ psycopg2 versión: {psycopg2.__version__}")
    except ImportError:
        print("❌ psycopg2 no está instalado")
        exit(1)
    
    # Verificar chunks
    chunks = get_all_chunks()
    print(f"✅ Total de chunks en PostgreSQL: {len(chunks)}")
    
    if len(chunks) == 0:
        print("⚠️ No hay chunks en la base de datos")
        exit(1)
    
    # Mostrar ejemplos de chunks
    print("\n📋 Ejemplos de chunks disponibles:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"   {i+1}. ID: {chunk[0]}")
        print(f"      Tipo: {chunk[3]}")
        print(f"      Tablas: {chunk[5]}")
        print()
    
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