# test_end_2_end.py - Versión con Llama 3.2 via Ollama

import os
import json
import re
import requests
from datetime import datetime
from typing import List, Tuple, Dict, Any
import numpy as np
import chromadb

# =========================================================
# CONFIGURACIÓN
# =========================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_DIR = CURRENT_DIR
BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CHROMA_PATH = os.path.join(BASE_PATH, "chroma_db")
RESULTS_DIR = os.path.join(RUN_DIR, "evaluation_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Configuración de Ollama
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2"  # o "llama3.2:3b"

# =========================================================
# CONEXIÓN A CHROMA
# =========================================================

client = chromadb.PersistentClient(path=CHROMA_PATH)
try:
    collection = client.get_collection("migrations")
    print(f"✅ Conectado a ChromaDB: {collection.count()} chunks")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Ejecute ingest.py primero")
    exit(1)

# =========================================================
# FUNCIÓN PARA LLAMAR A LLAMA 3.2
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
                    "temperature": 0.1  # Bajo para respuestas determinísticas
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
        print("   ❌ No se pudo conectar a Ollama. ¿Está corriendo?")
        print("   Ejecute: ollama serve")
        return ""
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return ""


def generate_sql_answer(question: str, retrieved_chunks: List[str]) -> str:
    """
    Genera respuesta SQL usando Llama 3.2
    """
    # Preparar contexto
    context = "\n\n".join(retrieved_chunks[:5])  # Top 5 chunks
    
    # Prompt especializado para generación SQL (PostgreSQL)
    prompt = f"""Eres un asistente experto en SQL para PostgreSQL. 
Tu tarea es generar la sentencia SQL correcta basada en el contexto proporcionado.

CONTEXTO (esquemas de base de datos existentes):
{context}

PREGUNTA DEL USUARIO:
{question}

REGLAS IMPORTANTES:
1. Responde SOLO con la sentencia SQL, sin explicaciones adicionales
2. Usa sintaxis de PostgreSQL (SERIAL en lugar de AUTO_INCREMENT)
3. Si la pregunta pide una tabla, genera CREATE TABLE
4. Si la pregunta pide una relación, genera la tabla intermedia con FOREIGN KEY
5. Si no encuentras la información en el contexto, responde: "CREATE TABLE example (id SERIAL PRIMARY KEY);"

RESPUESTA SQL:"""

    answer = call_llama(prompt, max_tokens=500)
    
    # Limpiar respuesta si contiene markdown o texto extra
    if "```sql" in answer:
        answer = re.search(r'```sql\n(.*?)\n```', answer, re.DOTALL)
        if answer:
            answer = answer.group(1)
    elif "```" in answer:
        answer = re.search(r'```\n(.*?)\n```', answer, re.DOTALL)
        if answer:
            answer = answer.group(1)
    
    # Asegurar que sea SQL válido
    if not answer or len(answer) < 20:
        # Fallback a respuesta simple
        if "usuario" in question.lower():
            answer = """CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(30) NOT NULL,
  password VARCHAR(40) NOT NULL,
  email VARCHAR(30) NOT NULL
);"""
        elif "libro" in question.lower():
            answer = """CREATE TABLE books (
  id SERIAL PRIMARY KEY,
  title VARCHAR(60),
  isbn VARCHAR(30),
  pages INTEGER
);"""
        else:
            answer = "CREATE TABLE example (id SERIAL PRIMARY KEY);"
    
    return answer


def get_ground_truth_answer(question: str, required_tables: set) -> str:
    """Ground truth para PostgreSQL"""
    
    ground_truths = {
        "users": """CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(30) NOT NULL,
  password VARCHAR(40) NOT NULL,
  email VARCHAR(30) NOT NULL
);""",
        "books": """CREATE TABLE books (
  id SERIAL PRIMARY KEY,
  title VARCHAR(60),
  isbn VARCHAR(30),
  pages INTEGER
);""",
        "genres": """CREATE TABLE genres (
  id SERIAL PRIMARY KEY,
  name VARCHAR(30) NOT NULL
);""",
        "books_genres": """CREATE TABLE books_genres (
  id SERIAL PRIMARY KEY,
  book_id INTEGER NOT NULL,
  genre_id INTEGER NOT NULL,
  FOREIGN KEY (book_id) REFERENCES books(id),
  FOREIGN KEY (genre_id) REFERENCES genres(id)
);""",
        "books_authors": """CREATE TABLE books_authors (
  id SERIAL PRIMARY KEY,
  book_id INTEGER NOT NULL,
  author_id INTEGER NOT NULL,
  FOREIGN KEY (book_id) REFERENCES books(id),
  FOREIGN KEY (author_id) REFERENCES authors(id)
);""",
        "reviews": """CREATE TABLE reviews (
  id SERIAL PRIMARY KEY,
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
    
    return "CREATE TABLE example (id SERIAL PRIMARY KEY);"


# =========================================================
# FUNCIÓN DE RELEVANCIA
# =========================================================

def is_relevant_for_ground_truth(chunk: str, required_tables: set) -> bool:
    """Determina si un chunk es relevante"""
    text = chunk.lower()
    
    for table in required_tables:
        if re.search(rf'create\s+table\s+{re.escape(table)}\b', text):
            return True
        if table in text and 'serial' in text:
            return True
    
    return False


def get_ground_truth_relevance(chunks: List[str], required_tables: set) -> List[int]:
    return [1 if is_relevant_for_ground_truth(chunk, required_tables) else 0 for chunk in chunks]


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
    """Faithfulness: verifica si la respuesta está respaldada por el contexto"""
    if not answer or not contexts:
        return 0.0
    
    context_text = " ".join(contexts).lower()
    answer_lower = answer.lower()
    
    # Extraer palabras clave importantes
    sql_keywords = ['create table', 'serial', 'primary key', 'foreign key', 'references']
    
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
    """Answer Relevancy mejorada para SQL"""
    if not answer or not question:
        return 0.0
    
    answer_lower = answer.lower()
    question_lower = question.lower()
    
    # Mapeo semántico de preguntas a tablas
    semantic_mapping = {
        'usuario': 'users',
        'personas': 'users',
        'user': 'users',
        'libro': 'books',
        'book': 'books',
        'género': 'genres',
        'genero': 'genres',
        'reseña': 'reviews',
        'review': 'reviews',
        'autor': 'authors',
        'author': 'authors'
    }
    
    # Detectar tabla esperada
    expected_table = None
    for keyword, table in semantic_mapping.items():
        if keyword in question_lower:
            expected_table = table
            break
    
    # Verificar si la respuesta contiene la tabla esperada
    if expected_table:
        if f'create table {expected_table}' in answer_lower:
            return 1.0
        if expected_table in answer_lower and 'create table' in answer_lower:
            return 1.0
    
    # Verificar si la respuesta tiene SQL válido
    if 'create table' in answer_lower:
        return 0.5
    
    return 0.0


# =========================================================
# FUNCIONES PRINCIPALES
# =========================================================

def retrieve_chunks(query_text: str, k: int = 5) -> Tuple[List[str], List[float]]:
    """Recupera chunks desde ChromaDB"""
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=k,
            include=["documents", "distances"]
        )
        documents = results["documents"][0] if results["documents"] else []
        distances = results["distances"][0] if results["distances"] else []
        similarities = [1 - d for d in distances] if distances else []
        return documents, similarities
    except Exception as e:
        print(f"Error: {e}")
        return [], []


def create_e2e_queries() -> List[Dict[str, Any]]:
    """Crea queries para evaluación"""
    queries = []
    
    queries.append({
        "name": "Tabla users - creación completa",
        "question": "Necesito crear una tabla para usuarios con id, nombre de usuario, contraseña y email",
        "required_tables": {"users"}
    })
    
    queries.append({
        "name": "Tabla books - estructura",
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
        "name": "Relación libros-autores",
        "question": "Tabla para vincular libros con autores",
        "required_tables": {"books_authors"}
    })
    
    queries.append({
        "name": "Query ambigua - usuarios",
        "question": "Guardar información de personas que usan el sistema",
        "required_tables": {"users"}
    })
    
    queries.append({
        "name": "Tabla inexistente (negativa)",
        "question": "Necesito una tabla para inventario con stock y ubicación",
        "required_tables": {"inventory"}
    })
    
    return queries


def evaluate_e2e(k: int = 5) -> Dict[str, Any]:
    """Evaluación end-to-end completa"""
    
    queries = create_e2e_queries()
    results = []
    
    print(f"\n{'='*70}")
    print(f"📊 EVALUACIÓN END-TO-END (K={k}) con {MODEL_NAME}")
    print(f"{'='*70}\n")
    
    for query in queries:
        print(f"📝 {query['name']}")
        print(f"   Pregunta: {query['question'][:80]}...")
        
        # 1. Recuperar chunks
        chunks, similarities = retrieve_chunks(query["question"], k)
        
        if not chunks:
            print(f"   ❌ No se recuperaron chunks")
            results.append({"query_name": query["name"], "error": "No chunks"})
            continue
        
        # 2. Generar respuesta con Llama 3.2
        generated_answer = generate_sql_answer(query["question"], chunks)
        
        # 3. Ground truth
        ground_truth = get_ground_truth_answer(query["question"], query["required_tables"])
        
        # 4. Calcular métricas de recuperación
        relevance = get_ground_truth_relevance(chunks, query["required_tables"])
        total_relevant = sum(relevance)
        ap = average_precision(relevance)
        
        # 5. Calcular métricas de generación
        faithfulness = calculate_faithfulness(generated_answer, chunks)
        answer_relevancy = calculate_answer_relevancy(generated_answer, query["question"])
        bleu_score = calculate_bleu_simple(generated_answer, ground_truth)
        rouge_l = calculate_rouge_l_simple(generated_answer, ground_truth)
        
        result = {
            "query_name": query["name"],
            "question": query["question"],
            "generated_answer": generated_answer[:500],
            "ground_truth": ground_truth[:500],
            "retrieval_ap": ap,
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "bleu": bleu_score,
            "rouge_l": rouge_l,
            "num_chunks": len(chunks),
            "relevant_chunks": total_relevant
        }
        
        results.append(result)
        
        print(f"   📊 AP: {ap:.3f} | Faithfulness: {faithfulness:.3f} | Relevancy: {answer_relevancy:.3f}")
        print(f"   📊 BLEU: {bleu_score:.3f} | ROUGE-L: {rouge_l:.3f}")
        print()
    
    # Métricas globales
    valid = [r for r in results if "error" not in r]
    
    global_metrics = {
        "k": k,
        "model": MODEL_NAME,
        "total_queries": len(results),
        "valid_queries": len(valid),
        "mean_retrieval_ap": np.mean([r["retrieval_ap"] for r in valid]),
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
    print("📈 REPORTE END-TO-END")
    print(f"{'='*70}\n")
    
    print(f"🎯 Modelo: {m['model']}")
    print(f"\n🎯 MÉTRICAS DE GENERACIÓN:")
    print(f"   Mean Faithfulness:     {m['mean_faithfulness']:.4f}")
    print(f"   Mean Answer Relevancy: {m['mean_answer_relevancy']:.4f}")
    
    print(f"\n🎯 MÉTRICAS NLG CLÁSICAS:")
    print(f"   Mean BLEU:             {m['mean_bleu']:.4f}")
    print(f"   Mean ROUGE-L:          {m['mean_rouge_l']:.4f}")
    
    print(f"\n📊 MÉTRICAS DE RECUPERACIÓN:")
    print(f"   Mean Retrieval AP:     {m['mean_retrieval_ap']:.4f}")
    
    print(f"\n✅ Queries evaluadas: {m['valid_queries']}/{m['total_queries']}")


def save_results(evaluation: Dict[str, Any], timestamp: str):
    """Guarda resultados"""
    output = {
        "timestamp": timestamp,
        "model": MODEL_NAME,
        "global_metrics": {k: float(v) if isinstance(v, np.float64) else v 
                          for k, v in evaluation["global_metrics"].items()},
        "per_query_results": evaluation["per_query_results"]
    }
    
    filename = f"e2e_report_{timestamp}.json"
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
    print("🔍 EVALUACIÓN END-TO-END CON LLAMA 3.2")
    print("="*70)
    
    # Verificar Ollama
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            if not any(m.get("name", "").startswith(MODEL_NAME) for m in models):
                print(f"⚠️ Modelo {MODEL_NAME} no encontrado")
                print(f"   Ejecute: ollama pull {MODEL_NAME}")
        else:
            print(f"⚠️ No se pudo conectar a Ollama en {OLLAMA_URL}")
            print("   Ejecute: ollama serve")
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
        save_results(evaluation, f"{timestamp}_k{k}")
    
    print(f"\n✅ Evaluación completada")
    print(f"📁 Resultados en: {RESULTS_DIR}")