# =========================================================
# reindex_chromadb.py - Script para reindexar correctamente
# =========================================================

import os
import re
import glob
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions

# =========================================================
# CONFIGURACIÓN - RUTAS CORREGIDAS
# =========================================================

# IMPORTANTE: El script se ejecuta desde el directorio actual
# que contiene la carpeta 'migrations'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# La carpeta migrations está en el mismo directorio que este script
MIGRATIONS_PATH = os.path.join(CURRENT_DIR, "migrations")

# ChromaDB está en el directorio padre (herramienta/chroma_db)
BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
CHROMA_PATH = os.path.join(BASE_PATH, "chroma_db")

# Nombre de la colección
COLLECTION_NAME = "migrations"

# Configuración de chunking
CHUNK_SIZE = 800  # caracteres por chunk (aumentado para SQL)
CHUNK_OVERLAP = 100  # superposición entre chunks

print(f"📂 Directorio actual: {CURRENT_DIR}")
print(f"📁 Migraciones: {MIGRATIONS_PATH}")
print(f"💾 ChromaDB: {CHROMA_PATH}")

# =========================================================
# FUNCIONES DE PROCESAMIENTO
# =========================================================

def find_sql_files(migrations_path: str) -> List[str]:
    """Encuentra todos los archivos SQL en el directorio de migraciones"""
    sql_files = []
    
    if not os.path.exists(migrations_path):
        print(f"❌ ERROR: No existe {migrations_path}")
        return []
    
    # Buscar archivos .sql
    pattern = os.path.join(migrations_path, "*.sql")
    sql_files.extend(glob.glob(pattern))
    
    print(f"   Archivos .sql encontrados: {len(sql_files)}")
    
    return sorted(sql_files)


