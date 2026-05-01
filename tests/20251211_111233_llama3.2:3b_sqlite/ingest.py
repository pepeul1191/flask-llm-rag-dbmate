# ingest_sqlite_schema.py - Versión para SQLite3 con esquema de usuarios/sistemas/roles

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
SQLITE_PATH = os.path.join(BASE_PATH, "rag_system.db")

# Configuración de chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Modelo de embeddings
MODEL_NAME = "all-MiniLM-L6-v2"

# Tablas del esquema objetivo
TARGET_TABLES = ['users', 'systems', 'roles', 'permissions', 'systems_users', 'systems_users_permissions']

# Sentencias SQL del esquema
SCHEMA_SQL = {
    "users": """CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(20) NOT NULL,
    password VARCHAR(100) NOT NULL,
    activation_key VARCHAR(30),
    reset_key VARCHAR(30),
    email VARCHAR(50) NOT NULL,
    activated BOOLEAN DEFAULT 0,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP
);""",
    
    "systems": """CREATE TABLE systems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(40) NOT NULL,
    description TEXT,
    repository VARCHAR(100),
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP
);""",
    
    "roles": """CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(40) NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    system_id INTEGER NOT NULL,
    FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE
);""",
    
    "permissions": """CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(40) NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    role_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);""",
    
    "systems_users": """CREATE TABLE systems_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(system_id, user_id)
);""",
    
    "systems_users_permissions": """CREATE TABLE systems_users_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE(system_id, user_id, permission_id)
);"""
}


# =========================================================
# FUNCIONES DE PROCESAMIENTO
# =========================================================

def find_sql_files(migrations_path: str) -> List[str]:
    """Encuentra todos los archivos SQL"""
    sql_files = []
    
    if not os.path.exists(migrations_path):
        print(f"⚠️ No existe {migrations_path}, creando directorio...")
        os.makedirs(migrations_path, exist_ok=True)
        return []
    
    pattern = os.path.join(migrations_path, "*.sql")
    sql_files.extend(glob.glob(pattern))
    
    sql_files.sort()
    return sql_files


def read_sql_file(filepath: str) -> str:
    """Lee el contenido de un archivo SQL"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            return f.read()


def extract_table_names(sql_content: str) -> List[str]:
    """Extrae nombres de tablas del contenido SQL"""
    tables = set()
    
    # Eliminar comentarios
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


def extract_foreign_keys(sql_content: str) -> List[Dict[str, str]]:
    """Extrae relaciones de foreign keys"""
    fks = []
    
    fk_pattern = r'FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+([a-z_]+)\s*\(([^)]+)\)'
    matches = re.finditer(fk_pattern, sql_content, re.IGNORECASE)
    
    for match in matches:
        fks.append({
            'columns': match.group(1).strip(),
            'referenced_table': match.group(2).strip().lower(),
            'referenced_columns': match.group(3).strip()
        })
    
    return fks


def generate_enhanced_chunks(sql_files: List[str]) -> List[Dict[str, Any]]:
    """Genera chunks mejorados con múltiples estrategias"""
    all_chunks = []
    
    # Procesar archivos SQL existentes
    for filepath in sql_files:
        filename = os.path.basename(filepath)
        content = read_sql_file(filepath)
        tables_in_file = extract_table_names(content)
        fks = extract_foreign_keys(content)
        
        print(f"\n📖 Procesando: {filename}")
        print(f"   Tablas encontradas: {tables_in_file}")
        
        # 1. Chunk completo
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
        
        # 2. Chunks por CREATE TABLE
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
    
    # 3. Añadir chunks del esquema objetivo (para garantizar cobertura)
    print("\n📦 Generando chunks del esquema objetivo...")
    
    # Descripción general del esquema
    schema_description = f"""Sistema de gestión de usuarios, sistemas, roles y permisos para SQLite.

Tablas principales:
- users: Almacena información de usuarios (username, password, email, activation_key, reset_key, activated)
- systems: Define los diferentes sistemas/aplicaciones en la plataforma (name, description, repository)
- roles: Define roles por sistema (name, system_id) - relación con systems
- permissions: Permisos específicos asociados a roles (name, role_id) - relación con roles
- systems_users: Relación muchos-a-muchos entre usuarios y sistemas (system_id, user_id)
- systems_users_permissions: Permisos especiales por usuario y sistema (system_id, user_id, permission_id)

Relaciones clave:
- Un usuario puede tener acceso a múltiples sistemas (systems_users)
- Cada sistema tiene múltiples roles
- Cada rol tiene múltiples permisos
- Un usuario puede tener permisos especiales por sistema (systems_users_permissions)

