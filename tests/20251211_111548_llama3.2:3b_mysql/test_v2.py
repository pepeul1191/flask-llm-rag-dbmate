# test_v2.py
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

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATIONS_PATH = os.path.join(CURRENT_DIR, "migrations")
BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
CHROMA_PATH = os.path.join(BASE_PATH, "chroma_db")
COLLECTION_NAME = "migrations"

# Configuración de chunking optimizada
CHUNK_SIZE = 1500  # Aumentado para mantener contexto completo
CHUNK_OVERLAP = 200

print(f"📂 Directorio actual: {CURRENT_DIR}")
print(f"📁 Migraciones: {MIGRATIONS_PATH}")
print(f"💾 ChromaDB: {CHROMA_PATH}")

# =========================================================
# FUNCIONES DE PROCESAMIENTO MEJORADAS
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
    
    # Ordenar por nombre
    sql_files.sort()
    
    print(f"   📁 Directorio: {migrations_path}")
    print(f"   🔍 Archivos .sql encontrados: {len(sql_files)}")
    for f in sql_files:
        print(f"      - {os.path.basename(f)}")
    
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
    """Extrae nombres de tablas - VERSIÓN DEFINITIVA MEJORADA"""
    tables = set()
    
    # Eliminar comentarios de línea (-- )
    lines = sql_content.split('\n')
    clean_lines = []
    for line in lines:
        if '--' in line:
            line_without_comments = line.split('--')[0]
            clean_lines.append(line_without_comments)
        else:
            clean_lines.append(line)
    
    sql_clean = '\n'.join(clean_lines)
    
    # Patrones para CREATE TABLE (con y sin backticks)
    patterns = [
        r'CREATE\s+TABLE\s+([a-z_][a-z0-9_]*)',
        r'CREATE\s+TABLE\s+[`"\']([a-z_][a-z0-9_]*)[`"\']',
        r'CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+([a-z_][a-z0-9_]*)',
        r'CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+[`"\']([a-z_][a-z0-9_]*)[`"\']',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, sql_clean, re.IGNORECASE)
        for match in matches:
            table_name = match.lower().strip()
            if table_name and len(table_name) > 2 and not table_name.startswith('temp'):
                tables.add(table_name)
    
    return list(tables)


