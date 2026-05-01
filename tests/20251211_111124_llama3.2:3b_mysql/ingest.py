# ingest_mysql_schema.py - Versión para MySQL con el nuevo esquema (users, systems, roles, permissions)

import os
import re
import glob
import json
import pymysql
from pymysql import Error
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

# =========================================================
# CONFIGURACIÓN
# =========================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATIONS_PATH = os.path.join(CURRENT_DIR, "migrations")
BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

# Configuración MySQL
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123',
    'database': 'rag_system',
    'port': 3306,
    'charset': 'utf8mb4'
}

# Configuración de chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Modelo de embeddings
MODEL_NAME = "all-MiniLM-L6-v2"

# Esquema objetivo para generar chunks específicos
TARGET_SCHEMA = {
    'tables': ['users', 'systems', 'roles', 'permissions', 'systems_users', 'systems_users_permissions'],
    'relationships': [
        ('users', 'systems_users'),
        ('systems', 'systems_users'),
        ('systems', 'roles'),
        ('roles', 'permissions'),
        ('systems', 'systems_users_permissions'),
        ('users', 'systems_users_permissions'),
        ('permissions', 'systems_users_permissions')
    ]
}


# =========================================================
# FUNCIONES DE PROCESAMIENTO
# =========================================================

def find_sql_files(migrations_path: str) -> List[str]:
    """Encuentra todos los archivos SQL"""
    sql_files = []
    
    if not os.path.exists(migrations_path):
        print(f"❌ ERROR: No existe {migrations_path}")
        return []
    
    pattern = os.path.join(migrations_path, "*.sql")
    sql_files.extend(glob.glob(pattern))
    
    # Archivos sin extensión que parezcan SQL
    for file in glob.glob(os.path.join(migrations_path, "*")):
        if os.path.isfile(file) and not file.endswith('.sql'):
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(500)
                    if 'CREATE TABLE' in content.upper() or 'ALTER TABLE' in content.upper():
                        sql_files.append(file)
            except:
                pass
    
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
        r'ALTER\s+TABLE\s+["`]?([a-z_][a-z0-9_]*)["`]?',
        r'CREATE\s+TABLE\s+([a-z_][a-z0-9_]*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, sql_clean, re.IGNORECASE)
        for match in matches:
            table_name = match.lower().strip()
            if table_name and len(table_name) > 2 and not table_name.startswith('temp'):
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
    
    alter_pattern = r'ALTER\s+TABLE\s+([a-z_]+)\s+ADD\s+CONSTRAINT\s+\w+\s+FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+([a-z_]+)\s*\(([^)]+)\)'
    matches = re.finditer(alter_pattern, sql_content, re.IGNORECASE)
    
    for match in matches:
        fks.append({
            'table': match.group(1).strip().lower(),
            'columns': match.group(2).strip(),
            'referenced_table': match.group(3).strip().lower(),
            'referenced_columns': match.group(4).strip()
        })
    
    return fks


