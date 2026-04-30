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
collection = client.get_collection("migrations")


# =========================================================
# 3. CARGAR Y PARSEAR PUML
# =========================================================

def load_puml() -> str:
    """Carga el archivo PlantUML"""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return f.read()


def parse_puml(puml: str) -> Tuple[set, set]:
    """Extrae tablas y relaciones del PlantUML"""
    tables = set()
    relationships = set()

    for line in puml.splitlines():
        line = line.strip()

        # Detectar entidades/tablas
        if line.startswith("entity"):
            parts = line.split()
            if len(parts) >= 2:
                table_name = parts[1].lower()
                # Limpiar posibles caracteres especiales
                table_name = re.sub(r'[^a-z0-9_]', '', table_name)
                if table_name:
                    tables.add(table_name)

        # Detectar relaciones (ej: users -- orders)
        if "--" in line and ":" not in line:
            try:
                parts = line.split("--")
                if len(parts) >= 2:
                    left = re.sub(r'[^a-z0-9_]', '', parts[0].strip().lower())
                    right = re.sub(r'[^a-z0-9_]', '', parts[1].strip().lower())
                    if left and right:
                        relationships.add((left, right))
            except:
                pass

    return tables, relationships


# =========================================================
# 4. FUNCIÓN DE RELEVANCIA MEJORADA PARA TU ESQUEMA
# =========================================================

def is_relevant_chunk(
    chunk: str, 
    required_tables: set, 
    required_relationships: set
) -> bool:
    """
    Determina si un chunk es relevante para generar el esquema requerido.
    Adaptado a tu esquema real (books, genres, authors, users, etc.)
    """
    text = chunk.lower()
    
    # Tablas puente que podrían no estar en el PUML pero son necesarias
    bridge_tables = ['books_authors', 'books_genres']
    
    # ===== CASO 1: Creación exacta de tabla requerida =====
    for table in required_tables:
        # Busca CREATE TABLE nombre_tabla exacto
        pattern = rf'create\s+table\s+{re.escape(table)}\b'
        if re.search(pattern, text):
            # Verifica que tenga definición completa de columnas
            has_columns = any(keyword in text for keyword in [
                'varchar', 'int', 'bigint', 'boolean', 'timestamp', 
                'date', 'text', 'primary key', 'not null', 'auto_increment'
            ])
            if has_columns:
                return True
        
        # Para tablas puente (incluso si no están en required_tables original)
        if table in bridge_tables:
            if re.search(rf'create\s+table\s+{re.escape(table)}', text):
                return True
    
    # ===== CASO 2: Foreign keys reales =====
    for a, b in required_relationships:
        # Busca FOREIGN KEY explícita que referencie la tabla correcta
        fk_pattern = rf'foreign\s+key\s*\([^)]+\)\s+references\s+{re.escape(a)}\b'
        if re.search(fk_pattern, text):
            if b in text or a in text:
                return True
        
        # Busca CONSTRAINT con FOREIGN KEY
        constraint_pattern = rf'constraint\s+\w+\s+foreign\s+key\s*\([^)]+\)\s+references\s+{re.escape(b)}\b'
        if re.search(constraint_pattern, text):
            if a in text or b in text:
                return True
        
        # Caso especial: tabla books_genres (tiene dos FKs)
        if 'books_genres' in text and a in text and b in text:
            if 'foreign key' in text:
                return True
    
    # ===== CASO 3: Columnas importantes en tablas requeridas =====
    important_columns = ['id', 'created_at', 'updated_at']
    for col in important_columns:
        if re.search(rf'\b{col}\b', text):
            for table in required_tables:
                if re.search(rf'create\s+table\s+{re.escape(table)}', text):
                    return True
    
    # ===== CASO 4: Búsqueda semántica para autenticación =====
    if 'autenticación' in text or 'authentication' in text or 'login' in text:
        if 'users' in required_tables and 'create table users' in text:
            if any(field in text for field in ['email', 'password', 'auth']):
                return True
    
    return False


