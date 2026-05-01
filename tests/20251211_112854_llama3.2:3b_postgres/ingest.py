# ingest_postgres_programas.py - Versión corregida para PostgreSQL

import os
import re
import glob
import json
import psycopg2
from psycopg2 import sql
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

# =========================================================
# CONFIGURACIÓN
# =========================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATIONS_PATH = os.path.join(CURRENT_DIR, "migrations")
BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

# Configuración PostgreSQL
POSTGRES_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123',
    'database': 'rag_system_programas',
    'port': 5432
}

# Modelo de embeddings
MODEL_NAME = "all-MiniLM-L6-v2"

# Tablas del esquema objetivo
TARGET_TABLES = [
    'document_types', 'industries', 'specialisms', 'carrere_grades', 'carreres',
    'program_types', 'dni_types', 'nations', 'periods', 'programs', 'phases',
    'participants', 'internals', 'externals', 'workers', 'internal_workers',
    'external_workers', 'mentors', 'mentors_specialisms'
]


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

Tablas principales:
- CATÁLOGOS: document_types, industries, specialisms, carrere_grades, carreres, program_types, dni_types, nations, periods
- PROGRAMAS: programs, phases
- PARTICIPANTES: participants, internals, externals
- TRABAJADORES: workers, internal_workers, external_workers, mentors, mentors_specialisms

Relaciones clave:
- Un programa tiene muchas fases
- Un participante puede ser interno (con código, período, carrera) o externo
- Un trabajador puede ser interno, externo o mentor
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
    
    # Chunk de relaciones
    relationships_text = """Relaciones del esquema:

1. programs → program_types, periods
2. phases → programs
3. participants → dni_types, nations
4. carreres → carrere_grades
5. internals → participants, periods, carreres
6. externals → participants
7. internal_workers → workers
8. external_workers → workers
9. mentors → workers
10. mentors_specialisms → mentors, specialisms"""
    
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
# BASE DE DATOS POSTGRESQL
# =========================================================

def init_postgres_database():
    try:
        # Conectar a postgres para crear la DB
        conn = psycopg2.connect(
            host=POSTGRES_CONFIG['host'],
            user=POSTGRES_CONFIG['user'],
            password=POSTGRES_CONFIG['password'],
            port=POSTGRES_CONFIG['port'],
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Crear base de datos
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{POSTGRES_CONFIG['database']}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {POSTGRES_CONFIG['database']}")
            print(f"✅ Base de datos {POSTGRES_CONFIG['database']} creada")
        else:
            print(f"✅ Base de datos {POSTGRES_CONFIG['database']} ya existe")
        
        cursor.close()
        conn.close()
        
        # Conectar a la base de datos específica
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Crear tabla de chunks (sin vector, usando JSONB)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id VARCHAR(255) PRIMARY KEY,
                text TEXT NOT NULL,
                chunk_type VARCHAR(50),
                source_file VARCHAR(255),
                tables TEXT,
                num_tables INTEGER,
                char_length INTEGER,
                relationship VARCHAR(255),
                embedding JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices para búsqueda rápida
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunk_type ON chunks(chunk_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_file ON chunks(source_file)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tables ON chunks(tables)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Base de datos PostgreSQL inicializada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando PostgreSQL: {e}")
        return False


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


def add_chunks_to_postgres(chunks: List[Dict], model: SentenceTransformer):
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            text = chunk["text"]
            embedding = model.encode(text).tolist()
            embedding_json = json.dumps(embedding)
            
            metadata = chunk["metadata"]
            
            cursor.execute("""
                INSERT INTO chunks 
                (id, text, chunk_type, source_file, tables, num_tables, char_length, relationship, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (id) DO UPDATE SET
                text = EXCLUDED.text,
                embedding = EXCLUDED.embedding
            """, (
                chunk["id"],
                text,
                metadata.get("chunk_type", "unknown"),
                metadata.get("source_file", ""),
                metadata.get("tables", ""),
                metadata.get("num_tables", 0),
                metadata.get("char_length", len(text)),
                metadata.get("relationship", ""),
                embedding_json
            ))
            
            if (i + 1) % 20 == 0:
                conn.commit()
                print(f"   Progreso: {i + 1}/{total} chunks")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"   ✅ {total} chunks insertados en PostgreSQL")
        
    except Exception as e:
        print(f"❌ Error insertando chunks: {e}")
        import traceback
        traceback.print_exc()


def get_all_chunks():
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, text, embedding, chunk_type, source_file, tables FROM chunks")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"❌ Error obteniendo chunks: {e}")
        return []


def search_similar_chunks(query_text: str, model: SentenceTransformer, k: int = 5) -> List[tuple]:
    try:
        query_embedding = model.encode(query_text).tolist()
        rows = get_all_chunks()
        
        similarities = []
        for row in rows:
            chunk_id, chunk_text, embedding_json, _, _, _ = row
            similarity = cosine_similarity(query_embedding, embedding_json)
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
    print("🚀 REINDEXACIÓN CON POSTGRESQL - ESQUEMA DE PROGRAMAS")
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
    
    print(f"\n💾 Inicializando PostgreSQL...")
    if not init_postgres_database():
        return False
    
    # Limpiar tabla existente
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chunks")
        conn.commit()
        cursor.close()
        conn.close()
        print("   Tabla limpiada")
    except Exception as e:
        print(f"   Tabla nueva, no es necesario limpiar")
    
    print(f"\n💾 Insertando chunks con embeddings...")
    add_chunks_to_postgres(all_chunks, model)
    
    rows = get_all_chunks()
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
    rows = get_all_chunks()
    count = len(rows)
    print(f"\n✅ Base PostgreSQL existe con {count} chunks")
    
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
    print("🔄 SISTEMA DE INDEXACIÓN CON POSTGRESQL - PROGRAMAS")
    print("=" * 70)
    
    print(f"\n📂 Migraciones: {MIGRATIONS_PATH}")
    print(f"💾 PostgreSQL DB: {POSTGRES_CONFIG['database']} en {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
    print(f"👤 Usuario: {POSTGRES_CONFIG['user']}")
    
    print(f"\n📋 Tablas objetivo ({len(TARGET_TABLES)} tablas):")
    for table in TARGET_TABLES[:10]:
        print(f"   - {table}")
    print(f"   ... y {len(TARGET_TABLES) - 10} tablas más")
    
    try:
        import psycopg2
        print(f"\n✅ psycopg2 versión: {psycopg2.__version__}")
    except ImportError:
        print("❌ psycopg2 no está instalado. Ejecute: pip install psycopg2-binary")
        exit(1)
    
    print("\n🔍 Estado antes de reindexar:")
    current_count = quick_check()
    
    print(f"\n📊 Chunks actuales: {current_count}")
    
    response = input(f"\n¿Reindexar con PostgreSQL para el esquema de programas? (s/n): ")
    
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