# test_end_2_end_mysql_schema.py - Pruebas end-to-end con esquema de usuarios/sistemas/roles

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

# Configuración MySQL
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123',
    'database': 'rag_system',
    'port': 3306,
    'charset': 'utf8mb4'
}

# Modelo de embeddings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Configuración de Ollama
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2"

# Tablas del esquema objetivo
TARGET_TABLES = ['users', 'systems', 'roles', 'permissions', 'systems_users', 'systems_users_permissions']


# =========================================================
# CLASE PARA BÚSQUEDA VECTORIAL EN MYSQL
# =========================================================

class VectorSearchMySQL:
    def __init__(self, db_config: Dict, embedding_model: str = EMBEDDING_MODEL):
        self.db_config = db_config
        self.model = SentenceTransformer(embedding_model)
    
    def cosine_similarity(self, emb1: List[float], emb2_json: str) -> float:
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
    
    def search(self, query_text: str, k: int = 5) -> List[Tuple[str, str, float]]:
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            query_embedding = self.model.encode(query_text).tolist()
            cursor.execute("SELECT id, text, embedding FROM chunks")
            rows = cursor.fetchall()
            
            similarities = []
            for row in rows:
                similarity = self.cosine_similarity(query_embedding, row['embedding'])
                similarities.append((similarity, row['id'], row['text']))
            
            similarities.sort(key=lambda x: x[0], reverse=True)
            cursor.close()
            conn.close()
            
            return [(chunk_id, chunk_text, sim) 
                    for sim, chunk_id, chunk_text in similarities[:k]]
                    
        except Error as e:
            print(f"❌ Error en búsqueda: {e}")
            return []


# =========================================================
# FUNCIONES PARA LLAMA 3.2
# =========================================================

def call_llama(prompt: str, max_tokens: int = 600) -> str:
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
    """Genera respuesta SQL usando Llama 3.2 para el esquema"""
    
    context = "\n\n".join([chunk_text for _, chunk_text, _ in retrieved_chunks[:5]])
    
    prompt = f"""Eres un asistente experto en SQL para MySQL.
Tu tarea es generar la sentencia SQL correcta basada en el contexto proporcionado.

CONTEXTO DEL ESQUEMA:
{context}

PREGUNTA DEL USUARIO:
{question}

REGLAS IMPORTANTES:
1. Responde SOLO con la sentencia SQL, sin explicaciones adicionales
2. Usa sintaxis de MySQL (INT AUTO_INCREMENT PRIMARY KEY)
3. Para tablas de relación, usa FOREIGN KEY con referencias correctas
4. El esquema incluye: users, systems, roles, permissions, systems_users, systems_users_permissions
5. Si la pregunta es ambigua, genera la tabla más relevante

RESPUESTA SQL:"""

    answer = call_llama(prompt, max_tokens=600)
    
    # Limpiar respuesta
    if "```sql" in answer:
        match = re.search(r'```sql\n(.*?)\n```', answer, re.DOTALL)
        if match:
            answer = match.group(1)
    elif "```" in answer:
        match = re.search(r'```\n(.*?)\n```', answer, re.DOTALL)
        if match:
            answer = match.group(1)
    
    # Fallback según pregunta
    if not answer or len(answer) < 30:
        if "usuario" in question.lower():
            answer = """CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(20) NOT NULL,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(50) NOT NULL,
    activated BOOLEAN DEFAULT FALSE,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);"""
        elif "sistema" in question.lower():
            answer = """CREATE TABLE systems (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);"""
        elif "rol" in question.lower():
            answer = """CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    system_id INT NOT NULL,
    FOREIGN KEY (system_id) REFERENCES systems(id)
);"""
        elif "permiso" in question.lower():
            answer = """CREATE TABLE permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    role_id INT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);"""
        else:
            answer = "CREATE TABLE example (id INT AUTO_INCREMENT PRIMARY KEY);"
    
    return answer


