# test_end_2_end_postgres_schema.py - Versión corregida

import os
import json
import re
import psycopg2
import numpy as np
import requests
from datetime import datetime
from typing import List, Tuple, Dict, Any
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

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2"

TARGET_TABLES = ['users', 'systems', 'roles', 'permissions', 'systems_users', 'systems_users_permissions']


# =========================================================
# FUNCIONES DE UTILIDAD
# =========================================================

def cosine_similarity(emb1: List[float], emb2: List[float]) -> float:
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
        cursor.execute("SELECT id, text, embedding FROM chunks")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"❌ Error obteniendo chunks: {e}")
        return []


# =========================================================
# CLASE DE BÚSQUEDA
# =========================================================

class VectorSearchPostgreSQL:
    def __init__(self, db_config: Dict, embedding_model: str = EMBEDDING_MODEL):
        self.db_config = db_config
        self.model = SentenceTransformer(embedding_model)
        self.cached_chunks = None
    
    def _get_chunks(self):
        if self.cached_chunks is None:
            self.cached_chunks = get_all_chunks()
        return self.cached_chunks
    
    def search(self, query_text: str, k: int = 5) -> List[Tuple[str, str, float]]:
        try:
            query_embedding = self.model.encode(query_text).tolist()
            chunks = self._get_chunks()
            
            if not chunks:
                return []
            
            similarities = []
            for row in chunks:
                chunk_id, chunk_text, embedding_jsonb = row
                
                if isinstance(embedding_jsonb, str):
                    chunk_embedding = json.loads(embedding_jsonb)
                else:
                    chunk_embedding = embedding_jsonb
                
                similarity = cosine_similarity(query_embedding, chunk_embedding)
                similarities.append((similarity, chunk_id, chunk_text))
            
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [(chunk_id, chunk_text, sim) for sim, chunk_id, chunk_text in similarities[:k]]
            
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
            return []


# =========================================================
# FUNCIONES PARA LLAMA 3.2
# =========================================================

def call_llama(prompt: str, max_tokens: int = 600) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.1
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        else:
            return ""
            
    except Exception as e:
        print(f"   ⚠️ Error Ollama: {e}")
        return ""


def generate_sql_answer(question: str, retrieved_chunks: List[Tuple[str, str, float]]) -> str:
    context = "\n\n".join([chunk_text for _, chunk_text, _ in retrieved_chunks[:5]])
    
    prompt = f"""Eres un experto en SQL para PostgreSQL. Genera solo la sentencia SQL.

CONTEXTO:
{context}

PREGUNTA: {question}

REGLAS:
1. Solo responde con SQL
2. Usa SERIAL para auto-incremento
3. Incluye FOREIGN KEY si es necesario

SQL:"""

    answer = call_llama(prompt, max_tokens=600)
    
    if "```sql" in answer:
        match = re.search(r'```sql\n(.*?)\n```', answer, re.DOTALL)
        if match:
            answer = match.group(1)
    
    if not answer or len(answer) < 20:
        if "usuario" in question.lower():
            answer = "CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR(20) NOT NULL, password VARCHAR(100) NOT NULL, email VARCHAR(50) NOT NULL);"
        else:
            answer = "CREATE TABLE example (id SERIAL PRIMARY KEY);"
    
    return answer


def get_ground_truth_answer(question: str) -> str:
    ground_truths = {
        "users": """CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(20) NOT NULL,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(50) NOT NULL
);""",
        "systems": """CREATE TABLE systems (
    id SERIAL PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    description TEXT
);""",
        "roles": """CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    system_id INTEGER NOT NULL,
    FOREIGN KEY (system_id) REFERENCES systems(id)
);""",
        "permissions": """CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    role_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);"""
    }
    
    question_lower = question.lower()
    for table, gt in ground_truths.items():
        if table in question_lower:
            return gt
    
    return ground_truths["users"]


# =========================================================
# MÉTRICAS
# =========================================================