def generate_create_table_statements() -> Dict[str, str]:
    """Genera sentencias CREATE TABLE para el esquema"""
    
    statements = {
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
    
    return statements


def generate_enhanced_chunks(sql_files: List[str]) -> List[Dict[str, Any]]:
    """Genera chunks mejorados con múltiples estrategias"""
    all_chunks = []
    
    # Obtener sentencias CREATE TABLE del esquema objetivo
    schema_statements = generate_create_table_statements()
    
    for filepath in sql_files:
        filename = os.path.basename(filepath)
        content = read_sql_file(filepath)
        tables = extract_table_names(content)
        fks = extract_foreign_keys(content)
        
        print(f"\n📖 Procesando: {filename}")
        print(f"   Tablas encontradas: {tables}")
        print(f"   Foreign keys: {len(fks)}")
        
        # 1. Chunk completo
        all_chunks.append({
            "id": f"{filename}_full",
            "text": content,
            "metadata": {
                "source_file": filename,
                "chunk_type": "full_file",
                "tables": ",".join(tables),
                "num_tables": len(tables),
                "char_length": len(content),
                "schema_type": "original"
            }
        })
        
        # 2. Chunks por CREATE TABLE del archivo original
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
                        "char_length": len(stmt),
                        "schema_type": "original"
                    }
                })
    
    # 3. Añadir chunks del esquema objetivo (para garantizar cobertura)
    print("\n📦 Generando chunks del esquema objetivo...")
    
    # Descripción general del esquema
    schema_description = f"""Sistema de gestión de usuarios, sistemas, roles y permisos.

Tablas principales:
- users: Almacena información de usuarios (username, password, email, estado de activación)
- systems: Define los diferentes sistemas/aplicaciones en la plataforma
- roles: Define roles por sistema (administrador, editor, lector, etc.)
- permissions: Permisos específicos asociados a roles
- systems_users: Relación muchos-a-muchos entre usuarios y sistemas
- systems_users_permissions: Permisos específicos por usuario y sistema

Relaciones:
- Un usuario puede tener acceso a múltiples sistemas (systems_users)
- Cada sistema tiene múltiples roles
- Cada rol tiene múltiples permisos
- Un usuario puede tener permisos especiales por sistema (systems_users_permissions)

Esta estructura permite un control de acceso granular y flexible."""
    
    all_chunks.append({
        "id": "schema_description",
        "text": schema_description,
        "metadata": {
            "source_file": "schema.puml",
            "chunk_type": "schema_description",
            "tables": ",".join(TARGET_SCHEMA['tables']),
            "num_tables": len(TARGET_SCHEMA['tables']),
            "char_length": len(schema_description),
            "schema_type": "target"
        }
    })
    
    # Chunks individuales por tabla del esquema objetivo
    for table_name, create_sql in schema_statements.items():
        all_chunks.append({
            "id": f"target_schema_{table_name}",
            "text": create_sql,
            "metadata": {
                "source_file": "schema.puml",
                "chunk_type": "target_table",
                "tables": table_name,
                "num_tables": 1,
                "char_length": len(create_sql),
                "schema_type": "target"
            }
        })
        
        # Añadir descripción enriquecida de cada tabla
        table_descriptions = {
            "users": "Tabla de usuarios: Almacena credenciales (username, password), datos de contacto (email), claves de activación/reset, y estado de activación.",
            "systems": "Tabla de sistemas: Define las aplicaciones en la plataforma con nombre, descripción y repositorio.",
            "roles": "Tabla de roles: Define roles por sistema (ej: admin, editor, viewer) con relación a systems.",
            "permissions": "Tabla de permisos: Define permisos específicos asociados a roles (ej: create, read, update, delete).",
            "systems_users": "Tabla de relación: Conecta usuarios con sistemas (qué usuario tiene acceso a qué sistema).",
            "systems_users_permissions": "Tabla de permisos especiales: Permite asignar permisos específicos a un usuario en un sistema."
        }
        
        if table_name in table_descriptions:
            enhanced_text = f"{table_descriptions[table_name]}\n\n{create_sql}"
            all_chunks.append({
                "id": f"target_schema_{table_name}_enhanced",
                "text": enhanced_text,
                "metadata": {
                    "source_file": "schema.puml",
                    "chunk_type": "target_table_enhanced",
                    "tables": table_name,
                    "num_tables": 1,
                    "char_length": len(enhanced_text),
                    "schema_type": "target"
                }
            })
    
    # Chunk de relaciones
    relationships_text = """Relaciones del esquema de usuarios, sistemas, roles y permisos:

1. users (1) ---- (N) systems_users: Un usuario puede tener acceso a múltiples sistemas
2. systems (1) ---- (N) systems_users: Un sistema puede tener múltiples usuarios
3. systems (1) ---- (N) roles: Un sistema puede tener múltiples roles
4. roles (1) ---- (N) permissions: Un rol puede tener múltiples permisos
5. systems_users_permissions: Permisos especiales por usuario y sistema
   - Referencia system_id → systems(id)
   - Referencia user_id → users(id)  
   - Referencia permission_id → permissions(id)

Consultas típicas:
- Obtener todos los sistemas de un usuario: JOIN users, systems_users, systems
- Obtener roles de un sistema: SELECT * FROM roles WHERE system_id = X
- Obtener permisos de un rol: SELECT * FROM permissions WHERE role_id = Y
- Verificar permiso especial: SELECT * FROM systems_users_permissions WHERE user_id = X AND system_id = Y AND permission_id = Z"""
    
    all_chunks.append({
        "id": "target_schema_relationships",
        "text": relationships_text,
        "metadata": {
            "source_file": "schema.puml",
            "chunk_type": "relationships",
            "tables": ",".join(TARGET_SCHEMA['tables']),
            "num_tables": len(TARGET_SCHEMA['tables']),
            "char_length": len(relationships_text),
            "schema_type": "target"
        }
    })
    
    return all_chunks


