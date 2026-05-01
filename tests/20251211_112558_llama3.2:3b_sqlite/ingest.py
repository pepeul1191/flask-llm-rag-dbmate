# ingest_sqlite_programas.py - Versión para SQLite3 con esquema de programas

import os
import re
import glob
import json
import sqlite3
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

# =========================================================
# CONFIGURACIÓN
# =========================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATIONS_PATH = os.path.join(CURRENT_DIR, "migrations")
BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
SQLITE_PATH = os.path.join(BASE_PATH, "rag_system_programas.db")

# Modelo de embeddings
MODEL_NAME = "all-MiniLM-L6-v2"

# Tablas del esquema objetivo
TARGET_TABLES = [
    'document_types', 'industries', 'specialisms', 'carrere_grades', 'carreres',
    'program_types', 'dni_types', 'nations', 'periods', 'programs', 'phases',
    'participants', 'internals', 'externals', 'workers', 'internal_workers',
    'external_workers', 'mentors', 'mentors_specialisms'
]

# Sentencias SQL del esquema para SQLite3
SCHEMA_SQL = {
    "document_types": """CREATE TABLE IF NOT EXISTS document_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(22) NOT NULL
);""",
    
    "industries": """CREATE TABLE IF NOT EXISTS industries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL
);""",
    
    "specialisms": """CREATE TABLE IF NOT EXISTS specialisms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(70) NOT NULL
);""",
    
    "carrere_grades": """CREATE TABLE IF NOT EXISTS carrere_grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(40) NOT NULL
);""",
    
    "carreres": """CREATE TABLE IF NOT EXISTS carreres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(40) NOT NULL,
    carrere_grade_id INTEGER NOT NULL,
    FOREIGN KEY (carrere_grade_id) REFERENCES carrere_grades(id)
);""",
    
    "program_types": """CREATE TABLE IF NOT EXISTS program_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL
);""",
    
    "dni_types": """CREATE TABLE IF NOT EXISTS dni_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL
);""",
    
    "nations": """CREATE TABLE IF NOT EXISTS nations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL
);""",
    
    "periods": """CREATE TABLE IF NOT EXISTS periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(10) NOT NULL,
    init_date DATE,
    end_date DATE
);""",
    
    "programs": """CREATE TABLE IF NOT EXISTS programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL,
    description TEXT,
    image_url VARCHAR(60),
    pdf_url VARCHAR(60),
    max_participant_team INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    program_type_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    FOREIGN KEY (program_type_id) REFERENCES program_types(id),
    FOREIGN KEY (period_id) REFERENCES periods(id)
);""",
    
    "phases": """CREATE TABLE IF NOT EXISTS phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL,
    description TEXT,
    init_date DATE,
    end_date DATE,
    delivery_deadline DATE,
    evaluation_deadline DATE,
    revaluation_deadline DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    program_id INTEGER NOT NULL,
    FOREIGN KEY (program_id) REFERENCES programs(id)
);""",
    
    "participants": """CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    names VARCHAR(50) NOT NULL,
    last_names VARCHAR(50) NOT NULL,
    email VARCHAR(40) NOT NULL UNIQUE,
    phone VARCHAR(40),
    dni VARCHAR(20) NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    dni_type_id INTEGER NOT NULL,
    nation_id INTEGER NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (dni_type_id) REFERENCES dni_types(id),
    FOREIGN KEY (nation_id) REFERENCES nations(id)
);""",
    
    "internals": """CREATE TABLE IF NOT EXISTS internals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    carrere_id INTEGER NOT NULL,
    FOREIGN KEY (participant_id) REFERENCES participants(id),
    FOREIGN KEY (period_id) REFERENCES periods(id),
    FOREIGN KEY (carrere_id) REFERENCES carreres(id),
    UNIQUE(participant_id, period_id)
);""",
    
    "externals": """CREATE TABLE IF NOT EXISTS externals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL,
    FOREIGN KEY (participant_id) REFERENCES participants(id)
);""",
    
    "workers": """CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    names VARCHAR(50) NOT NULL,
    last_names VARCHAR(50) NOT NULL,
    email VARCHAR(40) NOT NULL UNIQUE,
    phone VARCHAR(40),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER
);""",
    
    "internal_workers": """CREATE TABLE IF NOT EXISTS internal_workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,
    code INTEGER NOT NULL,
    FOREIGN KEY (worker_id) REFERENCES workers(id),
    UNIQUE(worker_id)
);""",
    
    "external_workers": """CREATE TABLE IF NOT EXISTS external_workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,
    FOREIGN KEY (worker_id) REFERENCES workers(id),
    UNIQUE(worker_id)
);""",
    
    "mentors": """CREATE TABLE IF NOT EXISTS mentors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,
    FOREIGN KEY (worker_id) REFERENCES workers(id),
    UNIQUE(worker_id)
);""",
    
    "mentors_specialisms": """CREATE TABLE IF NOT EXISTS mentors_specialisms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER NOT NULL,
    specialism_id INTEGER NOT NULL,
    FOREIGN KEY (mentor_id) REFERENCES mentors(id),
    FOREIGN KEY (specialism_id) REFERENCES specialisms(id),
    UNIQUE(mentor_id, specialism_id)
);"""
}


