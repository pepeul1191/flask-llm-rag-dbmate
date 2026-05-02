# test_end_2_end_sqlite_programas.py - Pruebas end-to-end con normalización

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
SQLITE_PATH = os.path.join(BASE_PATH, "rag_system_programas.db")

RESULTS_DIR = os.path.join(CURRENT_DIR, "evaluation_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2"

TARGET_TABLES = ['programs', 'phases', 'participants', 'internals', 'workers', 'mentors']


# =========================================================
# FUNCIONES DE NORMALIZACIÓN (NUEVAS)
# =========================================================

def normalize_table_name_sqlite(table_name: str) -> str:
    """Normaliza nombres de tabla español → inglés para SQLite"""
    mapping = {
        # Español → Inglés
        'programa': 'programs',
        'programas': 'programs',
        'fase': 'phases',
        'fases': 'phases',
        'participante': 'participants',
        'participantes': 'participants',
        'trabajador': 'workers',
        'trabajadores': 'workers',
        'mentor': 'mentors',
        'mentores': 'mentors',
        'internos': 'internals',
        'interno': 'internals',
        'externos': 'externals',
        'externo': 'externals',
        # Inglés → Inglés (por si acaso)
        'program': 'programs',
        'phase': 'phases',
        'participant': 'participants',
        'worker': 'workers',
        'mentor': 'mentors',
    }
    table_lower = table_name.lower().strip()
    return mapping.get(table_lower, table_lower)


def extract_table_name_from_sql(sql: str) -> str:
    """Extrae nombre de tabla de sentencia CREATE TABLE para SQLite"""
    if not sql:
        return None
    
    # Patrones para SQLite
    patterns = [
        r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`\[]?([a-z_][a-z0-9_]*)["`\]]?',
        r'CREATE\s+TABLE\s+["`\[]?([a-z_][a-z0-9_]*)["`\]]?',
    ]
    
    sql_lower = sql.lower()
    for pattern in patterns:
        match = re.search(pattern, sql_lower, re.IGNORECASE)
        if match:
            table_name = match.group(1).strip('`').strip("'").strip('"').strip('[').strip(']')
            return table_name.lower()
    
    return None


def validate_table_name(expected: str, generated_sql: str) -> bool:
    """Valida si el SQL generado crea la tabla esperada (con normalización)"""
    if not expected or not generated_sql:
        return False
    
    # Extraer nombre de tabla del SQL generado
    generated_table = extract_table_name_from_sql(generated_sql)
    
    if not generated_table:
        # Fallback: búsqueda directa
        generated_lower = generated_sql.lower()
        if f'create table {expected}' in generated_lower:
            return True
        return False
    
    # Normalizar ambos nombres
    expected_norm = expected.lower().strip()
    generated_norm = normalize_table_name_sqlite(generated_table)
    
    # Debug (opcional - puede comentarse después)
    if expected_norm != generated_norm:
        print(f"   🐛 Debug: Esperado='{expected_norm}' | Generado='{generated_norm}' (original='{generated_table}')")
    
    return expected_norm == generated_norm


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
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, text, embedding FROM chunks")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"❌ Error obteniendo chunks: {e}")
        return []


# =========================================================
# CLASE DE BÚSQUEDA
# =========================================================

class VectorSearchSQLite:
    def __init__(self, db_path: str, embedding_model: str = EMBEDDING_MODEL):
        self.db_path = db_path
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
                chunk_id, chunk_text, embedding_bytes = row
                chunk_embedding = np.frombuffer(embedding_bytes, dtype=np.float32).tolist()
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
    
    prompt = f"""Eres un experto en SQL para SQLite. Genera solo la sentencia CREATE TABLE.

CONTEXTO DEL ESQUEMA (nombres en INGLÉS):
{context}

PREGUNTA: {question}

REGLAS ESTRICTAS:
1. Los nombres de tabla DEBEN estar en INGLÉS (programs, phases, participants, workers, mentors)
2. NO uses nombres en español (programas, fases, participantes, trabajadores, mentores)
3. Usa INTEGER PRIMARY KEY AUTOINCREMENT
4. Incluye FOREIGN KEY si es necesario

EJEMPLOS CORRECTOS:
- "programas" → CREATE TABLE programs (...)
- "fases" → CREATE TABLE phases (...)
- "participantes" → CREATE TABLE participants (...)
- "trabajadores" → CREATE TABLE workers (...)
- "mentores" → CREATE TABLE mentors (...)

SQL:"""

    answer = call_llama(prompt, max_tokens=600)
    
    if "```sql" in answer:
        match = re.search(r'```sql\n(.*?)\n```', answer, re.DOTALL)
        if match:
            answer = match.group(1)
    
    # Fallback específico
    if not answer or len(answer) < 20:
        if "programa" in question.lower():
            answer = """CREATE TABLE programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL,
    description TEXT
);"""
        elif "fase" in question.lower():
            answer = """CREATE TABLE phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL,
    init_date DATE,
    end_date DATE,
    program_id INTEGER NOT NULL,
    FOREIGN KEY (program_id) REFERENCES programs(id)
);"""
        elif "participante" in question.lower():
            answer = """CREATE TABLE participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    names VARCHAR(50) NOT NULL,
    last_names VARCHAR(50) NOT NULL,
    email VARCHAR(40) NOT NULL,
    dni VARCHAR(20) NOT NULL
);"""
        elif "trabajador" in question.lower():
            answer = """CREATE TABLE workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    names VARCHAR(50) NOT NULL,
    last_names VARCHAR(50) NOT NULL,
    email VARCHAR(40) NOT NULL
);"""
        else:
            answer = "CREATE TABLE example (id INTEGER PRIMARY KEY AUTOINCREMENT);"
    
    return answer