# =========================================================
# BASE DE DATOS MYSQL
# =========================================================

def init_mysql_database():
    """Inicializa MySQL con tabla para embeddings"""
    
    try:
        # Conectar sin base de datos específica para crearla
        conn = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            port=MYSQL_CONFIG['port'],
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # Crear base de datos si no existe
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']} "
                      f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        conn.close()
        
        # Conectar a la base de datos específica
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # Crear tabla de chunks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id VARCHAR(255) PRIMARY KEY,
                text LONGTEXT NOT NULL,
                chunk_type VARCHAR(50),
                source_file VARCHAR(255),
                tables TEXT,
                num_tables INT,
                char_length INT,
                relationship VARCHAR(255),
                schema_type VARCHAR(20),
                embedding JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_chunk_type (chunk_type),
                INDEX idx_source_file (source_file),
                INDEX idx_schema_type (schema_type),
                FULLTEXT INDEX idx_text_fulltext (text),
                INDEX idx_tables (tables(255))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Base de datos MySQL inicializada correctamente")
        return True
        
    except Error as e:
        print(f"❌ Error inicializando MySQL: {e}")
        return False


def add_chunks_to_mysql(chunks: List[Dict], model: SentenceTransformer):
    """Agrega chunks a MySQL con sus embeddings"""
    
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            # Generar embedding
            text = chunk["text"]
            embedding = model.encode(text).tolist()
            
            # Convertir embedding a JSON string
            embedding_json = json.dumps(embedding)
            
            metadata = chunk["metadata"]
            
            cursor.execute("""
                INSERT INTO chunks 
                (id, text, chunk_type, source_file, tables, num_tables, 
                 char_length, relationship, schema_type, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                text = VALUES(text),
                embedding = VALUES(embedding)
            """, (
                chunk["id"],
                text,
                metadata.get("chunk_type", "unknown"),
                metadata.get("source_file", ""),
                metadata.get("tables", ""),
                metadata.get("num_tables", 0),
                metadata.get("char_length", len(text)),
                metadata.get("relationship", ""),
                metadata.get("schema_type", "unknown"),
                embedding_json
            ))
            
            if (i + 1) % 20 == 0:
                conn.commit()
                print(f"   Progreso: {i + 1}/{total} chunks")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"   ✅ {total} chunks insertados en MySQL")
        
    except Error as e:
        print(f"❌ Error insertando chunks: {e}")