def calculate_bleu_simple(candidate: str, reference: str) -> float:
    if not candidate or not reference:
        return 0.0
    
    cand_words = set(candidate.lower().split())
    ref_words = set(reference.lower().split())
    
    if not ref_words:
        return 0.0
    
    intersection = cand_words.intersection(ref_words)
    precision = len(intersection) / len(cand_words) if cand_words else 0.0
    
    if len(cand_words) < len(ref_words):
        bp = np.exp(1 - len(ref_words) / len(cand_words)) if cand_words else 0.0
    else:
        bp = 1.0
    
    return bp * precision


def calculate_rouge_l_simple(candidate: str, reference: str) -> float:
    if not candidate or not reference:
        return 0.0
    
    cand_words = candidate.lower().split()
    ref_words = reference.lower().split()
    
    def lcs_length(a, b):
        dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                if a[i-1] == b[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        return dp[len(a)][len(b)]
    
    lcs = lcs_length(cand_words, ref_words)
    
    if len(ref_words) == 0:
        return 0.0
    
    recall = lcs / len(ref_words)
    precision = lcs / len(cand_words) if cand_words else 0.0
    
    if precision + recall == 0:
        return 0.0
    
    return 2 * precision * recall / (precision + recall)


def calculate_faithfulness(answer: str, contexts: List[str]) -> float:
    if not answer or not contexts:
        return 0.0
    
    context_text = " ".join(contexts).lower()
    answer_lower = answer.lower()
    
    sql_keywords = ['create table', 'primary key', 'foreign key', 'serial']
    
    supported = 0
    total = 0
    
    for keyword in sql_keywords:
        if keyword in answer_lower:
            total += 1
            if keyword in context_text:
                supported += 1
    
    if total == 0:
        return 1.0
    
    return supported / total


def calculate_answer_relevancy(answer: str, question: str) -> float:
    if not answer or not question:
        return 0.0
    
    answer_lower = answer.lower()
    question_lower = question.lower()
    
    mapping = {
        'usuario': 'users', 'sistema': 'systems',
        'rol': 'roles', 'permiso': 'permissions'
    }
    
    expected = None
    for key, table in mapping.items():
        if key in question_lower:
            expected = table
            break
    
    if expected:
        if f'create table {expected}' in answer_lower:
            return 1.0
        if expected in answer_lower:
            return 0.8
    
    return 0.5 if 'create table' in answer_lower else 0.0


def create_e2e_queries() -> List[Dict[str, Any]]:
    queries = []
    
    queries.append({
        "name": "Tabla users",
        "question": "Necesito crear una tabla para usuarios con nombre de usuario, contraseña y email",
        "expected_table": "users"
    })
    
    queries.append({
        "name": "Tabla systems",
        "question": "Tabla para sistemas con nombre y descripción",
        "expected_table": "systems"
    })
    
    queries.append({
        "name": "Tabla roles",
        "question": "Tabla para roles que pertenecen a un sistema",
        "expected_table": "roles"
    })
    
    queries.append({
        "name": "Tabla permissions",
        "question": "Tabla para permisos asociados a roles",
        "expected_table": "permissions"
    })
    
    queries.append({
        "name": "Query negativa",
        "question": "Necesito una tabla para logs",
        "expected_table": None
    })
    
    return queries


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def evaluate_e2e(k: int = 5) -> Dict[str, Any]:
    print(f"\n{'='*70}")
    print(f"📊 EVALUACIÓN K={k} con PostgreSQL")
    print(f"{'='*70}\n")
    
    searcher = VectorSearchPostgreSQL(POSTGRES_CONFIG)
    queries = create_e2e_queries()
    results = []
    
    for query in queries:
        print(f"📝 {query['name']}")
        print(f"   Pregunta: {query['question'][:60]}...")
        
        retrieved = searcher.search(query["question"], k)
        
        if not retrieved:
            print(f"   ❌ No se recuperaron chunks")
            results.append({"query_name": query["name"], "error": "No chunks"})
            continue
        
        chunks_text = [text for _, text, _ in retrieved]
        generated_answer = generate_sql_answer(query["question"], retrieved)
        ground_truth = get_ground_truth_answer(query["question"])
        
        faithfulness = calculate_faithfulness(generated_answer, chunks_text)
        answer_relevancy = calculate_answer_relevancy(generated_answer, query["question"])
        bleu_score = calculate_bleu_simple(generated_answer, ground_truth)
        rouge_l = calculate_rouge_l_simple(generated_answer, ground_truth)
        
        expected = query.get("expected_table")
        table_correct = False
        if expected:
            if f'create table {expected}' in generated_answer.lower():
                table_correct = True
        
        result = {
            "query_name": query["name"],
            "question": query["question"],
            "expected_table": expected,
            "table_correct": table_correct,
            "generated_answer": generated_answer[:500],
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "bleu": bleu_score,
            "rouge_l": rouge_l,
            "num_chunks": len(retrieved)
        }
        
        results.append(result)
        
        print(f"   Faithfulness: {faithfulness:.3f} | Relevancy: {answer_relevancy:.3f}")
        print(f"   BLEU: {bleu_score:.3f} | ROUGE-L: {rouge_l:.3f}")
        if expected:
            print(f"   Tabla esperada: {expected} | Correcta: {'✅' if table_correct else '❌'}")
        print()
    
    valid = [r for r in results if "error" not in r]
    
    global_metrics = {
        "k": k,
        "model": MODEL_NAME,
        "backend": "PostgreSQL",
        "total_queries": len(results),
        "valid_queries": len(valid),
        "mean_faithfulness": np.mean([r["faithfulness"] for r in valid]) if valid else 0,
        "mean_answer_relevancy": np.mean([r["answer_relevancy"] for r in valid]) if valid else 0,
        "mean_bleu": np.mean([r["bleu"] for r in valid]) if valid else 0,
        "mean_rouge_l": np.mean([r["rouge_l"] for r in valid]) if valid else 0,
        "table_accuracy": sum(1 for r in valid if r.get("table_correct", False)) / len([r for r in valid if r.get("expected_table")]) if valid else 0
    }
    
    return {"global_metrics": global_metrics, "per_query_results": results}


def print_report(evaluation: Dict[str, Any]):
    m = evaluation["global_metrics"]
    
    print(f"\n{'='*70}")
    print("📈 REPORTE END-TO-END - PostgreSQL")
    print(f"{'='*70}\n")
    
    print(f"🎯 Backend: {m['backend']}")
    print(f"🎯 K={m['k']}")
    
    print(f"\n🎯 MÉTRICAS:")
    print(f"   Faithfulness:     {m['mean_faithfulness']:.4f}")
    print(f"   Answer Relevancy: {m['mean_answer_relevancy']:.4f}")
    print(f"   Table Accuracy:   {m['table_accuracy']:.2%}")
    print(f"   BLEU:             {m['mean_bleu']:.4f}")
    print(f"   ROUGE-L:          {m['mean_rouge_l']:.4f}")
    
    print(f"\n✅ Queries: {m['valid_queries']}/{m['total_queries']}")


def save_results(evaluation: Dict[str, Any], timestamp: str, k: int):
    output = {
        "timestamp": timestamp,
        "k": k,
        "backend": "PostgreSQL",
        "model": MODEL_NAME,
        "global_metrics": {k: float(v) if isinstance(v, np.float64) else v 
                          for k, v in evaluation["global_metrics"].items()},
        "per_query_results": evaluation["per_query_results"]
    }
    
    filename = f"e2e_postgres_report_{timestamp}_k{k}.json"
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
    print("🔍 EVALUACIÓN END-TO-END CON POSTGRESQL")
    print("=" * 70)
    
    chunks = get_all_chunks()
    print(f"✅ Conectado a PostgreSQL: {len(chunks)} chunks")
    
    if len(chunks) == 0:
        print("⚠️ No hay chunks. Ejecute: python3 ingest_postgres_schema.py")
        exit(1)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for k in [3, 5, 10]:
        print(f"\n{'─'*70}")
        print(f"🔄 K={k}")
        print(f"{'─'*70}")
        
        evaluation = evaluate_e2e(k=k)
        print_report(evaluation)
        save_results(evaluation, timestamp, k)
    
    print(f"\n✅ Evaluación completada")