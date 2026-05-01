# ingest.py - Versión mejorada para PostgreSQL con embeddings de alta calidad

import os
import re
import glob
import json
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions

# =========================================================
# CONFIGURACIÓN
# =========================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATIONS_PATH = os.path.join(CURRENT_DIR, "migrations")
BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
CHROMA_PATH = os.path.join(BASE_PATH, "chroma_db")
COLLECTION_NAME = "migrations"

# Configuración de chunking mejorada
CHUNK_SIZE = 1000  # Aumentado para capturar sentencias completas
CHUNK_OVERLAP = 200

# =========================================================
# FUNCIONES DE PROCESAMIENTO
# =========================================================

def find_sql_files(migrations_path: str) -> List[str]:
    """Encuentra todos los archivos SQL"""
    sql_files = []
    
    if not os.path.exists(migrations_path):
        print(f"❌ ERROR: No existe {migrations_path}")
        return []
    
    # Buscar .sql y también archivos sin extensión que contengan SQL
    pattern = os.path.join(migrations_path, "*.sql")
    sql_files.extend(glob.glob(pattern))
    
    # También buscar archivos que parezcan migraciones (sin extensión)
    for file in glob.glob(os.path.join(migrations_path, "*")):
        if os.path.isfile(file) and not file.endswith('.sql'):
            # Verificar si parece un archivo SQL
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
    """Extrae nombres de tablas del contenido SQL (PostgreSQL)"""
    tables = set()
    
    # Eliminar comentarios SQL
    lines = sql_content.split('\n')
    clean_lines = []
    for line in lines:
        if '--' in line:
            line_without_comments = line.split('--')[0]
            clean_lines.append(line_without_comments)
        else:
            clean_lines.append(line)
    
    sql_clean = '\n'.join(clean_lines)
    
    # Patrones para CREATE TABLE (PostgreSQL)
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
    
    # Patrón para FOREIGN KEY en PostgreSQL
    fk_pattern = r'FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+([a-z_]+)\s*\(([^)]+)\)'
    matches = re.finditer(fk_pattern, sql_content, re.IGNORECASE)
    
    for match in matches:
        fks.append({
            'columns': match.group(1).strip(),
            'referenced_table': match.group(2).strip().lower(),
            'referenced_columns': match.group(3).strip()
        })
    
    # También buscar en ALTER TABLE ADD CONSTRAINT
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
        
        # ===== 1. Chunk completo del archivo =====
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
        
        # ===== 2. Chunks por sentencia CREATE TABLE =====
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
        
        # ===== 3. Chunks por FOREIGN KEY (con contexto ampliado) =====
        for i, fk in enumerate(fks):
            # Buscar contexto alrededor de la FK
            fk_context = ""
            ref_table = fk.get('referenced_table', '')
            
            # Buscar en el contenido sentencias que mencionen esta relación
            lines = content.split('\n')
            for j, line in enumerate(lines):
                if 'FOREIGN KEY' in line.upper() and ref_table in line.lower():
                    # Tomar contexto: 3 líneas antes y después
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
        
        # ===== 4. NUEVO: Chunks enfocados por nombre de tabla =====
        for table in tables:
            # Buscar todo el bloque CREATE TABLE de esa tabla
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
        
        # ===== 5. NUEVO: Chunks de resumen para búsqueda semántica =====
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


def index_all_migrations():
    """Indexa todas las migraciones con chunking mejorado y mejores embeddings"""
    
    print("=" * 70)
    print("🚀 REINDEXACIÓN CON CHUNKING MEJORADO PARA POSTGRESQL")
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
    
    # Generar chunks mejorados
    print("\n📦 Generando chunks mejorados...")
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
    
    # Conectar a ChromaDB
    try:
        os.makedirs(CHROMA_PATH, exist_ok=True)
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        
        # Eliminar colección existente
        try:
            client.delete_collection(COLLECTION_NAME)
            print("\n🗑️ Colección existente eliminada")
        except:
            pass
        
        # Usar embedding de sentence-transformers (mucho mejor que default)
        print("\n🔧 Configurando embedding model: all-MiniLM-L6-v2")
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Crear nueva colección
        collection = client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn
        )
        print("✅ Colección creada con embeddings mejorados")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Indexar en lotes
    print(f"\n💾 Indexando {len(all_chunks)} chunks...")
    
    BATCH_SIZE = 50
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i + BATCH_SIZE]
        try:
            collection.add(
                ids=[chunk["id"] for chunk in batch],
                documents=[chunk["text"] for chunk in batch],
                metadatas=[chunk["metadata"] for chunk in batch]
            )
            print(f"   ✅ Lote {i // BATCH_SIZE + 1}: {len(batch)} chunks")
        except Exception as e:
            print(f"   ❌ Error en lote: {e}")
            return False
    
    final_count = collection.count()
    
    print("\n" + "=" * 70)
    print("📊 RESULTADO FINAL")
    print("=" * 70)
    print(f"\n✅ Total de chunks indexados: {final_count}")
    
    # Verificar tablas específicas
    print("\n🔍 VERIFICANDO TABLAS CRÍTICAS:")
    critical_tables = ['users', 'books', 'books_genres', 'reviews', 'books_authors', 'authors']
    
    for table in critical_tables:
        results = collection.query(
            query_texts=[f"CREATE TABLE {table}"],
            n_results=1
        )
        if results['documents'][0]:
            print(f"   ✅ {table}: encontrado")
        else:
            print(f"   ❌ {table}: NO encontrado")
    
    print("\n" + "=" * 70)
    print("✅ REINDEXACIÓN COMPLETADA")
    print("=" * 70)
    print("\n💡 Ahora ejecute: python3 test_end_2_end.py")
    
    return True


def quick_check():
    """Verificación rápida del estado"""
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(COLLECTION_NAME)
        count = collection.count()
        print(f"\n✅ Colección '{COLLECTION_NAME}' existe con {count} chunks")
        
        if count > 0:
            print("\n📋 Muestra de chunks:")
            sample = collection.get(limit=3)
            for i, (chunk_id, metadata) in enumerate(zip(sample['ids'], sample['metadatas'])):
                print(f"   {i+1}. {chunk_id}")
                print(f"      Tipo: {metadata.get('chunk_type', 'N/A')}")
                print(f"      Tablas: {metadata.get('tables', 'N/A')}")
        
        return count
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 0


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🔄 SISTEMA DE INDEXACIÓN PARA POSTGRESQL")
    print("=" * 70)
    
    print(f"\n📂 Migraciones: {MIGRATIONS_PATH}")
    print(f"💾 ChromaDB: {CHROMA_PATH}")
    
    # Verificar estado actual
    print("\n🔍 Estado antes de reindexar:")
    current_count = quick_check()
    
    print(f"\n📊 Chunks actuales: {current_count}")
    
    response = input(f"\n¿Reindexar con chunking mejorado y mejores embeddings? (s/n): ")
    
    if response.lower() == 's':
        success = index_all_migrations()
        if success:
            print("\n" + "=" * 70)
            print("🎉 ¡REINDEXACIÓN COMPLETADA EXITOSAMENTE!")
            print("=" * 70)
            print("\n📊 Comparación:")
            print(f"   Chunks antes: {current_count}")
            print(f"   Chunks ahora: {quick_check()}")
            print("\n💡 Ejecute: python3 test_end_2_end.py")
        else:
            print("\n❌ Falló la reindexación")
    else:
        print("\n❌ Reindexación cancelada")