def cosine_similarity_mysql(embedding1: List[float], embedding2_json: str) -> float:
    """Calcula similitud coseno entre dos vectores"""
    try:
        embedding2 = json.loads(embedding2_json)
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    except:
        return 0.0


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def index_all_migrations():
    """Indexa todas las migraciones en MySQL"""
    
    print("=" * 70)
    print("🚀 REINDEXACIÓN CON MYSQL PARA ESQUEMA DE USUARIOS/SISTEMAS/ROLES")
    print("=" * 70)
    
    # Verificar directorio
    if not os.path.exists(MIGRATIONS_PATH):
        print(f"❌ ERROR: {MIGRATIONS_PATH} no existe")
        print("   Creando directorio...")
        os.makedirs(MIGRATIONS_PATH, exist_ok=True)
    
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
    schema_types = {}
    for chunk in all_chunks:
        ctype = chunk["metadata"]["chunk_type"]
        chunk_types[ctype] = chunk_types.get(ctype, 0) + 1
        stype = chunk["metadata"].get("schema_type", "unknown")
        schema_types[stype] = schema_types.get(stype, 0) + 1
    
    print(f"\n   Tipos de chunks:")
    for ctype, count in sorted(chunk_types.items()):
        print(f"      - {ctype}: {count}")
    
    print(f"\n   Por tipo de esquema:")
    for stype, count in sorted(schema_types.items()):
        print(f"      - {stype}: {count}")
    
    # Inicializar MySQL
    print(f"\n💾 Inicializando MySQL...")
    if not init_mysql_database():
        print("❌ No se pudo inicializar la base de datos")
        return False
    
    # Limpiar tabla existente
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chunks")
        conn.commit()
        cursor.close()
        conn.close()
        print("   Tabla limpiada")
    except Error as e:
        print(f"   ⚠️ Error limpiando tabla: {e}")
    
    # Insertar chunks
    print(f"\n💾 Insertando chunks con embeddings...")
    add_chunks_to_mysql(all_chunks, model)
    
    # Verificar
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
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
    for table in TARGET_SCHEMA['tables']:
        try:
            conn = pymysql.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE tables LIKE %s", (f'%{table}%',))
            found = cursor.fetchone()[0]
            if found > 0:
                print(f"   ✅ {table}: encontrado ({found} chunks)")
            else:
                print(f"   ❌ {table}: NO encontrado")
            cursor.close()
            conn.close()
        except Error as e:
            print(f"   Error verificando {table}: {e}")
    
    print("\n" + "=" * 70)
    print("✅ REINDEXACIÓN COMPLETADA")
    print("=" * 70)
    print("\n💡 Ahora ejecute: python3 test_end_2_end_mysql_schema.py")
    
    return True


def quick_check():
    """Verificación rápida del estado MySQL"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks")
        count = cursor.fetchone()[0]
        print(f"\n✅ Base MySQL existe con {count} chunks")
        
        if count > 0:
            print("\n📋 Muestra de chunks:")
            cursor.execute("SELECT id, chunk_type, tables, schema_type FROM chunks LIMIT 5")
            rows = cursor.fetchall()
            for i, (chunk_id, chunk_type, tables, schema_type) in enumerate(rows):
                print(f"   {i+1}. {chunk_id}")
                print(f"      Tipo: {chunk_type} | Esquema: {schema_type}")
                print(f"      Tablas: {tables[:50]}..." if tables and len(tables) > 50 else f"      Tablas: {tables}")
        
        cursor.close()
        conn.close()
        return count
    except Error as e:
        print(f"\n❌ Error: {e}")
        return 0


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🔄 SISTEMA DE INDEXACIÓN CON MYSQL - ESQUEMA USUARIOS/SISTEMAS/ROLES")
    print("=" * 70)
    
    print(f"\n📂 Migraciones: {MIGRATIONS_PATH}")
    print(f"💾 MySQL DB: {MYSQL_CONFIG['database']} en {MYSQL_CONFIG['host']}")
    
    print(f"\n📋 Tablas objetivo:")
    for table in TARGET_SCHEMA['tables']:
        print(f"   - {table}")
    
    # Verificar PyMySQL
    try:
        import pymysql
        print(f"\n✅ PyMySQL versión: {pymysql.__version__}")
    except ImportError:
        print("❌ PyMySQL no está instalado. Ejecute: pip install pymysql")
        exit(1)
    
    # Verificar estado actual
    print("\n🔍 Estado antes de reindexar:")
    current_count = quick_check()
    
    print(f"\n📊 Chunks actuales: {current_count}")
    
    response = input(f"\n¿Reindexar con MySQL para el nuevo esquema? (s/n): ")
    
    if response.lower() == 's':
        success = index_all_migrations()
        if success:
            print("\n" + "=" * 70)
            print("🎉 ¡REINDEXACIÓN COMPLETADA EXITOSAMENTE!")
            print("=" * 70)
            print("\n📊 Comparación:")
            print(f"   Chunks antes: {current_count}")
            print(f"   Chunks ahora: {quick_check()}")
            print("\n💡 Ejecute: python3 test_end_2_end_mysql_schema.py")
        else:
            print("\n❌ Falló la reindexación")
    else:
        print("\n❌ Reindexación cancelada")