# =========================================================
# FUNCIONES DE PROCESAMIENTO
# =========================================================

def find_sql_files(migrations_path: str) -> List[str]:
    sql_files = []
    
    if not os.path.exists(migrations_path):
        os.makedirs(migrations_path, exist_ok=True)
        return []
    
    pattern = os.path.join(migrations_path, "*.sql")
    sql_files.extend(glob.glob(pattern))
    sql_files.sort()
    return sql_files


def read_sql_file(filepath: str) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            return f.read()


def extract_table_names(sql_content: str) -> List[str]:
    tables = set()
    
    lines = sql_content.split('\n')
    clean_lines = []
    for line in lines:
        if '--' in line:
            line_without_comments = line.split('--')[0]
            clean_lines.append(line_without_comments)
        else:
            clean_lines.append(line)
    
    sql_clean = '\n'.join(clean_lines)
    
    patterns = [
        r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?([a-z_][a-z0-9_]*)["`]?',
        r'CREATE\s+TABLE\s+["`]?([a-z_][a-z0-9_]*)["`]?',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, sql_clean, re.IGNORECASE)
        for match in matches:
            table_name = match.lower().strip()
            if table_name and len(table_name) > 2:
                tables.add(table_name)
    
    return list(tables)


def generate_enhanced_chunks(sql_files: List[str]) -> List[Dict[str, Any]]:
    all_chunks = []
    
    # Procesar archivos SQL existentes
    for filepath in sql_files:
        filename = os.path.basename(filepath)
        content = read_sql_file(filepath)
        tables_in_file = extract_table_names(content)
        
        print(f"\n📖 Procesando: {filename}")
        print(f"   Tablas encontradas: {tables_in_file}")
        
        all_chunks.append({
            "id": f"{filename}_full",
            "text": content,
            "metadata": {
                "source_file": filename,
                "chunk_type": "full_file",
                "tables": ",".join(tables_in_file),
                "num_tables": len(tables_in_file),
                "char_length": len(content)
            }
        })
        
        create_statements = re.split(r'(?=CREATE\s+TABLE)', content, flags=re.IGNORECASE)
        for i, stmt in enumerate(create_statements):
            if 'CREATE TABLE' in stmt.upper():
                stmt_tables = extract_table_names(stmt)
                all_chunks.append({
                    "id": f"{filename}_create_{i}",
                    "text": stmt.strip(),
                    "metadata": {
                        "source_file": filename,
                        "chunk_type": "create_table",
                        "tables": ",".join(stmt_tables),
                        "num_tables": len(stmt_tables),
                        "char_length": len(stmt)
                    }
                })
    
    # Añadir chunks del esquema objetivo
    print("\n📦 Generando chunks del esquema objetivo...")
    
    # Descripción general del esquema
    schema_description = """Sistema de gestión de programas, participantes, trabajadores y mentores.

Tablas principales (19 tablas en total):

CATÁLOGOS:
- document_types: Tipos de documentos
- industries: Industrias/sectores
- specialisms: Especialidades para mentores
- carrere_grades: Grados académicos (pregrado, posgrado, etc.)
- carreres: Carreras profesionales
- program_types: Tipos de programa (diplomado, curso, taller)
- dni_types: Tipos de documento de identidad
- nations: Nacionalidades
- periods: Períodos académicos

ESTRUCTURA PRINCIPAL:
- programs: Programas académicos (nombre, descripción, fechas)
- phases: Fases de cada programa (fechas de inicio, fin, entregas)

PARTICIPANTES:
- participants: Datos personales de participantes
- internals: Participantes internos (con código, período, carrera)
- externals: Participantes externos

TRABAJADORES:
- workers: Datos personales de trabajadores
- internal_workers: Trabajadores internos (con código)
- external_workers: Trabajadores externos
- mentors: Mentores (trabajadores que actúan como mentores)
- mentors_specialisms: Relación mentores-especialidades

Relaciones clave:
- Un programa tiene muchas fases
- Un participante puede ser INTERNO (con código, período, carrera) o EXTERNO
- Un trabajador puede ser INTERNO, EXTERNO o MENTOR
- Un mentor puede tener múltiples especialidades"""
    
    all_chunks.append({
        "id": "schema_description",
        "text": schema_description,
        "metadata": {
            "source_file": "schema",
            "chunk_type": "description",
            "tables": ",".join(TARGET_TABLES),
            "num_tables": len(TARGET_TABLES),
            "char_length": len(schema_description)
        }
    })
    
    # Descripciones mejoradas por tabla
    descriptions = {
        "programs": "Tabla de programas: Define los programas académicos con nombre, descripción, URLs de imagen/PDF, máximo de participantes por equipo, relación con tipo de programa y período.",
        "phases": "Tabla de fases: Define las fases de cada programa con fechas de inicio, fin, entregas, evaluaciones y reevaluaciones.",
        "participants": "Tabla de participantes: Almacena información personal de participantes (nombres, email, DNI) con relación a tipo de DNI y nacionalidad.",
        "internals": "Tabla de participantes internos: Participantes que pertenecen a la institución, con código, período y carrera.",
        "externals": "Tabla de participantes externos: Participantes externos a la institución.",
        "workers": "Tabla de trabajadores: Almacena información de trabajadores (nombres, email, teléfono).",
        "internal_workers": "Tabla de trabajadores internos: Trabajadores de la institución con código.",
        "external_workers": "Tabla de trabajadores externos: Trabajadores externos a la institución.",
        "mentors": "Tabla de mentores: Trabajadores que actúan como mentores.",
        "mentors_specialisms": "Tabla de relación: Conecta mentores con sus especialidades (relación muchos-a-muchos).",
        "specialisms": "Tabla de especialidades: Define las áreas de expertise de los mentores.",
        "carreres": "Tabla de carreras: Define las carreras profesionales con relación a grado académico.",
        "periods": "Tabla de períodos: Define períodos académicos con fechas de inicio y fin."
    }
    
    for table_name, create_sql in SCHEMA_SQL.items():
        all_chunks.append({
            "id": f"schema_{table_name}",
            "text": create_sql,
            "metadata": {
                "source_file": "schema",
                "chunk_type": "table_sql",
                "tables": table_name,
                "num_tables": 1,
                "char_length": len(create_sql)
            }
        })
        
        if table_name in descriptions:
            enhanced_text = f"{descriptions[table_name]}\n\n{create_sql}"
            all_chunks.append({
                "id": f"schema_{table_name}_enhanced",
                "text": enhanced_text,
                "metadata": {
                    "source_file": "schema",
                    "chunk_type": "table_enhanced",
                    "tables": table_name,
                    "num_tables": 1,
                    "char_length": len(enhanced_text)
                }
            })
    
    # Chunk de relaciones
    relationships_text = """Relaciones del esquema (SQLite con FOREIGN KEY constraints):

1. programs → program_types (N:1) - Cada programa tiene un tipo
2. programs → periods (N:1) - Cada programa pertenece a un período
3. phases → programs (N:1) - Cada fase pertenece a un programa
4. participants → dni_types (N:1) - Cada participante tiene un tipo de DNI
5. participants → nations (N:1) - Cada participante tiene una nacionalidad
6. carreres → carrere_grades (N:1) - Cada carrera tiene un grado académico
7. internals → participants (1:1) - Participante interno (relación 1-1)
8. internals → periods (N:1) - Participante interno tiene un período
9. internals → carreres (N:1) - Participante interno tiene una carrera
10. externals → participants (1:1) - Participante externo (relación 1-1)
11. internal_workers → workers (1:1) - Trabajador interno (relación 1-1)
12. external_workers → workers (1:1) - Trabajador externo (relación 1-1)
13. mentors → workers (1:1) - Mentor (relación 1-1)
14. mentors_specialisms → mentors (N:1) - Un mentor puede tener múltiples especialidades
15. mentors_specialisms → specialisms (N:1) - Una especialidad puede tener múltiples mentores

Jerarquía de participantes:
- Un participante puede ser INTERNO (con código, período, carrera) o EXTERNO

Jerarquía de trabajadores:
- Un trabajador puede ser INTERNO (con código), EXTERNO o MENTOR
- Un mentor puede tener múltiples especialidades (relación muchos-a-muchos)

Restricciones de unicidad:
- UNIQUE(participant_id, period_id) en internals
- UNIQUE(worker_id) en internal_workers, external_workers, mentors
- UNIQUE(mentor_id, specialism_id) en mentors_specialisms
- UNIQUE(email) en participants y workers
- UNIQUE(dni) en participants"""
    
    all_chunks.append({
        "id": "schema_relationships",
        "text": relationships_text,
        "metadata": {
            "source_file": "schema",
            "chunk_type": "relationships",
            "tables": ",".join(TARGET_TABLES),
            "num_tables": len(TARGET_TABLES),
            "char_length": len(relationships_text)
        }
    })
    
    return all_chunks


# =========================================================
# BASE DE DATOS SQLITE3
# =========================================================

def cosine_similarity(emb1: List[float], emb2: List[float]) -> float:
    vec1 = np.array(emb1)
    vec2 = np.array(emb2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def init_sqlite_database(db_path: str):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                chunk_type TEXT,
                source_file TEXT,
                tables TEXT,
                num_tables INTEGER,
                char_length INTEGER,
                relationship TEXT,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunk_type ON chunks(chunk_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_file ON chunks(source_file)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tables ON chunks(tables)")
        
        conn.commit()
        conn.close()
        
        print("✅ Base de datos SQLite3 inicializada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando SQLite: {e}")
        return False


def add_chunks_to_sqlite(db_path: str, chunks: List[Dict], model: SentenceTransformer):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        text = chunk["text"]
        embedding = model.encode(text).tolist()
        embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
        
        metadata = chunk["metadata"]
        
        cursor.execute("""
            INSERT OR REPLACE INTO chunks 
            (id, text, chunk_type, source_file, tables, num_tables, char_length, relationship, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chunk["id"],
            text,
            metadata.get("chunk_type", "unknown"),
            metadata.get("source_file", ""),
            metadata.get("tables", ""),
            metadata.get("num_tables", 0),
            metadata.get("char_length", len(text)),
            metadata.get("relationship", ""),
            embedding_bytes
        ))
        
        if (i + 1) % 20 == 0:
            conn.commit()
            print(f"   Progreso: {i + 1}/{total} chunks")
    
    conn.commit()
    conn.close()
    print(f"   ✅ {total} chunks insertados en SQLite3")


def get_all_chunks(db_path: str):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, text, embedding, chunk_type, source_file, tables FROM chunks")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"❌ Error obteniendo chunks: {e}")
        return []


def search_similar_chunks(db_path: str, query_text: str, model: SentenceTransformer, k: int = 5) -> List[tuple]:
    try:
        query_embedding = model.encode(query_text).tolist()
        rows = get_all_chunks(db_path)
        
        similarities = []
        for row in rows:
            chunk_id, chunk_text, embedding_bytes, _, _, _ = row
            chunk_embedding = np.frombuffer(embedding_bytes, dtype=np.float32).tolist()
            similarity = cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((similarity, chunk_id, chunk_text))
        
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [(chunk_id, chunk_text, sim) for sim, chunk_id, chunk_text in similarities[:k]]
        
    except Exception as e:
        print(f"❌ Error buscando chunks: {e}")
        return []


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def index_all_migrations():
    print("=" * 70)
    print("🚀 REINDEXACIÓN CON SQLITE3 - ESQUEMA DE PROGRAMAS")
    print("=" * 70)
    
    if not os.path.exists(MIGRATIONS_PATH):
        os.makedirs(MIGRATIONS_PATH, exist_ok=True)
        print(f"📁 Directorio creado: {MIGRATIONS_PATH}")
    
    sql_files = find_sql_files(MIGRATIONS_PATH)
    print(f"\n📁 Archivos encontrados: {len(sql_files)}")
    for f in sql_files:
        print(f"   - {os.path.basename(f)}")
    
    print(f"\n🔧 Cargando modelo: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print(f"✅ Modelo cargado (dimensión: {model.get_sentence_embedding_dimension()})")
    
    print("\n📦 Generando chunks...")
    all_chunks = generate_enhanced_chunks(sql_files)
    
    print(f"\n📊 Estadísticas:")
    print(f"   - Archivos SQL: {len(sql_files)}")
    print(f"   - Chunks generados: {len(all_chunks)}")
    
    chunk_types = {}
    for chunk in all_chunks:
        ctype = chunk["metadata"]["chunk_type"]
        chunk_types[ctype] = chunk_types.get(ctype, 0) + 1
    
    print(f"\n   Tipos de chunks:")
    for ctype, count in sorted(chunk_types.items()):
        print(f"      - {ctype}: {count}")
    
    print(f"\n💾 Inicializando SQLite3...")
    if not init_sqlite_database(SQLITE_PATH):
        return False
    
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chunks")
        conn.commit()
        conn.close()
        print("   Tabla limpiada")
    except Exception as e:
        print(f"   ⚠️ Error limpiando tabla: {e}")
    
    print(f"\n💾 Insertando chunks con embeddings...")
    add_chunks_to_sqlite(SQLITE_PATH, all_chunks, model)
    
    rows = get_all_chunks(SQLITE_PATH)
    count = len(rows)
    
    print("\n" + "=" * 70)
    print("📊 RESULTADO FINAL")
    print("=" * 70)
    print(f"\n✅ Total de chunks indexados: {count}")
    
    print("\n🔍 VERIFICANDO TABLAS DEL ESQUEMA:")
    for table in TARGET_TABLES[:10]:
        found = sum(1 for row in rows if table in row[5] if row[5])
        if found > 0:
            print(f"   ✅ {table}: encontrado ({found} chunks)")
        else:
            print(f"   ⚠️ {table}: no encontrado")
    
    print("\n" + "=" * 70)
    print("✅ REINDEXACIÓN COMPLETADA")
    print("=" * 70)
    
    return count > 0


def quick_check():
    rows = get_all_chunks(SQLITE_PATH)
    count = len(rows)
    print(f"\n✅ Base SQLite existe con {count} chunks")
    
    if count > 0:
        print("\n📋 Muestra de chunks:")
        for i, row in enumerate(rows[:3]):
            print(f"   {i+1}. ID: {row[0]}")
            print(f"      Tipo: {row[3]}")
            print(f"      Tablas: {row[5][:50] if row[5] else 'N/A'}...")
    
    return count


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🔄 SISTEMA DE INDEXACIÓN CON SQLITE3 - PROGRAMAS")
    print("=" * 70)
    
    print(f"\n📂 Migraciones: {MIGRATIONS_PATH}")
    print(f"💾 SQLite DB: {SQLITE_PATH}")
    
    print(f"\n📋 Tablas objetivo ({len(TARGET_TABLES)} tablas):")
    for table in TARGET_TABLES[:10]:
        print(f"   - {table}")
    print(f"   ... y {len(TARGET_TABLES) - 10} tablas más")
    
    print("\n🔍 Estado antes de reindexar:")
    current_count = quick_check()
    
    print(f"\n📊 Chunks actuales: {current_count}")
    
    response = input(f"\n¿Reindexar con SQLite3 para el esquema de programas? (s/n): ")
    
    if response.lower() == 's':
        success = index_all_migrations()
        if success:
            print("\n" + "=" * 70)
            print("🎉 ¡REINDEXACIÓN COMPLETADA EXITOSAMENTE!")
            print("=" * 70)
            print(f"\n📊 Chunks ahora: {quick_check()}")
        else:
            print("\n❌ Falló la reindexación")
    else:
        print("\n❌ Reindexación cancelada")