Consultas típicas:
- Obtener sistemas de un usuario: SELECT s.* FROM systems s JOIN systems_users su ON s.id = su.system_id WHERE su.user_id = ?
- Obtener roles de un sistema: SELECT * FROM roles WHERE system_id = ?
- Obtener permisos de un rol: SELECT * FROM permissions WHERE role_id = ?
- Verificar permiso especial: SELECT * FROM systems_users_permissions WHERE user_id = ? AND system_id = ? AND permission_id = ?"""
    
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
    
    # Chunks individuales por tabla con SQL y descripción
    for table_name, create_sql in SCHEMA_SQL.items():
        # SQL puro
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
        
        # Descripción enriquecida + SQL
        descriptions = {
            "users": "Tabla de usuarios: Almacena credenciales (username, password), datos de contacto (email), claves de activación/reset, y estado de activación.",
            "systems": "Tabla de sistemas: Define las aplicaciones en la plataforma con nombre, descripción y repositorio.",
            "roles": "Tabla de roles: Define roles por sistema (ej: admin, editor, viewer) con relación a systems.",
            "permissions": "Tabla de permisos: Define permisos específicos asociados a roles (ej: create, read, update, delete).",
            "systems_users": "Tabla de relación: Conecta usuarios con sistemas (qué usuario tiene acceso a qué sistema).",
            "systems_users_permissions": "Tabla de permisos especiales: Permite asignar permisos específicos a un usuario en un sistema."
        }
        
        enhanced_text = f"{descriptions.get(table_name, '')}\n\n{create_sql}"
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

1. users (1) ---- (N) systems_users
   FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE

2. systems (1) ---- (N) systems_users
   FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE

3. systems (1) ---- (N) roles
   FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE

4. roles (1) ---- (N) permissions
   FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE

5. systems_users_permissions (tabla de permisos especiales):
   - FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE
   - FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
   - FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE

Todas las tablas tienen id INTEGER PRIMARY KEY AUTOINCREMENT."""
    
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