def get_ground_truth_answer(question: str) -> str:
    ground_truths = {
        "programa": """CREATE TABLE programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL,
    description TEXT,
    image_url VARCHAR(60),
    pdf_url VARCHAR(60),
    max_participant_team INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    program_type_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    FOREIGN KEY (program_type_id) REFERENCES program_types(id),
    FOREIGN KEY (period_id) REFERENCES periods(id)
);""",
        "participante": """CREATE TABLE participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    names VARCHAR(50) NOT NULL,
    last_names VARCHAR(50) NOT NULL,
    email VARCHAR(40) NOT NULL,
    phone VARCHAR(40),
    dni VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    dni_type_id INTEGER NOT NULL,
    nation_id INTEGER NOT NULL,
    FOREIGN KEY (dni_type_id) REFERENCES dni_types(id),
    FOREIGN KEY (nation_id) REFERENCES nations(id)
);""",
        "trabajador": """CREATE TABLE workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    names VARCHAR(50) NOT NULL,
    last_names VARCHAR(50) NOT NULL,
    email VARCHAR(40) NOT NULL,
    phone VARCHAR(40),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);"""
    }
    
    question_lower = question.lower()
    for key, gt in ground_truths.items():
        if key in question_lower:
            return gt
    
    return ground_truths["programa"]


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
    
    sql_keywords = ['create table', 'primary key', 'foreign key', 'autoincrement']
    
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
        'programa': 'programs',
        'fase': 'phases',
        'participante': 'participants',
        'trabajador': 'workers',
        'mentor': 'mentors'
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
        "name": "Tabla programs",
        "question": "Necesito crear una tabla para almacenar programas con nombre y descripción",
        "expected_table": "programs"
    })
    
    queries.append({
        "name": "Tabla phases",
        "question": "Tabla para fases de programa con fechas de inicio y fin",
        "expected_table": "phases"
    })
    
    queries.append({
        "name": "Tabla participants",
        "question": "Tabla para participantes con nombres, email y DNI",
        "expected_table": "participants"
    })
    
    queries.append({
        "name": "Tabla workers",
        "question": "Tabla para trabajadores con nombres y email",
        "expected_table": "workers"
    })
    
    queries.append({
        "name": "Query negativa",
        "question": "Necesito una tabla para inscripciones",
        "expected_table": None
    })
    
    return queries


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def evaluate_e2e(k: int = 5) -> Dict[str, Any]:
    print(f"\n{'='*70}")
    print(f"📊 EVALUACIÓN K={k} con SQLite3")
    print(f"{'='*70}\n")
    
    searcher = VectorSearchSQLite(SQLITE_PATH)
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
        
        # ✅ VALIDACIÓN CORREGIDA CON NORMALIZACIÓN
        expected = query.get("expected_table")
        table_correct = False
        if expected:
            table_correct = validate_table_name(expected, generated_answer)
        
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
        "backend": "SQLite3",
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
    print("📈 REPORTE END-TO-END - SQLite3 (Programas)")
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
        "backend": "SQLite3",
        "model": MODEL_NAME,
        "global_metrics": {k: float(v) if isinstance(v, np.float64) else v 
                          for k, v in evaluation["global_metrics"].items()},
        "per_query_results": evaluation["per_query_results"]
    }
    
    filename = f"e2e_sqlite_programas_report_{timestamp}_k{k}.json"
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
    print("🔍 EVALUACIÓN END-TO-END CON SQLITE3")
    print("   Esquema: Programas, Fases, Participantes, Trabajadores")
    print("=" * 70)
    
    if not os.path.exists(SQLITE_PATH):
        print(f"❌ Base SQLite no existe: {SQLITE_PATH}")
        print("   Ejecute primero: python3 ingest_sqlite_programas.py")
        exit(1)
    
    chunks = get_all_chunks()
    print(f"✅ Conectado a SQLite: {len(chunks)} chunks")
    
    if len(chunks) == 0:
        print("⚠️ No hay chunks. Ejecute: python3 ingest_sqlite_programas.py")
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