def get_all_relevant_chunks(
    chunks: List[str],
    required_tables: set,
    required_relationships: set
) -> List[int]:
    """Genera vector de relevancia para todos los chunks"""
    return [
        1 if is_relevant_chunk(chunk, required_tables, required_relationships) 
        else 0 
        for chunk in chunks
    ]


# =========================================================
# 5. MÉTRICAS DE EVALUACIÓN
# =========================================================

def precision_at_k(relevance: List[int], k: int) -> float:
    """Precision@K: proporción de relevantes entre los primeros K"""
    if k <= 0 or not relevance:
        return 0.0
    return sum(relevance[:k]) / k


def recall_at_k(relevance: List[int], total_relevant: int, k: int) -> float:
    """Recall@K: proporción de relevantes recuperados"""
    if total_relevant <= 0:
        return 0.0
    return sum(relevance[:k]) / total_relevant


def top1_accuracy(relevance: List[int]) -> float:
    """Top-1 Accuracy: el primer resultado es relevante"""
    return 1.0 if relevance and relevance[0] == 1 else 0.0


def mean_reciprocal_rank(relevance: List[int]) -> float:
    """MRR: inverso de la posición del primer relevante"""
    for i, rel in enumerate(relevance):
        if rel == 1:
            return 1.0 / (i + 1)
    return 0.0


def average_precision(relevance: List[int]) -> float:
    """Average Precision para una query"""
    hits = 0
    sum_precisions = 0.0
    
    for i, rel in enumerate(relevance):
        if rel == 1:
            hits += 1
            sum_precisions += hits / (i + 1)
    
    return sum_precisions / hits if hits > 0 else 0.0


def map_score(relevance_scores: List[List[int]]) -> float:
    """Mean Average Precision para múltiples queries"""
    if not relevance_scores:
        return 0.0
    
    aps = [average_precision(rel) for rel in relevance_scores]
    return np.mean(aps)


def ndcg_at_k(relevance: List[int], k: int) -> float:
    """NDCG@K: Normalized Discounted Cumulative Gain"""
    if k <= 0 or not relevance:
        return 0.0
    
    # DCG
    dcg = 0.0
    for i in range(min(k, len(relevance))):
        gain = relevance[i]
        if gain > 0:
            dcg += gain / np.log2(i + 2)
    
    # IDCG
    ideal = sorted(relevance, reverse=True)
    idcg = 0.0
    for i in range(min(k, len(ideal))):
        gain = ideal[i]
        if gain > 0:
            idcg += gain / np.log2(i + 2)
    
    return dcg / idcg if idcg > 0 else 0.0


def average_rank(relevance: List[int]) -> float:
    """Posición promedio del primer resultado relevante"""
    for i, rel in enumerate(relevance):
        if rel == 1:
            return float(i + 1)
    return float('inf')


def hit_rate(relevance_list: List[List[int]], k: int = 1) -> float:
    """Hit Rate@K: al menos un relevante en top K"""
    hits = 0
    for relevance in relevance_list:
        if sum(relevance[:k]) > 0:
            hits += 1
    return hits / len(relevance_list) if relevance_list else 0.0


def f_beta_score(precision: float, recall: float, beta: float = 1.0) -> float:
    """F-beta score: beta>1 da más peso a recall"""
    if precision + recall == 0:
        return 0.0
    return (1 + beta**2) * (precision * recall) / ((beta**2 * precision) + recall)


# =========================================================
# 6. QUERIES DE PRUEBA - ADAPTADAS A TU ESQUEMA REAL
# =========================================================

