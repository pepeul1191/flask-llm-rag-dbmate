# ingest_postgres_schema.py - Versión para PostgreSQL con esquema de usuarios/sistemas/roles

import os
import re
import glob
import json
import psycopg2
from psycopg2 import sql, extras
import numpy as np
from typing import List, Dict, Any, Optional
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
    'password': '123',  # Cambiar por tu contraseña
    'database': 'rag_system',
    'port': 5432
}

# Configuración de chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Modelo de embeddings
MODEL_NAME = "all-MiniLM-L6-v2"

# Tablas del esquema objetivo
TARGET_TABLES = ['users', 'systems', 'roles', 'permissions', 'systems_users', 'systems_users_permissions']

# Sentencias SQL del esquema para PostgreSQL
SCHEMA_SQL = {
    "users": """CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(20) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    activation_key VARCHAR(30),
    reset_key VARCHAR(30),
    email VARCHAR(50) NOT NULL UNIQUE,
    activated BOOLEAN DEFAULT FALSE,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
    
    "systems": """CREATE TABLE IF NOT EXISTS systems (
    id SERIAL PRIMARY KEY,
    name VARCHAR(40) NOT NULL UNIQUE,
    description TEXT,
    repository VARCHAR(100),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
    
    "roles": """CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    system_id INTEGER NOT NULL,
    FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE,
    UNIQUE(name, system_id)
);""",
    
    "permissions": """CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE(name, role_id)
);""",
    
    "systems_users": """CREATE TABLE IF NOT EXISTS systems_users (
    id SERIAL PRIMARY KEY,
    system_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(system_id, user_id)
);""",
    
    "systems_users_permissions": """CREATE TABLE IF NOT EXISTS systems_users_permissions (
    id SERIAL PRIMARY KEY,
    system_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE(system_id, user_id, permission_id)
);"""
}

# Función para actualizar timestamp automáticamente
UPDATE_TIMESTAMP_FUNCTION = """
CREATE OR REPLACE FUNCTION update_updated_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
"""

# Triggers para actualizar updated automáticamente
TRIGGERS = {
    "users": """
    DROP TRIGGER IF EXISTS update_users_updated ON users;
    CREATE TRIGGER update_users_updated
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_column();
    """,
    "systems": """
    DROP TRIGGER IF EXISTS update_systems_updated ON systems;
    CREATE TRIGGER update_systems_updated
        BEFORE UPDATE ON systems
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_column();
    """,
    "roles": """
    DROP TRIGGER IF EXISTS update_roles_updated ON roles;
    CREATE TRIGGER update_roles_updated
        BEFORE UPDATE ON roles
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_column();
    """,
    "permissions": """
    DROP TRIGGER IF EXISTS update_permissions_updated ON permissions;
    CREATE TRIGGER update_permissions_updated
        BEFORE UPDATE ON permissions
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_column();
    """
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
        print(f"   Foreign keys: {len(fks)}")
        
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
    schema_description = f"""Sistema de gestión de usuarios, sistemas, roles y permisos para PostgreSQL.

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

Características de PostgreSQL:
- SERIAL para auto-incremento
- TIMESTAMP con zona horaria
- ON DELETE CASCADE para integridad referencial
- Triggers para actualizar updated automáticamente

Consultas típicas:
- Obtener sistemas de un usuario: SELECT s.* FROM systems s JOIN systems_users su ON s.id = su.system_id WHERE su.user_id = $1
- Obtener roles de un sistema: SELECT * FROM roles WHERE system_id = $1
- Obtener permisos de un rol: SELECT * FROM permissions WHERE role_id = $1
- Verificar permiso especial: SELECT * FROM systems_users_permissions WHERE user_id = $1 AND system_id = $2 AND permission_id = $3"""
    
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
    descriptions = {
        "users": "Tabla de usuarios: Almacena credenciales (username, password), datos de contacto (email), claves de activación/reset, y estado de activación. Usa SERIAL para ID auto-incrementable.",
        "systems": "Tabla de sistemas: Define las aplicaciones en la plataforma con nombre, descripción y repositorio. Usa SERIAL para ID.",
        "roles": "Tabla de roles: Define roles por sistema (ej: admin, editor, viewer) con relación a systems. Incluye FOREIGN KEY a systems(id).",
        "permissions": "Tabla de permisos: Define permisos específicos asociados a roles (ej: create, read, update, delete). Incluye FOREIGN KEY a roles(id).",
        "systems_users": "Tabla de relación: Conecta usuarios con sistemas (qué usuario tiene acceso a qué sistema). Incluye FOREIGN KEYS a systems(id) y users(id).",
        "systems_users_permissions": "Tabla de permisos especiales: Permite asignar permisos específicos a un usuario en un sistema. Incluye 3 FOREIGN KEYS."
    }
    
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
    relationships_text = """Relaciones del esquema PostgreSQL con FOREIGN KEY constraints:

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

Todas las tablas usan SERIAL como tipo de dato para PRIMARY KEY.
Las tablas users, systems, roles y permissions tienen triggers para actualizar updated automáticamente."""
    
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
    """Inicializa PostgreSQL con tabla para embeddings usando vector extension"""
    
    try:
        # Conectar a la base de datos por defecto para crear la DB
        conn = psycopg2.connect(
            host=POSTGRES_CONFIG['host'],
            user=POSTGRES_CONFIG['user'],
            password=POSTGRES_CONFIG['password'],
            port=POSTGRES_CONFIG['port'],
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Crear base de datos si no existe
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{POSTGRES_CONFIG['database']}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {POSTGRES_CONFIG['database']}")
            print(f"✅ Base de datos {POSTGRES_CONFIG['database']} creada")
        
        cursor.close()
        conn.close()
        
        # Conectar a la base de datos específica
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Habilitar extensión vector (para embeddings nativos)
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Crear tabla de chunks con soporte vectorial
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
                embedding VECTOR(384),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear índice para búsqueda vectorial (IVFFlat)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
            ON chunks 
            USING ivfflat (embedding vector_cosine_ops)
        """)
        
        # Índices para búsqueda rápida
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunk_type ON chunks(chunk_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_file ON chunks(source_file)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tables ON chunks(tables)")
        
        # Crear índice GIN para búsqueda textual
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_text_gin ON chunks USING gin(to_tsvector('spanish', text))")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Base de datos PostgreSQL inicializada correctamente (con extensión vector)")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando PostgreSQL: {e}")
        return False


def add_chunks_to_postgres(chunks: List[Dict], model: SentenceTransformer):
    """Agrega chunks a PostgreSQL con sus embeddings usando vector extension"""
    
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            # Generar embedding
            text = chunk["text"]
            embedding = model.encode(text).tolist()
            
            # Convertir embedding a string para PostgreSQL vector
            embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
            
            metadata = chunk["metadata"]
            
            cursor.execute("""
                INSERT INTO chunks 
                (id, text, chunk_type, source_file, tables, num_tables, char_length, relationship, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
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
                embedding_str
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


def search_similar_chunks_postgres(query_text: str, model: SentenceTransformer, k: int = 5) -> List[tuple]:
    """Busca chunks similares usando vector cosine similarity en PostgreSQL"""
    
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Generar embedding de la query
        query_embedding = model.encode(query_text).tolist()
        query_embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'
        
        # Búsqueda por similitud coseno usando vector extension
        cursor.execute("""
            SELECT id, text, 1 - (embedding <=> %s::vector) as similarity
            FROM chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding_str, query_embedding_str, k))
        
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [(row[0], row[1], row[2]) for row in rows]
        
    except Exception as e:
        print(f"❌ Error buscando chunks: {e}")
        return []


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def index_all_migrations():
    """Indexa todas las migraciones en PostgreSQL"""
    
    print("=" * 70)
    print("🚀 REINDEXACIÓN CON POSTGRESQL - ESQUEMA USUARIOS/SISTEMAS/ROLES")
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
    print(f"   Dimensión del embedding: {model.get_sentence_embedding_dimension()}")
    
    # Generar chunks
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
    
    # Inicializar PostgreSQL
    print(f"\n💾 Inicializando PostgreSQL...")
    if not init_postgres_database():
        print("❌ No se pudo inicializar la base de datos")
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
        print(f"   ⚠️ Error limpiando tabla: {e}")
    
    # Insertar chunks
    print(f"\n💾 Insertando chunks con embeddings (usando VECTOR)...")
    add_chunks_to_postgres(all_chunks, model)
    
    # Verificar
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
    except:
        count = 0
    
    print("\n" + "=" * 70)
    print("📊 RESULTADO FINAL")
    print("=" * 70)
    print(f"\n✅ Total de chunks indexados: {count}")
    
    # Verificar tablas específicas
    print("\n🔍 VERIFICANDO TABLAS DEL ESQUEMA:")
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        for table in TARGET_TABLES:
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE tables LIKE %s", (f'%{table}%',))
            found = cursor.fetchone()[0]
            if found > 0:
                print(f"   ✅ {table}: encontrado ({found} chunks)")
            else:
                print(f"   ⚠️ {table}: no encontrado en chunks existentes")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"   Error verificando: {e}")
    
    print("\n" + "=" * 70)
    print("✅ REINDEXACIÓN COMPLETADA")
    print("=" * 70)
    print("\n💡 Ahora ejecute: python3 test_end_2_end_postgres_schema.py")
    
    return count > 0


def quick_check():
    """Verificación rápida del estado PostgreSQL"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks")
        count = cursor.fetchone()[0]
        print(f"\n✅ Base PostgreSQL existe con {count} chunks")
        
        if count > 0:
            print("\n📋 Muestra de chunks:")
            cursor.execute("SELECT id, chunk_type, tables FROM chunks LIMIT 5")
            rows = cursor.fetchall()
            for i, (chunk_id, chunk_type, tables) in enumerate(rows):
                print(f"   {i+1}. {chunk_id}")
                print(f"      Tipo: {chunk_type}")
                print(f"      Tablas: {tables[:50] if tables else 'N/A'}...")
        
        cursor.close()
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
    print("🔄 SISTEMA DE INDEXACIÓN CON POSTGRESQL")
    print("=" * 70)
    
    print(f"\n📂 Migraciones: {MIGRATIONS_PATH}")
    print(f"💾 PostgreSQL DB: {POSTGRES_CONFIG['database']} en {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
    
    print(f"\n📋 Tablas objetivo:")
    for table in TARGET_TABLES:
        print(f"   - {table}")
    
    # Verificar psycopg2
    try:
        import psycopg2
        print(f"\n✅ psycopg2 versión: {psycopg2.__version__}")
    except ImportError:
        print("❌ psycopg2 no está instalado. Ejecute: pip install psycopg2-binary")
        exit(1)
    
    # Verificar estado actual
    print("\n🔍 Estado antes de reindexar:")
    current_count = quick_check()
    
    print(f"\n📊 Chunks actuales: {current_count}")
    
    response = input(f"\n¿Reindexar con PostgreSQL para el nuevo esquema? (s/n): ")
    
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