def init_sqlite_database(db_path: str):
    """Inicializa SQLite3 con tabla para embeddings"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Habilitar foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Crear tabla de chunks
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
    
    # Índices para búsqueda rápida
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunk_type ON chunks(chunk_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_file ON chunks(source_file)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tables ON chunks(tables)")
    
    conn.commit()
    conn.close()
    
    print("✅ Base de datos SQLite3 inicializada correctamente")
    return True


def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Calcula similitud coseno entre dos vectores"""
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def add_chunks_to_sqlite(db_path: str, chunks: List[Dict], model: SentenceTransformer):
    """Agrega chunks a SQLite con sus embeddings"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        # Generar embedding
        text = chunk["text"]
        embedding = model.encode(text).tolist()
        
        # Convertir embedding a bytes
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


def search_similar_chunks(db_path: str, query_text: str, model: SentenceTransformer, k: int = 5) -> List[tuple]:
    """Busca chunks similares usando similitud coseno"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Generar embedding de la query
    query_embedding = model.encode(query_text).tolist()
    
    # Obtener todos los chunks
    cursor.execute("SELECT id, text, embedding, chunk_type, source_file, tables FROM chunks")
    rows = cursor.fetchall()
    
    # Calcular similitud con cada chunk
    similarities = []
    for row in rows:
        chunk_id, chunk_text, embedding_bytes, chunk_type, source_file, tables = row
        chunk_embedding = np.frombuffer(embedding_bytes, dtype=np.float32).tolist()
        similarity = cosine_similarity(query_embedding, chunk_embedding)
        similarities.append((similarity, chunk_id, chunk_text, chunk_type, source_file, tables))
    
    # Ordenar por similitud descendente
    similarities.sort(key=lambda x: x[0], reverse=True)
    
    conn.close()
    
    # Retornar top k
    return [(chunk_id, chunk_text, similarity) 
            for similarity, chunk_id, chunk_text, _, _, _ in similarities[:k]]


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def index_all_migrations():
    """Indexa todas las migraciones en SQLite3"""
    
    print("=" * 70)
    print("🚀 REINDEXACIÓN CON SQLITE3 - ESQUEMA USUARIOS/SISTEMAS/ROLES")
    print("=" * 70)
    
    # Verificar directorio
    if not os.path.exists(MIGRATIONS_PATH):
        os.makedirs(MIGRATIONS_PATH, exist_ok=True)
        print(f"📁 Directorio creado: {MIGRATIONS_PATH}")
    
    # Encontrar archivos
    sql_files = find_sql_files(MIGRATIONS_PATH)
    print(f"\n📁 Archivos encontrados: {len(sql_files)}")
    for f in sql_files:
        print(f"   - {os.path.basename(f)}")
    
    # Cargar modelo de embeddings
    print(f"\n🔧 Cargando modelo: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("✅ Modelo cargado")
    
    # Generar chunks (incluye chunks del esquema objetivo)
    print("\n📦 Generando chunks...")
    all_chunks = generate_enhanced_chunks(sql_files)
    
    print(f"\n📊 Estadísticas:")
    print(f"   - Archivos SQL: {len(sql_files)}")
    print(f"   - Chunks generados: {len(all_chunks)}")
    
    # Contar tipos
    chunk_types = {}
    for chunk in all_chunks:
        ctype = chunk["metadata"]["chunk_type"]
        chunk_types[ctype] = chunk_types.get(ctype, 0) + 1
    
    print(f"\n   Tipos de chunks:")
    for ctype, count in sorted(chunk_types.items()):
        print(f"      - {ctype}: {count}")
    
    # Inicializar SQLite
    print(f"\n💾 Inicializando SQLite3 en: {SQLITE_PATH}")
    init_sqlite_database(SQLITE_PATH)
    
    # Limpiar tabla existente
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chunks")
        conn.commit()
        conn.close()
        print("   Tabla limpiada")
    except Exception as e:
        print(f"   ⚠️ Error limpiando tabla: {e}")
    
    # Insertar chunks
    print(f"\n💾 Insertando chunks con embeddings...")
    add_chunks_to_sqlite(SQLITE_PATH, all_chunks, model)
    
    # Verificar
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM chunks")
    count = cursor.fetchone()[0]
    conn.close()
    
    print("\n" + "=" * 70)
    print("📊 RESULTADO FINAL")
    print("=" * 70)
    print(f"\n✅ Total de chunks indexados: {count}")
    
    # Verificar tablas específicas
    print("\n🔍 VERIFICANDO TABLAS DEL ESQUEMA:")
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    
    for table in TARGET_TABLES:
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE tables LIKE ?", (f'%{table}%',))
        found = cursor.fetchone()[0]
        if found > 0:
            print(f"   ✅ {table}: encontrado ({found} chunks)")
        else:
            print(f"   ⚠️ {table}: no encontrado en chunks existentes")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ REINDEXACIÓN COMPLETADA")
    print("=" * 70)
    print("\n💡 Ahora ejecute: python3 test_end_2_end_sqlite_schema.py")
    
    return count > 0


def quick_check():
    """Verificación rápida del estado SQLite"""
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks")
        count = cursor.fetchone()[0]
        print(f"\n✅ Base SQLite existe con {count} chunks")
        
        if count > 0:
            print("\n📋 Muestra de chunks:")
            cursor.execute("SELECT id, chunk_type, tables FROM chunks LIMIT 5")
            rows = cursor.fetchall()
            for i, (chunk_id, chunk_type, tables) in enumerate(rows):
                print(f"   {i+1}. {chunk_id}")
                print(f"      Tipo: {chunk_type}")
                print(f"      Tablas: {tables[:50] if tables else 'N/A'}...")
        
        conn.close()
        return count
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 0


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🔄 SISTEMA DE INDEXACIÓN CON SQLITE3")
    print("=" * 70)
    
    print(f"\n📂 Migraciones: {MIGRATIONS_PATH}")
    print(f"💾 SQLite DB: {SQLITE_PATH}")
    
    print(f"\n📋 Tablas objetivo:")
    for table in TARGET_TABLES:
        print(f"   - {table}")
    
    # Verificar estado actual
    print("\n🔍 Estado antes de reindexar:")
    current_count = quick_check()
    
    print(f"\n📊 Chunks actuales: {current_count}")
    
    response = input(f"\n¿Reindexar con SQLite3 para el nuevo esquema? (s/n): ")
    
    if response.lower() == 's':
        success = index_all_migrations()
        if success:
            print("\n" + "=" * 70)
            print("🎉 ¡REINDEXACIÓN COMPLETADA EXITOSAMENTE!")
            print("=" * 70)
            print("\n📊 Comparación:")
            print(f"   Chunks antes: {current_count}")
            print(f"   Chunks ahora: {quick_check()}")
        else:
            print("\n❌ Falló la reindexación")
    else:
        print("\n❌ Reindexación cancelada")