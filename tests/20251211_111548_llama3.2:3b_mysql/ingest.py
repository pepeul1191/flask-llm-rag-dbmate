# ingest.py - Versión para MySQL con PyMySQL

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
    'password': '123',  # Cambiar por tu contraseña
    'database': 'rag_system',
    'port': 3306,
    'charset': 'utf8mb4',
    'autocommit': False
}

# Configuración de chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Modelo de embeddings
MODEL_NAME = "all-MiniLM-L6-v2"


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


def generate_enhanced_chunks(sql_files: List[str]) -> List[Dict[str, Any]]:
    """Genera chunks mejorados con múltiples estrategias"""
    all_chunks = []
    
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
        
        # 3. Chunks por FOREIGN KEY
        for i, fk in enumerate(fks):
            fk_context = ""
            ref_table = fk.get('referenced_table', '')
            
            lines = content.split('\n')
            for j, line in enumerate(lines):
                if 'FOREIGN KEY' in line.upper() and ref_table in line.lower():
                    start = max(0, j - 3)
                    end = min(len(lines), j + 4)
                    fk_context = '\n'.join(lines[start:end])
                    break
            
            if fk_context:
                all_chunks.append({
                    "id": f"{filename}_fk_{i}",
                    "text": fk_context,
                    "metadata": {
                        "source_file": filename,
                        "chunk_type": "foreign_key",
                        "tables": ref_table,
                        "relationship": f"references_{ref_table}",
                        "char_length": len(fk_context)
                    }
                })
        
        # 4. Chunks por tabla
        for table in tables:
            table_pattern = rf'(CREATE\s+TABLE\s+{re.escape(table)}[^;]+;)'
            table_match = re.search(table_pattern, content, re.IGNORECASE | re.DOTALL)
            
            if table_match:
                table_content = table_match.group(1)
                all_chunks.append({
                    "id": f"{filename}_table_{table}",
                    "text": f"Tabla {table}:\n{table_content}",
                    "metadata": {
                        "source_file": filename,
                        "chunk_type": "table_focused",
                        "tables": table,
                        "char_length": len(table_content)
                    }
                })
        
        # 5. Chunks de resumen
        summary = f"""Archivo de migración: {filename}
Tablas contenidas: {', '.join(tables)}
Relaciones (Foreign Keys): {len(fks)}
Contenido resumido: {content[:500]}..."""
        
        all_chunks.append({
            "id": f"{filename}_summary",
            "text": summary,
            "metadata": {
                "source_file": filename,
                "chunk_type": "summary",
                "tables": ",".join(tables),
                "num_tables": len(tables)
            }
        })
    
    return all_chunks


# =========================================================
# BASE DE DATOS MYSQL
# =========================================================