def chunk_sql_content(content: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    """Divide el contenido SQL manteniendo CREATE TABLEs completos"""
    chunks = []
    
    # Dividir por CREATE TABLE
    creates = re.split(r'(?=CREATE\s+TABLE)', content, flags=re.IGNORECASE)
    
    for create_stmt in creates:
        if 'CREATE TABLE' in create_stmt.upper():
            # Cada CREATE TABLE a su propio chunk
            if len(create_stmt) <= chunk_size * 2:
                chunks.append({
                    "text": create_stmt.strip(),
                    "type": "table_definition"
                })
            else:
                # Si es muy grande, dividir pero mantener contexto
                sub_chunks = []
                current = ""
                for line in create_stmt.split('\n'):
                    if len(current) + len(line) > chunk_size and current:
                        sub_chunks.append(current)
                        # Mantener overlap
                        overlap_lines = current.split('\n')[-3:]
                        current = '\n'.join(overlap_lines) + '\n'
                    current += line + '\n'
                if current:
                    sub_chunks.append(current)
                
                for i, sub in enumerate(sub_chunks):
                    chunks.append({
                        "text": sub.strip(),
                        "type": f"table_definition_part_{i}"
                    })
    
    # Si no hay CREATE TABLEs, comportamiento normal
    if not chunks:
        statements = [s.strip() for s in content.split(';') if s.strip()]
        current_chunk = ""
        for stmt in statements:
            if len(current_chunk) + len(stmt) > chunk_size and current_chunk:
                chunks.append({"text": current_chunk.strip(), "type": "combined"})
                overlap_text = '\n'.join(current_chunk.split('\n')[-5:])
                current_chunk = overlap_text + "\n"
            current_chunk += stmt + ';\n'
        if current_chunk.strip():
            chunks.append({"text": current_chunk.strip(), "type": "combined"})
    
    return chunks if chunks else [{"text": content.strip(), "type": "single"}]


def get_chunk_metadata(content: str, filename: str, chunk_index: int) -> Dict[str, Any]:
    """Genera metadata para un chunk"""
    tables = extract_table_names(content)
    
    content_upper = content.upper()
    operation_type = "unknown"
    
    if "CREATE TABLE" in content_upper:
        operation_type = "create"
    elif "ALTER TABLE" in content_upper:
        operation_type = "alter"
    elif "INSERT INTO" in content_upper:
        operation_type = "insert"
    
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
    
    if not os.path.exists(MIGRATIONS_PATH):
        print(f"❌ ERROR: Directorio de migraciones no encontrado: {MIGRATIONS_PATH}")
        return False
    
    sql_files = find_sql_files(MIGRATIONS_PATH)
    print(f"\n📁 Encontrados {len(sql_files)} archivos SQL TOTALES")
    
    if not sql_files:
        print("❌ No se encontraron archivos SQL")
        return False
    
    # Procesar archivos
    all_chunks = []
    total_tables_found = set()
    
    for idx, filepath in enumerate(sql_files, 1):
        filename = os.path.basename(filepath)
        print(f"\n[{idx}/{len(sql_files)}] 📖 Procesando: {filename}")
        
        content = read_sql_file(filepath)
        tables_in_file = extract_table_names(content)
        print(f"   → Tablas encontradas: {tables_in_file}")
        
        for table in tables_in_file:
            total_tables_found.add(table)
        
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
    print(f"📋 Tablas únicas: {sorted(total_tables_found)}")
    
    # Crear colección ChromaDB
    try:
        os.makedirs(CHROMA_PATH, exist_ok=True)
        print(f"\n💾 Conectando a ChromaDB...")
        
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        
        # Eliminar colección si existe
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"🗑️ Colección existente eliminada")
        except:
            pass
        
        # Crear nueva colección
        embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        collection = client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn
        )
        print(f"✅ Colección '{COLLECTION_NAME}' creada")
        
    except Exception as e:
        print(f"❌ Error al crear colección: {e}")
        return False
    
    # Indexar en lotes
    print(f"\n💾 Indexando {len(all_chunks)} chunks...")
    
    BATCH_SIZE = 100
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i+BATCH_SIZE]
        try:
            collection.add(
                ids=[chunk["id"] for chunk in batch],
                documents=[chunk["text"] for chunk in batch],
                metadatas=[chunk["metadata"] for chunk in batch]
            )
            print(f"   → Lote {i//BATCH_SIZE + 1}: {len(batch)} chunks")
        except Exception as e:
            print(f"   ❌ Error en lote: {e}")
            return False
    
    final_count = collection.count()
    
    print("\n" + "="*70)
    print("📊 RESULTADO DE LA INDEXACIÓN")
    print("="*70)
    print(f"\n✅ Total de chunks indexados: {final_count}")
    print(f"📋 Tablas encontradas ({len(total_tables_found)}):")
    for table in sorted(total_tables_found):
        print(f"   - {table}")
    
    return final_count == len(all_chunks)


def quick_check():
    """Verificación rápida"""
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(COLLECTION_NAME)
        count = collection.count()
        print(f"\n✅ Colección '{COLLECTION_NAME}' existe con {count} chunks")
        return count
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 0


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔄 SCRIPT DE REINDEXACIÓN DE MIGRACIONES")
    print("="*70)
    
    print(f"\n📂 Directorio actual: {CURRENT_DIR}")
    print(f"📁 Ruta migraciones: {MIGRATIONS_PATH}")
    print(f"💾 Ruta ChromaDB: {CHROMA_PATH}")
    
    current_count = quick_check()
    
    response = input(f"\n¿Desea reindexar todas las migraciones? (s/n): ")
    
    if response.lower() == 's':
        success = index_all_migrations()
        if success:
            print("\n✅ Reindexación completada exitosamente")
            new_count = quick_check()
            print(f"\n📊 Chunks antes: {current_count}, después: {new_count}")
        else:
            print("\n❌ Falló la reindexación")
    else:
        print("\n❌ Reindexación cancelada")