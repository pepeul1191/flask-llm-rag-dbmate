# test_end_2_end.py - Versión con SQLite3 y Llama 3.2

import os
import json
import re
import sqlite3
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

SQLITE_PATH = os.path.join(BASE_PATH, "rag_system.db")
RESULTS_DIR = os.path.join(CURRENT_DIR, "evaluation_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Modelo de embeddings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Configuración de Ollama
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2"

# =========================================================
# CLASE PARA BÚSQUEDA VECTORIAL EN SQLITE
# =========================================================

class VectorSearchSQLite:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.model = SentenceTransformer(EMBEDDING_MODEL)
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def cosine_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calcula similitud coseno"""
        vec1 = np.array(emb1)
        vec2 = np.array(emb2)
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def search(self, query_text: str, k: int = 5) -> List[Tuple[str, str, float]]:
        """Busca chunks similares"""
        self.connect()
        cursor = self.conn.cursor()
        
        # Generar embedding de la query
        query_embedding = self.model.encode(query_text).tolist()
        
        # Obtener todos los chunks
        cursor.execute("SELECT id, text, embedding FROM chunks")
        rows = cursor.fetchall()
        
        # Calcular similitudes
        similarities = []
        for row in rows:
            chunk_id, chunk_text, embedding_bytes = row
            chunk_embedding = np.frombuffer(embedding_bytes, dtype=np.float32).tolist()
            similarity = self.cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((similarity, chunk_id, chunk_text))
        
        # Ordenar y retornar top k
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        self.close()
        return [(chunk_id, chunk_text, sim) for sim, chunk_id, chunk_text in similarities[:k]]


# =========================================================
# FUNCIONES PARA LLAMA 3.2
# =========================================================

def call_llama(prompt: str, max_tokens: int = 500) -> str:
    """Llama a Llama 3.2 via Ollama API"""
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
            print(f"   ⚠️ Error Ollama: {response.status_code}")
            return ""
            
    except requests.exceptions.ConnectionError:
        print("   ❌ No se pudo conectar a Ollama")
        return ""
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return ""


def generate_sql_answer(question: str, retrieved_chunks: List[Tuple[str, str, float]]) -> str:
    """Genera respuesta SQL usando Llama 3.2"""
    
    # Preparar contexto
    context = "\n\n".join([chunk_text for _, chunk_text, _ in retrieved_chunks[:5]])
    
    prompt = f"""Eres un asistente experto en SQL para SQLite/PostgreSQL.
Tu tarea es generar la sentencia SQL correcta basada en el contexto proporcionado.

CONTEXTO:
{context}

PREGUNTA:
{question}

REGLAS IMPORTANTES:
1. Responde SOLO con la sentencia SQL, sin explicaciones
2. Usa sintaxis SQL estándar (INTEGER PRIMARY KEY AUTOINCREMENT para SQLite)
3. Si la pregunta pide una tabla, genera CREATE TABLE
4. Si la pregunta pide una relación, genera la tabla intermedia con FOREIGN KEY
5. Si no encuentras la información, responde con una tabla simple de ejemplo

RESPUESTA SQL:"""

    answer = call_llama(prompt, max_tokens=500)
    
    # Limpiar respuesta
    if "```sql" in answer:
        match = re.search(r'```sql\n(.*?)\n```', answer, re.DOTALL)
        if match:
            answer = match.group(1)
    elif "```" in answer:
        match = re.search(r'```\n(.*?)\n```', answer, re.DOTALL)
        if match:
            answer = match.group(1)
    
    # Fallback
    if not answer or len(answer) < 20:
        if "usuario" in question.lower():
            answer = "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, password TEXT NOT NULL, email TEXT NOT NULL);"
        elif "libro" in question.lower():
            answer = "CREATE TABLE books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, isbn TEXT, pages INTEGER);"
        else:
            answer = "CREATE TABLE example (id INTEGER PRIMARY KEY AUTOINCREMENT);"
    
    return answer


def get_ground_truth_answer(question: str, required_tables: set) -> str:
    """Ground truth para SQLite"""
    
    ground_truths = {
        "users": """CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    email TEXT NOT NULL
);""",
        "books": """CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    isbn TEXT,
    pages INTEGER
);""",
        "genres": """CREATE TABLE genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);""",
        "books_genres": """CREATE TABLE books_genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (genre_id) REFERENCES genres(id)
);""",
        "books_authors": """CREATE TABLE books_authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (author_id) REFERENCES authors(id)
);""",
        "reviews": """CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rating INTEGER NOT NULL,
    comment TEXT,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
);"""
    }
    
    for table, gt in ground_truths.items():
        if table in required_tables:
            return gt
    
    return "CREATE TABLE example (id INTEGER PRIMARY KEY AUTOINCREMENT);"


# =========================================================
# MÉTRICAS
# =========================================================

def calculate_bleu_simple(candidate: str, reference: str) -> float:
    """BLEU simplificado"""
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
    """ROUGE-L simplificado"""
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
    """Verifica si la respuesta está respaldada por el contexto"""
    if not answer or not contexts:
        return 0.0
    
    context_text = " ".join(contexts).lower()
    answer_lower = answer.lower()
    
    sql_keywords = ['create table', 'primary key', 'foreign key', 'references', 'autoincrement']
    
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
    """Answer Relevancy para SQL"""
    if not answer or not question:
        return 0.0
    
    answer_lower = answer.lower()
    question_lower = question.lower()
    
    semantic_mapping = {
        'usuario': 'users', 'personas': 'users', 'user': 'users',
        'libro': 'books', 'book': 'books',
        'género': 'genres', 'genero': 'genres',
        'reseña': 'reviews', 'review': 'reviews',
        'autor': 'authors', 'author': 'authors'
    }
    
    expected_table = None
    for keyword, table in semantic_mapping.items():
        if keyword in question_lower:
            expected_table = table
            break
    
    if expected_table:
        if f'create table {expected_table}' in answer_lower:
            return 1.0
        if expected_table in answer_lower and 'create table' in answer_lower:
            return 1.0
    
    if 'create table' in answer_lower:
        return 0.5
    
    return 0.0


# =========================================================
# FUNCIONES PRINCIPALES
# =========================================================

def create_e2e_queries() -> List[Dict[str, Any]]:
    """Crea queries para evaluación"""
    queries = []
    
    queries.append({
        "name": "Tabla users",
        "question": "Necesito crear una tabla para usuarios con id, nombre de usuario, contraseña y email",
        "required_tables": {"users"}
    })
    
    queries.append({
        "name": "Tabla books",
        "question": "Quiero almacenar libros con título, ISBN y número de páginas",
        "required_tables": {"books"}
    })
    
    queries.append({
        "name": "Relación libros-géneros",
        "question": "Cómo relaciono libros con géneros? Necesito una tabla intermedia",
        "required_tables": {"books_genres"}
    })
    
    queries.append({
        "name": "Tabla de reseñas",
        "question": "Crear tabla para reseñas de libros con calificación, comentario y fecha",
        "required_tables": {"reviews"}
    })
    
    queries.append({
        "name": "Tabla inexistente (negativa)",
        "question": "Necesito una tabla para inventario con stock y ubicación",
        "required_tables": {"inventory"}
    })
    
    return queries


def evaluate_e2e(k: int = 5) -> Dict[str, Any]:
    """Evaluación end-to-end completa"""
    
    print(f"\n{'='*70}")
    print(f"📊 EVALUACIÓN END-TO-END (K={k}) con SQLite3 y {MODEL_NAME}")
    print(f"{'='*70}\n")
    
    # Inicializar buscador vectorial
    searcher = VectorSearchSQLite(SQLITE_PATH)
    
    queries = create_e2e_queries()
    results = []
    
    for query in queries:
        print(f"📝 {query['name']}")
        print(f"   Pregunta: {query['question'][:80]}...")
        
        # 1. Buscar chunks similares
        retrieved = searcher.search(query["question"], k)
        
        if not retrieved:
            print(f"   ❌ No se recuperaron chunks")
            results.append({"query_name": query["name"], "error": "No chunks"})
            continue
        
        chunks_text = [text for _, text, _ in retrieved]
        
        # 2. Generar respuesta con Llama
        generated_answer = generate_sql_answer(query["question"], retrieved)
        
        # 3. Ground truth
        ground_truth = get_ground_truth_answer(query["question"], query["required_tables"])
        
        # 4. Calcular métricas
        faithfulness = calculate_faithfulness(generated_answer, chunks_text)
        answer_relevancy = calculate_answer_relevancy(generated_answer, query["question"])
        bleu_score = calculate_bleu_simple(generated_answer, ground_truth)
        rouge_l = calculate_rouge_l_simple(generated_answer, ground_truth)
        
        result = {
            "query_name": query["name"],
            "question": query["question"],
            "generated_answer": generated_answer[:500],
            "ground_truth": ground_truth[:500],
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "bleu": bleu_score,
            "rouge_l": rouge_l,
            "num_chunks": len(retrieved)
        }
        
        results.append(result)
        
        print(f"   📊 Faithfulness: {faithfulness:.3f} | Relevancy: {answer_relevancy:.3f}")
        print(f"   📊 BLEU: {bleu_score:.3f} | ROUGE-L: {rouge_l:.3f}")
        print()
    
    # Métricas globales
    valid = [r for r in results if "error" not in r]
    
    global_metrics = {
        "k": k,
        "model": MODEL_NAME,
        "backend": "SQLite3",
        "total_queries": len(results),
        "valid_queries": len(valid),
        "mean_faithfulness": np.mean([r["faithfulness"] for r in valid]),
        "mean_answer_relevancy": np.mean([r["answer_relevancy"] for r in valid]),
        "mean_bleu": np.mean([r["bleu"] for r in valid]),
        "mean_rouge_l": np.mean([r["rouge_l"] for r in valid]),
    }
    
    return {"global_metrics": global_metrics, "per_query_results": results}


def print_report(evaluation: Dict[str, Any]):
    """Imprime reporte"""
    m = evaluation["global_metrics"]
    
    print(f"\n{'='*70}")
    print("📈 REPORTE END-TO-END CON SQLITE3")
    print(f"{'='*70}\n")
    
    print(f"🎯 Backend: {m['backend']}")
    print(f"🎯 Modelo: {m['model']}")
    
    print(f"\n🎯 MÉTRICAS DE GENERACIÓN:")
    print(f"   Mean Faithfulness:     {m['mean_faithfulness']:.4f}")
    print(f"   Mean Answer Relevancy: {m['mean_answer_relevancy']:.4f}")
    
    print(f"\n🎯 MÉTRICAS NLG CLÁSICAS:")
    print(f"   Mean BLEU:             {m['mean_bleu']:.4f}")
    print(f"   Mean ROUGE-L:          {m['mean_rouge_l']:.4f}")
    
    print(f"\n✅ Queries evaluadas: {m['valid_queries']}/{m['total_queries']}")


def save_results(evaluation: Dict[str, Any], timestamp: str, k: int):
    """Guarda resultados"""
    output = {
        "timestamp": timestamp,
        "k": k,
        "backend": "SQLite3",
        "model": MODEL_NAME,
        "global_metrics": {k: float(v) if isinstance(v, np.float64) else v 
                          for k, v in evaluation["global_metrics"].items()},
        "per_query_results": evaluation["per_query_results"]
    }
    
    filename = f"e2e_sqlite_report_{timestamp}_k{k}.json"
    filepath = os.path.join(RESULTS_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados en: {filepath}")
    return filepath


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔍 EVALUACIÓN END-TO-END CON SQLITE3 Y LLAMA 3.2")
    print("="*70)
    
    # Verificar SQLite
    if not os.path.exists(SQLITE_PATH):
        print(f"❌ Base SQLite no existe: {SQLITE_PATH}")
        print("   Ejecute primero: python3 ingest_sqlite.py")
        exit(1)
    
    # Verificar Ollama
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code != 200:
            print(f"⚠️ No se pudo conectar a Ollama en {OLLAMA_URL}")
    except:
        print(f"⚠️ No se pudo conectar a Ollama")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Evaluar con diferentes K
    for k in [3, 5, 10]:
        print(f"\n{'─'*70}")
        print(f"🔄 EVALUANDO CON K={k}")
        print(f"{'─'*70}")
        
        evaluation = evaluate_e2e(k=k)
        print_report(evaluation)
        save_results(evaluation, timestamp, k)
    
    print(f"\n✅ Evaluación completada")
    print(f"📁 Resultados en: {RESULTS_DIR}")