def init_mysql_database():
    """Inicializa MySQL con tabla para embeddings usando PyMySQL"""
    
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
                embedding JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_chunk_type (chunk_type),
                INDEX idx_source_file (source_file),
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
        print("\n💡 Soluciones:")
        print("   1. Verifica que MySQL esté corriendo: sudo systemctl status mysql")
        print("   2. Cambia el plugin de autenticación del usuario:")
        print("      ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'tu_password';")
        print("   3. O usa: pip install pymysql (ya lo estamos usando)")
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
                 char_length, relationship, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                embedding_json
            ))
            
            if (i + 1) % 50 == 0:
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
    embedding2 = json.loads(embedding2_json)
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def search_similar_chunks_mysql(query_text: str, model: SentenceTransformer, k: int = 5) -> List[tuple]:
    """Busca chunks similares usando MySQL"""
    
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Generar embedding de la query
        query_embedding = model.encode(query_text).tolist()
        
        # Obtener todos los chunks
        cursor.execute("SELECT id, text, embedding, chunk_type, source_file, tables FROM chunks")
        rows = cursor.fetchall()
        
        # Calcular similitud con cada chunk
        similarities = []
        for row in rows:
            similarity = cosine_similarity_mysql(query_embedding, row['embedding'])
            similarities.append((similarity, row['id'], row['text'], 
                               row['chunk_type'], row['source_file'], row['tables']))
        
        # Ordenar por similitud descendente
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        cursor.close()
        conn.close()
        
        # Retornar top k
        return [(chunk_id, chunk_text, similarity) 
                for similarity, chunk_id, chunk_text, _, _, _ in similarities[:k]]
        
    except Error as e:
        print(f"❌ Error buscando chunks: {e}")
        return []


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def index_all_migrations():
    """Indexa todas las migraciones en MySQL"""
    
    print("=" * 70)
    print("🚀 REINDEXACIÓN CON MYSQL Y EMBEDDINGS")
    print("=" * 70)
    
    # Verificar directorio
    if not os.path.exists(MIGRATIONS_PATH):
        print(f"❌ ERROR: {MIGRATIONS_PATH} no existe")
        return False
    
    # Encontrar archivos
    sql_files = find_sql_files(MIGRATIONS_PATH)
    print(f"\n📁 Archivos encontrados: {len(sql_files)}")
    for f in sql_files:
        print(f"   - {os.path.basename(f)}")
    
    if not sql_files:
        print("❌ No hay archivos SQL")
        return False
    
    # Cargar modelo de embeddings
    print(f"\n🔧 Cargando modelo: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("✅ Modelo cargado")
    
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
    print("\n🔍 VERIFICANDO TABLAS CRÍTICAS:")
    critical_tables = ['users', 'books', 'books_genres', 'reviews', 'books_authors', 'authors']
    
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        for table in critical_tables:
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE tables LIKE %s", (f'%{table}%',))
            found = cursor.fetchone()[0]
            if found > 0:
                print(f"   ✅ {table}: encontrado ({found} chunks)")
            else:
                print(f"   ❌ {table}: NO encontrado")
        
        cursor.close()
        conn.close()
    except Error as e:
        print(f"   Error verificando: {e}")
    
    print("\n" + "=" * 70)
    print("✅ REINDEXACIÓN COMPLETADA")
    print("=" * 70)
    print("\n💡 Ahora ejecute: python3 test_end_2_end_mysql.py")
    
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
            cursor.execute("SELECT id, chunk_type, tables FROM chunks LIMIT 3")
            rows = cursor.fetchall()
            for i, (chunk_id, chunk_type, tables) in enumerate(rows):
                print(f"   {i+1}. {chunk_id}")
                print(f"      Tipo: {chunk_type}")
                print(f"      Tablas: {tables}")
        
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
    print("🔄 SISTEMA DE INDEXACIÓN CON MYSQL")
    print("=" * 70)
    
    print(f"\n📂 Migraciones: {MIGRATIONS_PATH}")
    print(f"💾 MySQL DB: {MYSQL_CONFIG['database']} en {MYSQL_CONFIG['host']}")
    
    # Verificar PyMySQL
    try:
        import pymysql
        print(f"✅ PyMySQL versión: {pymysql.__version__}")
    except ImportError:
        print("❌ PyMySQL no está instalado. Ejecute: pip install pymysql")
        exit(1)
    
    # Verificar estado actual
    print("\n🔍 Estado antes de reindexar:")
    current_count = quick_check()
    
    print(f"\n📊 Chunks actuales: {current_count}")
    
    response = input(f"\n¿Reindexar con MySQL? (s/n): ")
    
    if response.lower() == 's':
        success = index_all_migrations()
        if success:
            print("\n" + "=" * 70)
            print("🎉 ¡REINDEXACIÓN COMPLETADA EXITOSAMENTE!")
            print("=" * 70)
            print("\n📊 Comparación:")
            print(f"   Chunks antes: {current_count}")
            print(f"   Chunks ahora: {quick_check()}")
            print("\n💡 Ejecute: python3 test_end_2_end_mysql.py")
        else:
            print("\n❌ Falló la reindexación")
    else:
        print("\n❌ Reindexación cancelada")