def create_test_queries() -> List[Dict[str, Any]]:
    """
    Crea queries basadas en las tablas REALES de tu esquema:
    books, publishers, books_genres, authors, books_authors, 
    devices, countries, reviews, users, genres
    """
    queries = []
    
    # ===== QUERIES POSITIVAS (DEBEN ENCONTRAR RESULTADOS) =====
    
    # 1. Tabla users (existe en tu esquema)
    queries.append({
        "name": "✅ Tabla users",
        "text": "generar la tabla users con columnas id, email, password, created_at",
        "required_tables": {"users"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "easy"
    })
    
    # 2. Tabla books (existe)
    queries.append({
        "name": "✅ Tabla books",
        "text": "necesito la tabla para almacenar libros con título, ISBN y páginas",
        "required_tables": {"books"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "easy"
    })
    
    # 3. Tabla genres (existe)
    queries.append({
        "name": "✅ Tabla genres",
        "text": "crear tabla de géneros literarios con id y nombre",
        "required_tables": {"genres"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "easy"
    })
    
    # 4. Relación books - genres (existe books_genres)
    queries.append({
        "name": "✅ Relación books-genres",
        "text": "crear relación muchos a muchos entre libros y géneros",
        "required_tables": {"books", "genres", "books_genres"},
        "required_relationships": {("books", "genres")},
        "expected_min_relevant": 1,
        "difficulty": "medium"
    })
    
    # 5. Tabla intermedia books_authors (existe)
    queries.append({
        "name": "✅ Tabla books_authors",
        "text": "tabla para relacionar libros con autores",
        "required_tables": {"books_authors"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "medium"
    })
    
    # 6. Múltiples tablas relacionadas
    queries.append({
        "name": "✅ Múltiples tablas",
        "text": "quiero las tablas para libros, autores y la relación entre ambos",
        "required_tables": {"books", "authors", "books_authors"},
        "required_relationships": {("books", "authors")},
        "expected_min_relevant": 2,
        "difficulty": "hard"
    })
    
    # 7. Query semántica (autenticación -> users)
    queries.append({
        "name": "✅ Query semántica: autenticación",
        "text": "migración para manejar autenticación de usuarios en el sistema",
        "required_tables": {"users"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "medium"
    })
    
    # 8. Reviews (existe)
    queries.append({
        "name": "✅ Tabla reviews",
        "text": "tabla para almacenar reseñas de libros con puntuación y comentario",
        "required_tables": {"reviews"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "easy"
    })
    
    # ===== QUERIES NEGATIVAS (NO DEBEN ENCONTRAR RESULTADOS) =====
    
    # 9. Tabla que NO existe
    queries.append({
        "name": "❌ Tabla inexistente",
        "text": "generar la tabla inventory con stock y ubicación",
        "required_tables": {"inventory"},
        "required_relationships": set(),
        "expected_min_relevant": 0,
        "difficulty": "negative"
    })
    
    # 10. Relación que NO existe
    queries.append({
        "name": "❌ Relación inexistente",
        "text": "crear foreign key entre users y devices",
        "required_tables": set(),
        "required_relationships": {("users", "devices")},
        "expected_min_relevant": 0,
        "difficulty": "negative"
    })
    
    # 11. Tabla que NO existe en el esquema
    queries.append({
        "name": "❌ Tabla shopping_cart",
        "text": "necesito tabla para carrito de compras",
        "required_tables": {"shopping_cart"},
        "required_relationships": set(),
        "expected_min_relevant": 0,
        "difficulty": "negative"
    })
    
    # 12. Query ambigua pero con tabla existente
    queries.append({
        "name": "⚠️ Query ambigua",
        "text": "tabla para guardar información de personas que usan el sistema",
        "required_tables": {"users"},
        "required_relationships": set(),
        "expected_min_relevant": 1,
        "difficulty": "hard"
    })
    
    return queries


# =========================================================
# 7. EVALUACIÓN PRINCIPAL
# =========================================================

def retrieve_chunks(query_text: str, k: int = 10) -> List[str]:
    """Recupera chunks desde ChromaDB"""
    results = collection.query(
        query_texts=[query_text],
        n_results=k
    )
    return results["documents"][0] if results["documents"] else []


def evaluate_single_query(
    query: Dict[str, Any],
    k: int = 10
) -> Dict[str, Any]:
    """
    Evalúa una única query
    """
    # Recuperar chunks
    chunks = retrieve_chunks(query["text"], k)
    
    if not chunks:
        return {
            "query_name": query["name"],
            "query_text": query["text"],
            "difficulty": query.get("difficulty", "unknown"),
            "precision@k": 0.0,
            "recall@k": 0.0,
            "top1_accuracy": 0.0,
            "mrr": 0.0,
            "ap": 0.0,
            "ndcg@k": 0.0,
            "average_rank": float('inf'),
            "f2_score": 0.0,
            "total_relevant": 0,
            "found_relevant": 0,
            "expected_min": query.get("expected_min_relevant", 0),
            "error": "No chunks retrieved"
        }
    
    # Calcular relevancia
    relevance = get_all_relevant_chunks(
        chunks,
        query["required_tables"],
        query["required_relationships"]
    )
    
    total_relevant = sum(relevance)
    found_relevant = sum(relevance[:k])
    
    precision = precision_at_k(relevance, k)
    recall = recall_at_k(relevance, total_relevant, k)
    
    # Calcular métricas
    return {
        "query_name": query["name"],
        "query_text": query["text"],
        "difficulty": query.get("difficulty", "unknown"),
        "precision@k": precision,
        "recall@k": recall,
        "top1_accuracy": top1_accuracy(relevance),
        "mrr": mean_reciprocal_rank(relevance),
        "ap": average_precision(relevance),
        "ndcg@k": ndcg_at_k(relevance, k),
        "average_rank": average_rank(relevance),
        "f2_score": f_beta_score(precision, recall, beta=2.0),
        "total_relevant": total_relevant,
        "found_relevant": found_relevant,
        "expected_min": query.get("expected_min_relevant", 0),
        "meets_expectation": found_relevant >= query.get("expected_min_relevant", 0),
        "relevance_vector": relevance[:k],
        "chunks": chunks[:3]
    }


def evaluate_system(k: int = 10) -> Dict[str, Any]:
    """
    Evalúa el sistema completo con múltiples queries
    """
    test_queries = create_test_queries()
    results = []
    
    print(f"\n{'='*70}")
    print(f"📊 EVALUANDO SISTEMA RAG (K={k})")
    print(f"{'='*70}\n")
    
    for query in test_queries:
        print(f"📝 {query['name']} [{query.get('difficulty', 'unknown').upper()}]")
        print(f"   Query: {query['text'][:80]}...")
        
        result = evaluate_single_query(query, k)
        results.append(result)
        
        # Mostrar resultado con color simbólico
        if result.get("error"):
            print(f"   ❌ ERROR: {result['error']}")
        elif result["meets_expectation"]:
            print(f"   ✅ OK: Precision@{k}={result['precision@k']:.3f}, Recall@{k}={result['recall@k']:.3f}, AP={result['ap']:.3f}")
        else:
            print(f"   ⚠️ WARNING: Esperaba ≥{result['expected_min']} relevantes, obtuvo {result['found_relevant']}")
            print(f"      Precision@{k}={result['precision@k']:.3f}, AP={result['ap']:.3f}")
        print()
    
    # Separar resultados por tipo
    positive_results = [r for r in results if r["expected_min"] > 0 and not r.get("error")]
    negative_results = [r for r in results if r["expected_min"] == 0 and not r.get("error")]
    
    # Calcular métricas globales
    all_relevance_vectors = [r["relevance_vector"] for r in results if "relevance_vector" in r and not r.get("error")]
    
    global_metrics = {
        "total_queries": len(results),
        "queries_with_results": sum(1 for r in results if not r.get("error")),
        
        # Métricas generales
        "mean_ap": np.mean([r["ap"] for r in results if not r.get("error") and r["ap"] > 0]) if positive_results else 0,
        "mean_precision": np.mean([r["precision@k"] for r in results if not r.get("error")]),
        "mean_recall": np.mean([r["recall@k"] for r in results if not r.get("error")]),
        "mean_ndcg": np.mean([r["ndcg@k"] for r in results if not r.get("error")]),
        "mean_f2": np.mean([r["f2_score"] for r in results if not r.get("error")]),
        "mrr": np.mean([r["mrr"] for r in results if not r.get("error")]),
        
        # Métricas solo queries positivas
        "positive_queries_count": len(positive_results),
        "positive_mean_ap": np.mean([r["ap"] for r in positive_results]) if positive_results else 0,
        "positive_mean_precision": np.mean([r["precision@k"] for r in positive_results]) if positive_results else 0,
        "positive_mean_recall": np.mean([r["recall@k"] for r in positive_results]) if positive_results else 0,
        
        # Métricas queries negativas (deben tener 0 relevantes)
        "negative_queries_count": len(negative_results),
        "negative_false_positives": sum(1 for r in negative_results if r["found_relevant"] > 0),
        "negative_specificity": 1.0 - (sum(1 for r in negative_results if r["found_relevant"] > 0) / len(negative_results)) if negative_results else 1.0,
        
        # Hit rates
        "hit_rate_1": hit_rate(all_relevance_vectors, 1),
        "hit_rate_3": hit_rate(all_relevance_vectors, 3),
        "hit_rate_5": hit_rate(all_relevance_vectors, 5),
        
        # Expectativas
        "expectations_met": sum(1 for r in results if r.get("meets_expectation", False) and not r.get("error")),
        "expectation_rate": sum(1 for r in results if r.get("meets_expectation", False) and not r.get("error")) / len([r for r in results if not r.get("error")]) if results else 0,
    }
    
    # Métricas por dificultad
    difficulties = {}
    for r in results:
        if not r.get("error"):
            diff = r.get("difficulty", "unknown")
            if diff not in difficulties:
                difficulties[diff] = {"aps": [], "precisions": [], "recalls": [], "count": 0}
            difficulties[diff]["aps"].append(r["ap"])
            difficulties[diff]["precisions"].append(r["precision@k"])
            difficulties[diff]["recalls"].append(r["recall@k"])
            difficulties[diff]["count"] += 1
    
    for diff, metrics in difficulties.items():
        if metrics["count"] > 0:
            difficulties[diff]["mean_ap"] = np.mean(metrics["aps"])
            difficulties[diff]["mean_precision"] = np.mean(metrics["precisions"])
            difficulties[diff]["mean_recall"] = np.mean(metrics["recalls"])
    
    global_metrics["by_difficulty"] = difficulties
    
    return {
        "global_metrics": global_metrics,
        "per_query_results": results
    }


# =========================================================
# 8. FUNCIÓN DE DIAGNÓSTICO
# =========================================================

def diagnose_system():
    """Diagnostica el estado actual del sistema"""
    print("\n" + "="*70)
    print("🔍 DIAGNÓSTICO DEL SISTEMA RAG")
    print("="*70 + "\n")
    
    # Cargar y parsear PUML
    puml = load_puml()
    tables, relationships = parse_puml(puml)
    
    print(f"📊 Tablas encontradas en PUML: {len(tables)}")
    print(f"   {sorted(list(tables))[:15]}...")
    print(f"\n🔗 Relaciones encontradas: {len(relationships)}")
    print(f"   {list(relationships)[:10]}...")
    
    # Verificar chunks en ChromaDB
    all_docs = collection.get()
    total_chunks = len(all_docs['documents']) if all_docs and all_docs['documents'] else 0
    print(f"\n💾 Total de chunks en ChromaDB: {total_chunks}")
    
    if total_chunks > 0:
        print(f"\n📄 Ejemplo de chunks almacenados:")
        for i, doc in enumerate(all_docs['documents'][:3]):
            print(f"\n--- Chunk {i+1} (primeros 200 chars) ---")
            print(doc[:200] + "...")
            
            # Verificar qué tablas contiene
            doc_lower = doc.lower()
            mentioned_tables = [t for t in tables if t in doc_lower]
            if mentioned_tables:
                print(f"   → Contiene tablas: {mentioned_tables[:5]}")
    
    print("\n" + "="*70)


# =========================================================
# 9. FUNCIÓN PARA REPORTE DETALLADO
# =========================================================

def print_detailed_report(evaluation: Dict[str, Any], k: int):
    """Imprime un reporte detallado de la evaluación"""
    
    metrics = evaluation["global_metrics"]
    
    print(f"\n{'='*70}")
    print(f"📈 REPORTE DETALLADO (K={k})")
    print(f"{'='*70}\n")
    
    print("🎯 MÉTRICAS GLOBALES:")
    print(f"   Mean Average Precision (MAP): {metrics['mean_ap']:.4f}")
    print(f"   Mean Precision@{k}: {metrics['mean_precision']:.4f}")
    print(f"   Mean Recall@{k}: {metrics['mean_recall']:.4f}")
    print(f"   Mean NDCG@{k}: {metrics['mean_ndcg']:.4f}")
    print(f"   Mean F2-Score: {metrics['mean_f2']:.4f}")
    print(f"   MRR: {metrics['mrr']:.4f}")
    print(f"   Expectation Rate: {metrics['expectation_rate']:.2%}")
    
    print(f"\n📊 POR TIPO DE QUERY:")
    print(f"   Positivas ({metrics['positive_queries_count']}):")
    print(f"     - MAP: {metrics['positive_mean_ap']:.4f}")
    print(f"     - Precision@{k}: {metrics['positive_mean_precision']:.4f}")
    print(f"     - Recall@{k}: {metrics['positive_mean_recall']:.4f}")
    
    print(f"\n   Negativas ({metrics['negative_queries_count']}):")
    print(f"     - False Positives: {metrics['negative_false_positives']}")
    print(f"     - Specificity: {metrics['negative_specificity']:.2%}")
    
    print(f"\n🎯 HIT RATES:")
    print(f"   Hit Rate@1: {metrics['hit_rate_1']:.2%}")
    print(f"   Hit Rate@3: {metrics['hit_rate_3']:.2%}")
    print(f"   Hit Rate@5: {metrics['hit_rate_5']:.2%}")
    
    print(f"\n📈 POR DIFICULTAD:")
    for difficulty, diff_metrics in metrics.get("by_difficulty", {}).items():
        if diff_metrics["count"] > 0:
            print(f"   {difficulty.upper()} ({diff_metrics['count']} queries):")
            print(f"     - MAP: {diff_metrics['mean_ap']:.4f}")
            print(f"     - Precision@{k}: {diff_metrics['mean_precision']:.4f}")
            print(f"     - Recall@{k}: {diff_metrics['mean_recall']:.4f}")
    
    print(f"\n⚠️ QUERIES PROBLEMÁTICAS:")
    for res in evaluation["per_query_results"]:
        if not res.get("meets_expectation", True) and not res.get("error"):
            print(f"   - {res['query_name']}: Esperaba ≥{res['expected_min']}, obtuvo {res['found_relevant']} (AP={res['ap']:.3f})")
    
    print(f"\n✅ EVALUACIÓN COMPLETADA")


# =========================================================
# 10. MAIN
# =========================================================

if __name__ == "__main__":
    
    # Diagnóstico inicial
    diagnose_system()
    
    # Evaluar con diferentes valores de K
    k_values = [5, 10, 20]
    all_evaluations = {}
    
    for k in k_values:
        print(f"\n{'─'*70}")
        print(f"🔄 EVALUANDO CON K={k}")
        print(f"{'─'*70}")
        
        evaluation = evaluate_system(k=k)
        all_evaluations[k] = evaluation
        
        # Reporte detallado
        print_detailed_report(evaluation, k)
    
    # Resumen comparativo
    print(f"\n{'='*70}")
    print("📊 RESUMEN COMPARATIVO")
    print(f"{'='*70}\n")
    
    print("K\tMAP\t\tP@{K}\t\tR@{K}\t\tHIT@1")
    print("-" * 65)
    for k in k_values:
        metrics = all_evaluations[k]["global_metrics"]
        print(f"{k}\t{metrics['mean_ap']:.4f}\t\t{metrics['mean_precision']:.4f}\t\t{metrics['mean_recall']:.4f}\t\t{metrics['hit_rate_1']:.2%}")
    
    print("\n✅ Diagnóstico y evaluación completados\n")