def read_sql_file(filepath: str) -> str:
    """Lee el contenido de un archivo SQL"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Intentar con latin-1 si UTF-8 falla
        with open(filepath, 'r', encoding='latin-1') as f:
            return f.read()


def extract_table_names(sql_content: str) -> List[str]:
    """Extrae nombres de tablas del contenido SQL"""
    tables = set()
    
    # Patrones para encontrar CREATE TABLE
    patterns = [
        r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?(\w+)["`]?',
        r'CREATE\s+TABLE\s+["`]?(\w+)["`]?',
        r'ALTER\s+TABLE\s+["`]?(\w+)["`]?',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, sql_content, re.IGNORECASE)
        for match in matches:
            table_name = match.strip('"\'`[]').lower()
            if table_name and not table_name.startswith('temp_') and len(table_name) > 2:
                tables.add(table_name)
    
    # También buscar en comentarios de migración
    # Formato: -- migrate:up / -- migrate:down no tienen tablas
    
    return list(tables)


def chunk_sql_content(content: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    """
    Divide el contenido SQL en chunks más pequeños.
    Mantiene las sentencias SQL completas cuando es posible.
    """
    chunks = []
    
    # Primero, dividir por sentencias (terminadas con ;)
    statements = []
    current_statement = []
    
    lines = content.split('\n')
    for line in lines:
        current_statement.append(line)
        if ';' in line and not line.strip().startswith('--'):
            statements.append('\n'.join(current_statement))
            current_statement = []
    
    if current_statement:
        statements.append('\n'.join(current_statement))
    
    # Combinar sentencias en chunks del tamaño adecuado
    current_chunk = ""
    
    for stmt in statements:
        # Si el chunk actual + la nueva sentencia excede el tamaño
        if len(current_chunk) + len(stmt) > chunk_size and current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "type": "combined"
            })
            # Mantener overlap
            if overlap > 0:
                # Guardar las últimas líneas para overlap
                overlap_text = '\n'.join(current_chunk.split('\n')[-5:])
                current_chunk = overlap_text + "\n"
        
        current_chunk += stmt + "\n"
    
    # Último chunk
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "type": "combined"
        })
    
    # Si no hay chunks (archivo muy pequeño), crear uno solo
    if not chunks and content.strip():
        chunks.append({
            "text": content.strip(),
            "type": "single"
        })
    
    return chunks


def get_chunk_metadata(content: str, filename: str, chunk_index: int) -> Dict[str, Any]:
    """Genera metadata para un chunk"""
    tables = extract_table_names(content)
    
    # Detectar tipo de operación
    content_upper = content.upper()
    operation_type = "unknown"
    
    if "CREATE TABLE" in content_upper:
        operation_type = "create"
    elif "ALTER TABLE" in content_upper:
        operation_type = "alter"
    elif "DROP TABLE" in content_upper:
        operation_type = "drop"
    elif "INSERT INTO" in content_upper:
        operation_type = "insert"
    elif "CREATE INDEX" in content_upper:
        operation_type = "index"
    
    return {
        "source_file": filename,
        "chunk_index": chunk_index,
        "tables": ",".join(tables),
        "operation_type": operation_type,
        "num_tables": len(tables),
        "char_length": len(content)
    }


def index_all_migrations():
    """Indexa todas las migraciones en ChromaDB"""
    
    print("="*70)
    print("🔄 REINDEXANDO MIGRACIONES EN CHROMA DB")
    print("="*70)
    
    # 1. Verificar directorio de migraciones
    if not os.path.exists(MIGRATIONS_PATH):
        print(f"❌ ERROR: Directorio de migraciones no encontrado: {MIGRATIONS_PATH}")
        return False
    
    # 2. Encontrar archivos SQL
    sql_files = find_sql_files(MIGRATIONS_PATH)
    print(f"\n📁 Encontrados {len(sql_files)} archivos SQL")
    
    if not sql_files:
        print("❌ No se encontraron archivos SQL en:", MIGRATIONS_PATH)
        # Listar contenido del directorio
        print(f"\nContenido de {MIGRATIONS_PATH}:")
        for item in os.listdir(MIGRATIONS_PATH):
            print(f"   - {item}")
        return False
    
    # Mostrar archivos encontrados
    print("\n📄 Archivos encontrados:")
    for f in sql_files:
        print(f"   - {os.path.basename(f)}")
    
    # 3. Crear/obtener colección ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # Eliminar colección existente para reindexar desde cero
    try:
        client.delete_collection(COLLECTION_NAME)
        print("\n🗑️ Colección existente eliminada")
    except Exception as e:
        print(f"\n⚠️ No se pudo eliminar colección (puede no existir): {e}")
    
    # Crear nueva colección
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn
    )
    print(f"✅ Nueva colección '{COLLECTION_NAME}' creada")
    
    # 4. Procesar cada archivo
    all_chunks = []
    total_tables_found = set()
    
    for filepath in sql_files:
        filename = os.path.basename(filepath)
        print(f"\n📖 Procesando: {filename}")
        
        content = read_sql_file(filepath)
        tables_in_file = extract_table_names(content)
        print(f"   → Tablas encontradas: {tables_in_file}")
        
        for table in tables_in_file:
            total_tables_found.add(table)
        
        # Dividir en chunks
        chunks = chunk_sql_content(content)
        print(f"   → {len(chunks)} chunks generados")
        
        for i, chunk in enumerate(chunks):
            metadata = get_chunk_metadata(chunk["text"], filename, i)
            chunk_id = f"{filename}_chunk_{i}"
            all_chunks.append({
                "id": chunk_id,
                "text": chunk["text"],
                "metadata": metadata
            })
    
    print(f"\n📦 Total de chunks generados: {len(all_chunks)}")
    
    # 5. Indexar en ChromaDB
    print(f"\n💾 Indexando en ChromaDB...")
    
    BATCH_SIZE = 100
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i+BATCH_SIZE]
        
        collection.add(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["text"] for chunk in batch],
            metadatas=[chunk["metadata"] for chunk in batch]
        )
        print(f"   → Lote {i//BATCH_SIZE + 1}: {len(batch)} chunks indexados")
    
    # 6. Verificar resultado
    final_count = collection.count()
    
    print("\n" + "="*70)
    print("📊 RESULTADO DE LA INDEXACIÓN")
    print("="*70)
    print(f"\n✅ Total de chunks indexados: {final_count}")
    
    print(f"\n📋 Tablas encontradas ({len(total_tables_found)}):")
    for table in sorted(total_tables_found):
        print(f"   - {table}")
    
    return True


def verify_migrations_folder():
    """Verifica el contenido de la carpeta de migraciones"""
    print("\n" + "="*70)
    print("🔍 VERIFICANDO CARPETA DE MIGRACIONES")
    print("="*70)
    
    if not os.path.exists(MIGRATIONS_PATH):
        print(f"❌ Carpeta no existe: {MIGRATIONS_PATH}")
        print(f"   Directorio actual: {CURRENT_DIR}")
        print(f"   Contenido del directorio actual:")
        for item in os.listdir(CURRENT_DIR):
            print(f"     - {item}")
        return None, None
    
    print(f"✅ Carpeta existe: {MIGRATIONS_PATH}")
    
    # Listar archivos
    sql_files = find_sql_files(MIGRATIONS_PATH)
    
    print(f"\n📄 Total de archivos SQL: {len(sql_files)}")
    
    if not sql_files:
        print("⚠️ No hay archivos .sql en la carpeta")
        print(f"\nContenido de {MIGRATIONS_PATH}:")
        for item in os.listdir(MIGRATIONS_PATH):
            print(f"   - {item}")
        return [], {}
    
    for f in sql_files:
        print(f"   - {os.path.basename(f)}")
    
    # Buscar tablas específicas
    target_tables = {
        'authors': False,
        'reviews': False,
        'publishers': False,
        'countries': False,
        'devices': False,
        'users': False,
        'books': False,
        'genres': False,
        'books_genres': False,
        'books_authors': False
    }
    
    print("\n🔎 Buscando tablas específicas en archivos:")
    for filepath in sql_files:
        filename = os.path.basename(filepath)
        content = read_sql_file(filepath).lower()
        
        for table in list(target_tables.keys()):
            if not target_tables[table]:
                # Buscar CREATE TABLE exacto
                if re.search(rf'create\s+table\s+["`]?{re.escape(table)}["`]?', content):
                    target_tables[table] = True
                    print(f"   ✅ {table} encontrado en {filename}")
                elif re.search(rf'create\s+table\s+{re.escape(table)}\b', content):
                    target_tables[table] = True
                    print(f"   ✅ {table} encontrado en {filename}")
    
    # Mostrar las que no se encontraron
    missing = [t for t, found in target_tables.items() if not found]
    if missing:
        print(f"\n⚠️ TABLAS NO ENCONTRADAS: {missing}")
    else:
        print(f"\n✅ Todas las tablas esperadas fueron encontradas")
    
    return sql_files, target_tables


def quick_check():
    """Verificación rápida sin reindexar"""
    print("\n" + "="*70)
    print("🔍 VERIFICACIÓN RÁPIDA DE CHROMA DB")
    print("="*70)
    
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(COLLECTION_NAME)
        count = collection.count()
        print(f"\n✅ Colección '{COLLECTION_NAME}' existe con {count} chunks")
        
        # Obtener algunos documentos para inspeccionar
        all_docs = collection.get(limit=5)
        if all_docs and all_docs['documents']:
            print("\n📄 Ejemplo de chunks en ChromaDB:")
            for i, doc in enumerate(all_docs['documents'][:3]):
                print(f"\n--- Chunk {i+1} ---")
                print(doc[:300] + "..." if len(doc) > 300 else doc)
        
        return count
    except Exception as e:
        print(f"\n❌ Error al acceder a ChromaDB: {e}")
        return 0


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    
    print("\n" + "="*70)
    print("🔄 SCRIPT DE REINDEXACIÓN DE MIGRACIONES")
    print("="*70)
    
    # Mostrar rutas
    print(f"\n📂 Directorio actual: {CURRENT_DIR}")
    print(f"📁 Ruta migraciones: {MIGRATIONS_PATH}")
    print(f"💾 Ruta ChromaDB: {CHROMA_PATH}")
    
    # 1. Verificar estado actual de ChromaDB
    current_count = quick_check()
    
    # 2. Verificar la carpeta de migraciones
    files, found_tables = verify_migrations_folder()
    
    if not files:
        print("\n❌ No se encontraron archivos SQL. Verifique la carpeta 'migrations'")
        exit(1)
    
    # 3. Preguntar si quiere reindexar
    print("\n" + "="*70)
    response = input(f"\n¿Desea reindexar todas las migraciones en ChromaDB? (s/n): ")
    
    if response.lower() == 's':
        success = index_all_migrations()
        if success:
            print("\n✅ Reindexación completada exitosamente")
            # Verificar resultado
            new_count = quick_check()
            print(f"\n📊 Chunks antes: {current_count}, después: {new_count}")
        else:
            print("\n❌ Falló la reindexación")
    else:
        print("\n❌ Reindexación cancelada")
    
    print("\n✅ Script completado")