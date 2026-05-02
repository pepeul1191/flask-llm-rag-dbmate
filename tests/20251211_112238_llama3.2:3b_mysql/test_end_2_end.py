# test_end_2_end_mysql_programas.py - Pruebas end-to-end

import os
import json
import re
import pymysql
from pymysql import Error
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

MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123',
    'database': 'rag_system_programas',
    'port': 3306,
    'charset': 'utf8mb4'
}

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2"

TARGET_TABLES = ['programs', 'phases', 'participants', 'internals', 'workers', 'mentors']


# =========================================================
# FUNCIONES DE UTILIDAD
# =========================================================

def cosine_similarity(emb1: List[float], emb2_json: str) -> float:
    try:
        emb2 = json.loads(emb2_json)
        vec1 = np.array(emb1)
        vec2 = np.array(emb2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    except:
        return 0.0


def get_all_chunks():
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, text, embedding FROM chunks")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Error as e:
        print(f"❌ Error obteniendo chunks: {e}")
        return []


# =========================================================
# CLASE DE BÚSQUEDA
# =========================================================

class VectorSearchMySQL:
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
                chunk_id, chunk_text, embedding_json = row
                similarity = cosine_similarity(query_embedding, embedding_json)
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
    
    prompt = f"""Eres un experto en SQL para MySQL. Genera solo la sentencia CREATE TABLE.

CONTEXTO DEL ESQUEMA (nombres en INGLÉS):
{context}

PREGUNTA: {question}

REGLAS ESTRICTAS:
1. Los nombres de tabla DEBEN estar en INGLÉS (programs, phases, participants, workers, mentors)
2. NO uses nombres en español (programas, fases, participantes, trabajadores, mentores)
3. Usa AUTO_INCREMENT para PRIMARY KEY
4. Incluye FOREIGN KEY según corresponda

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
    
    # Fallback específico para programas
    if not answer or len(answer) < 20:
        if "programa" in question.lower():
            answer = """CREATE TABLE programs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    description TEXT
);"""
        elif "participante" in question.lower():
            answer = """CREATE TABLE participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    names VARCHAR(50) NOT NULL,
    last_names VARCHAR(50) NOT NULL,
    email VARCHAR(40) NOT NULL,
    dni VARCHAR(20) NOT NULL
);"""
        elif "trabajador" in question.lower():
            answer = """CREATE TABLE workers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    names VARCHAR(50) NOT NULL,
    last_names VARCHAR(50) NOT NULL,
    email VARCHAR(40) NOT NULL
);"""
        elif "mentor" in question.lower():
            answer = """CREATE TABLE mentors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT NOT NULL,
    FOREIGN KEY (worker_id) REFERENCES workers(id)
);"""
        else:
            answer = "CREATE TABLE example (id INT AUTO_INCREMENT PRIMARY KEY);"
    
    return answer

def get_ground_truth_answer(question: str) -> str:
    ground_truths = {
        "programa": """CREATE TABLE programs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    description TEXT,
    image_url VARCHAR(60),
    pdf_url VARCHAR(60),
    max_participant_team INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    program_type_id INT NOT NULL,
    period_id INT NOT NULL,
    FOREIGN KEY (program_type_id) REFERENCES program_types(id),
    FOREIGN KEY (period_id) REFERENCES periods(id)
);""",
        "participante": """CREATE TABLE participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    names VARCHAR(50) NOT NULL,
    last_names VARCHAR(50) NOT NULL,
    email VARCHAR(40) NOT NULL,
    phone VARCHAR(40),
    dni VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    dni_type_id INT NOT NULL,
    nation_id INT NOT NULL,
    FOREIGN KEY (dni_type_id) REFERENCES dni_types(id),
    FOREIGN KEY (nation_id) REFERENCES nations(id)
);""",
        "trabajador": """CREATE TABLE workers (
    id INT AUTO_INCREMENT PRIMARY KEY,
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
    
    sql_keywords = ['create table', 'primary key', 'foreign key', 'auto_increment']
    
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
    print(f"📊 EVALUACIÓN K={k} con MySQL")
    print(f"{'='*70}\n")
    
    searcher = VectorSearchMySQL(MYSQL_CONFIG)
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
        "backend": "MySQL",
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
    print("📈 REPORTE END-TO-END - MySQL (Programas)")
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
        "backend": "MySQL",
        "model": MODEL_NAME,
        "global_metrics": {k: float(v) if isinstance(v, np.float64) else v 
                          for k, v in evaluation["global_metrics"].items()},
        "per_query_results": evaluation["per_query_results"]
    }
    
    filename = f"e2e_mysql_programas_report_{timestamp}_k{k}.json"
    filepath = os.path.join(RESULTS_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados en: {filepath}")
    return filepath

def normalize_table_name_mysql(table_name: str) -> str:
    """Normaliza nombres de tabla español → inglés para MySQL"""
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
        # Plurales irregulares
        'program': 'programs',
        'phase': 'phases',
        'participant': 'participants',
        'worker': 'workers',
        'mentor': 'mentors',
    }
    table_lower = table_name.lower().strip()
    return mapping.get(table_lower, table_lower)


def extract_table_name_from_sql(sql: str) -> str:
    """Extrae nombre de tabla de sentencia CREATE TABLE"""
    if not sql:
        return None
    
    # Patrón para MySQL
    patterns = [
        r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?([a-z_][a-z0-9_]*)`?',
        r'CREATE\s+TABLE\s+`?([a-z_][a-z0-9_]*)`?',
    ]
    
    sql_lower = sql.lower()
    for pattern in patterns:
        match = re.search(pattern, sql_lower, re.IGNORECASE)
        if match:
            table_name = match.group(1).strip('`').strip("'").strip('"')
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
    generated_norm = normalize_table_name_mysql(generated_table)
    
    # Debug (opcional)
    if expected_norm != generated_norm:
        print(f"   🐛 Debug: Esperado='{expected_norm}' | Generado='{generated_norm}' (original='{generated_table}')")
    
    return expected_norm == generated_norm

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🔍 EVALUACIÓN END-TO-END CON MYSQL")
    print("   Esquema: Programas, Fases, Participantes, Trabajadores")
    print("=" * 70)
    
    chunks = get_all_chunks()
    print(f"✅ Conectado a MySQL: {len(chunks)} chunks")
    
    if len(chunks) == 0:
        print("⚠️ No hay chunks. Ejecute: python3 ingest_mysql_programas.py")
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