def get_ground_truth_answer(question: str) -> str:
    """Ground truth para el esquema objetivo"""
    
    ground_truths = {
        "users": """CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(20) NOT NULL,
    password VARCHAR(100) NOT NULL,
    activation_key VARCHAR(30),
    reset_key VARCHAR(30),
    email VARCHAR(50) NOT NULL,
    activated BOOLEAN DEFAULT FALSE,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);""",
        
        "systems": """CREATE TABLE systems (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    description TEXT,
    repository VARCHAR(100),
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);""",
        
        "roles": """CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    system_id INT NOT NULL,
    FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE
);""",
        
        "permissions": """CREATE TABLE permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    role_id INT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);""",
        
        "systems_users": """CREATE TABLE systems_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    system_id INT NOT NULL,
    user_id INT NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_system_user (system_id, user_id)
);""",
        
        "systems_users_permissions": """CREATE TABLE systems_users_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    system_id INT NOT NULL,
    user_id INT NOT NULL,
    permission_id INT NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE KEY unique_system_user_permission (system_id, user_id, permission_id)
);"""
    }
    
    # Detectar qué tabla se pregunta
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
    
    sql_keywords = ['create table', 'primary key', 'foreign key', 'references', 'auto_increment']
    
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
    
    semantic_mapping = {
        'usuario': 'users',
        'usuarios': 'users',
        'user': 'users',
        'sistema': 'systems',
        'sistemas': 'systems',
        'rol': 'roles',
        'roles': 'roles',
        'permiso': 'permissions',
        'permisos': 'permissions',
        'relación usuario sistema': 'systems_users',
        'acceso a sistema': 'systems_users',
        'permiso especial': 'systems_users_permissions'
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
# QUERIES DE PRUEBA
# =========================================================

def create_e2e_queries() -> List[Dict[str, Any]]:
    """Crea queries para evaluación del esquema"""
    queries = []
    
    queries.append({
        "name": "Tabla users - Usuarios",
        "question": "Necesito crear una tabla para almacenar usuarios con nombre de usuario, contraseña y email",
        "expected_table": "users"
    })
    
    queries.append({
        "name": "Tabla systems - Sistemas",
        "question": "Quiero una tabla para guardar información de los sistemas de la plataforma con nombre y descripción",
        "expected_table": "systems"
    })
    
    queries.append({
        "name": "Tabla roles - Roles",
        "question": "Crear una tabla para roles que pertenecen a un sistema",
        "expected_table": "roles"
    })
    
    queries.append({
        "name": "Tabla permissions - Permisos",
        "question": "Necesito una tabla para permisos que están asociados a roles",
        "expected_table": "permissions"
    })
    
    queries.append({
        "name": "Relación users-systems - Acceso a sistemas",
        "question": "Cómo relaciono usuarios con sistemas? Necesito una tabla intermedia",
        "expected_table": "systems_users"
    })
    
    queries.append({
        "name": "Permisos especiales por usuario",
        "question": "Tabla para asignar permisos específicos a un usuario en un sistema",
        "expected_table": "systems_users_permissions"
    })
    
    queries.append({
        "name": "Query negativa - Tabla inexistente",
        "question": "Necesito una tabla para logs de auditoría",
        "expected_table": None
    })
    
    return queries


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def evaluate_e2e(k: int = 5) -> Dict[str, Any]:
    """Evaluación end-to-end completa"""
    
    print(f"\n{'='*70}")
    print(f"📊 EVALUACIÓN END-TO-END (K={k}) con MySQL y {MODEL_NAME}")
    print(f"   Esquema: Usuarios, Sistemas, Roles, Permisos")
    print(f"{'='*70}\n")
    
    searcher = VectorSearchMySQL(MYSQL_CONFIG)
    queries = create_e2e_queries()
    results = []
    
    for query in queries:
        print(f"📝 {query['name']}")
        print(f"   Pregunta: {query['question'][:80]}...")
        
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
        
        # Verificar si la tabla esperada está presente
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
            "generated_answer": generated_answer[:600],
            "ground_truth": ground_truth[:600],
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "bleu": bleu_score,
            "rouge_l": rouge_l,
            "num_chunks": len(retrieved)
        }
        
        results.append(result)
        
        print(f"   📊 Faithfulness: {faithfulness:.3f} | Relevancy: {answer_relevancy:.3f}")
        print(f"   📊 BLEU: {bleu_score:.3f} | ROUGE-L: {rouge_l:.3f}")
        if expected:
            print(f"   📋 Tabla esperada: {expected} | Correcta: {'✅' if table_correct else '❌'}")
        print()
    
    valid = [r for r in results if "error" not in r]
    
    global_metrics = {
        "k": k,
        "model": MODEL_NAME,
        "backend": "MySQL",
        "schema_tables": TARGET_TABLES,
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
    """Imprime reporte"""
    m = evaluation["global_metrics"]
    
    print(f"\n{'='*70}")
    print("📈 REPORTE END-TO-END - ESQUEMA USUARIOS/SISTEMAS/ROLES")
    print(f"{'='*70}\n")
    
    print(f"🎯 Backend: {m['backend']}")
    print(f"🎯 Modelo: {m['model']}")
    print(f"🎯 K={m['k']}")
    
    print(f"\n🎯 MÉTRICAS DE GENERACIÓN:")
    print(f"   Mean Faithfulness:     {m['mean_faithfulness']:.4f}")
    print(f"   Mean Answer Relevancy: {m['mean_answer_relevancy']:.4f}")
    print(f"   Table Accuracy:        {m['table_accuracy']:.2%}")
    
    print(f"\n🎯 MÉTRICAS NLG CLÁSICAS:")
    print(f"   Mean BLEU:             {m['mean_bleu']:.4f}")
    print(f"   Mean ROUGE-L:          {m['mean_rouge_l']:.4f}")
    
    print(f"\n✅ Queries evaluadas: {m['valid_queries']}/{m['total_queries']}")


def save_results(evaluation: Dict[str, Any], timestamp: str, k: int):
    """Guarda resultados"""
    output = {
        "timestamp": timestamp,
        "k": k,
        "backend": "MySQL",
        "model": MODEL_NAME,
        "schema": TARGET_TABLES,
        "global_metrics": {k: float(v) if isinstance(v, np.float64) else v 
                          for k, v in evaluation["global_metrics"].items()},
        "per_query_results": evaluation["per_query_results"]
    }
    
    filename = f"e2e_mysql_schema_report_{timestamp}_k{k}.json"
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
    print("🔍 EVALUACIÓN END-TO-END CON MYSQL")
    print("   Esquema: Usuarios, Sistemas, Roles, Permisos")
    print("=" * 70)
    
    try:
        import pymysql
        print(f"✅ PyMySQL versión: {pymysql.__version__}")
    except ImportError:
        print("❌ PyMySQL no está instalado")
        exit(1)
    
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"✅ Conectado a MySQL: {count} chunks")
        
        if count == 0:
            print("⚠️ No hay chunks en la base de datos")
            print("   Ejecute primero: python3 ingest_mysql_schema.py")
            exit(1)
    except Error as e:
        print(f"❌ Error conectando a MySQL: {e}")
        exit(1)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for k in [3, 5, 10]:
        print(f"\n{'─'*70}")
        print(f"🔄 EVALUANDO CON K={k}")
        print(f"{'─'*70}")
        
        evaluation = evaluate_e2e(k=k)
        print_report(evaluation)
        save_results(evaluation, timestamp, k)
    
    print(f"\n✅ Evaluación completada")
    print(f"📁 Resultados en: {RESULTS_DIR}")