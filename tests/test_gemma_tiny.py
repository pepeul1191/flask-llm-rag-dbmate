import os
import logging
import re
import shutil
import datetime
import json
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
MODEL_NAME = "gemma3:1b"
EMBEDDING_MODEL = "nomic-embed-text"
VECTOR_STORE_NAME = "puml-rag"
PERSIST_DIRECTORY = "./chroma_db"

def get_puml_file_hash(puml_path):
    """Calculate a simple hash of the PUML file to detect changes."""
    if os.path.exists(puml_path):
        with open(puml_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return hash(content)
    return None

def should_recreate_vector_db(puml_file, vector_db):
    """Check if vector DB should be recreated based on file changes."""
    if not vector_db:
        return True
    
    # Check if current PUML file is different from stored one
    current_hash = get_puml_file_hash(puml_file)
    
    # Try to get stored hash from vector DB metadata
    try:
        # Get some documents to check metadata
        docs = vector_db.similarity_search("test", k=1)
        if docs and 'source_file_hash' in docs[0].metadata:
            stored_hash = docs[0].metadata.get('source_file_hash')
            return current_hash != stored_hash
    except:
        pass
    
    return True

def clear_vector_db():
    """Safely clear the vector database directory."""
    if os.path.exists(PERSIST_DIRECTORY):
        try:
            # Change permissions if needed
            for root, dirs, files in os.walk(PERSIST_DIRECTORY):
                for dir in dirs:
                    os.chmod(os.path.join(root, dir), 0o755)
                for file in files:
                    os.chmod(os.path.join(root, file), 0o644)
            
            shutil.rmtree(PERSIST_DIRECTORY)
            logging.info("Cleared existing vector database.")
            return True
        except Exception as e:
            logging.error(f"Error clearing vector DB: {e}")
            # Try alternative method
            try:
                import subprocess
                subprocess.run(['rm', '-rf', PERSIST_DIRECTORY], check=True)
                logging.info("Cleared vector database using alternative method.")
                return True
            except:
                logging.error("Failed to clear vector database.")
                return False
    return True

# Check if the vector DB exists
def check_existing_vector_db():
    """Check if vector database already exists"""
    if os.path.exists(PERSIST_DIRECTORY):
        try:
            vector_db = Chroma(
                persist_directory=PERSIST_DIRECTORY,
                embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
                collection_name=VECTOR_STORE_NAME
            )
            if vector_db._collection.count() > 0:
                logging.info("Found existing vector database.")
                return vector_db
        except Exception as e:
            logging.warning(f"Existing DB issue: {e}")
    return None

# Ingest PUML content and split into manageable chunks
def ingest_puml(puml_path):
    """Load PUML content and split into manageable chunks."""
    if os.path.exists(puml_path):
        with open(puml_path, 'r', encoding='utf-8') as file:
            content = file.read()
        logging.info("PUML file loaded successfully.")
        return content
    else:
        logging.error(f"PUML file not found at path: {puml_path}")
        return None

def split_documents(content, puml_path):
    """Split PUML content into smaller chunks as Document objects."""
    # Calculate file hash for change detection
    file_hash = hash(content)
    
    chunks = []
    
    # Strategy 1: Split by entities (more semantic)
    entity_pattern = r'(entity\s+\w+\s*\{[^}]+\})'
    entities = re.findall(entity_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if entities:
        logging.info(f"Found {len(entities)} entities using entity pattern")
        for i, entity in enumerate(entities):
            chunks.append(Document(
                page_content=entity,
                metadata={
                    "source": "puml_file", 
                    "chunk_id": len(chunks),
                    "chunk_type": "entity",
                    "source_file": puml_path,
                    "source_file_hash": file_hash
                }
            ))
    
    # Strategy 2: Split by relationships
    relationship_pattern = r'(\w+\s+--\s+\w+|"\w+"\s+--\s+"\w+")'
    relationships = re.findall(relationship_pattern, content)
    
    if relationships:
        logging.info(f"Found {len(relationships)} relationships")
        relationship_chunk = "Relationships:\n" + "\n".join(relationships)
        chunks.append(Document(
            page_content=relationship_chunk,
            metadata={
                "source": "puml_file", 
                "chunk_id": len(chunks),
                "chunk_type": "relationships",
                "source_file": puml_path,
                "source_file_hash": file_hash
            }
        ))
    
    # Strategy 3: Fallback - split by lines if no entities found
    if not chunks:
        logging.info("Using line-based chunking as fallback")
        lines = content.splitlines()
        chunk_size = 15
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunk_text = "\n".join(chunk_lines)
            chunks.append(Document(
                page_content=chunk_text,
                metadata={
                    "source": "puml_file", 
                    "chunk_id": len(chunks),
                    "chunk_type": "line_chunk",
                    "source_file": puml_path,
                    "source_file_hash": file_hash
                }
            ))
    
    logging.info(f"PUML content split into {len(chunks)} chunks.")
    return chunks

# Create a vector database from PUML content
def create_vector_db(chunks, puml_path):
    """Create a vector database from PUML content chunks."""
    # Clear existing vector DB if it exists
    if not clear_vector_db():
        logging.error("Failed to clear existing vector database. Creating in memory only.")
        # Fallback to in-memory database
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
            collection_name=VECTOR_STORE_NAME
        )
        logging.info("In-memory vector database created.")
        return vector_db
    
    try:
        # Ensure directory exists with proper permissions
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True, mode=0o755)
        
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
            collection_name=VECTOR_STORE_NAME,
            persist_directory=PERSIST_DIRECTORY
        )
        vector_db.persist()
        logging.info(f"Vector database created and persisted for {puml_path}.")
        return vector_db
    except Exception as e:
        logging.error(f"Error creating persistent vector DB: {e}. Using in-memory fallback.")
        # Fallback to in-memory database
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
            collection_name=VECTOR_STORE_NAME
        )
        logging.info("In-memory vector database created as fallback.")
        return vector_db

# Load the vector database
def load_vector_db():
    """Load existing vector database."""
    try:
        vector_db = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
            collection_name=VECTOR_STORE_NAME
        )
        logging.info("Vector database loaded from disk.")
        return vector_db
    except Exception as e:
        logging.error(f"Error loading vector DB: {e}")
        return None

# Create a retriever to query the vector DB
def create_retriever(vector_db):
    """Create a multi-query retriever."""
    llm = ChatOllama(model=MODEL_NAME)

    QUERY_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""Eres un asistente especializado en diagramas UML y bases de datos. 
Genera 3 versiones diferentes de la siguiente pregunta para mejorar la búsqueda de información relevante.

Pregunta original: {question}

Genera 3 variaciones diferentes. Cada variación debe enfocarse en diferentes aspectos:
1. Una variación técnica sobre estructura de tablas
2. Una variación sobre relaciones y constraints
3. Una variación sobre tipos de datos específicos

Variaciones:"""
)

    retriever = MultiQueryRetriever.from_llm(
        vector_db.as_retriever(search_kwargs={"k": 5}),  # Más documentos para mejor contexto
        llm, 
        prompt=QUERY_PROMPT
    )

    logging.info("Retriever created.")
    return retriever

# Create the chain for LLM + retrieval
def create_chain(retriever):
    """Create the chain to process queries."""
    llm = ChatOllama(model=MODEL_NAME)
    
    
    template = """Eres un experto en bases de datos y diagramas UML. Analiza el diagrama PUML y genera código SQL.

    CONTEXTO del diagrama:
    {context}

    INSTRUCCIONES para la pregunta: {question}

    REQUISITOS:
    1. Analiza las entidades y relaciones del diagrama
    2. Genera código SQL válido y funcional
    3. Especifica el tipo de base de datos
    4. Incluye todas las tablas necesarias
    5. Usa nombres originales en inglés

    RESPONDE solo con código SQL en este formato:

    -- migrate:up
    CREATE TABLE nombre_tabla (
    id TIPO_PRIMARY_KEY,
    columna1 TIPO_DATO,
    PRIMARY KEY (id)
    );
    -- migrate:down
    DROP TABLE nombre_tabla;

    No incluyas explicaciones ni texto adicional."""

    prompt = ChatPromptTemplate.from_template(template=template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    logging.info("Chain created successfully.")
    return chain

# MEJORADO: Genera migraciones con enfoque más directo
def generate_sql_migrations_with_rag(chain, db_type, puml_file):
    """Generate SQL migrations - PROMPT MEJORADO para Gemma."""
    
    with open(puml_file, 'r', encoding='utf-8') as f:
        puml_content = f.read()
    
    # Extraer información del PUML
    entity_pattern = r'entity\s+(\w+)\s*\{([^}]+)\}'
    entities = re.findall(entity_pattern, puml_content, re.IGNORECASE | re.DOTALL)
    
    entity_details = []
    for entity_name, entity_content in entities:
        # Extraer atributos
        attribute_pattern = r'(\w+)\s*:\s*([^\n;]+)'
        attributes = re.findall(attribute_pattern, entity_content)
        
        attr_list = []
        for attr_name, attr_type in attributes:
            # Limpiar y formatear
            attr_type_clean = attr_type.strip().rstrip(',')
            attr_list.append(f"{attr_name}: {attr_type_clean}")
        
        entity_details.append(f"ENTITY: {entity_name}")
        if attr_list:
            entity_details.append(f"  Attributes: {', '.join(attr_list)}")
        entity_details.append("")  # Línea en blanco
    
    # Extraer relaciones
    relationship_pattern = r'(\w+)\s*--\s*(\w+)'
    relationships = re.findall(relationship_pattern, puml_content)
    
    entities_summary = "\n".join(entity_details)
    
    # PROMPT CORREGIDO - ESCAPAR LLAVES
    query = f"""
OBJETIVO: Generar código SQL para crear tablas a partir de un diagrama UML en PlantUML.

DIAGRAMA PUML:
{entities_summary}

RELACIONES DETECTADAS:
{chr(10).join([f'{rel[0]} -- {rel[1]}' for rel in relationships]) if relationships else 'No hay relaciones explícitas'}

CONFIGURACIÓN:
- Tipo de base de datos: {db_type.upper()}
- Cada entidad debe convertirse en una tabla
- Cada atributo debe convertirse en una columna

INSTRUCCIONES ESPECÍFICAS:
1. Para CADA entidad en el diagrama, genera UN bloque de migración
2. Cada bloque debe tener EXACTAMENTE este formato:

-- migrate:up
CREATE TABLE NombreEntidad (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  -- Añadir aquí las columnas basadas en los atributos
  columna1 TIPO_DE_DATO,
  columna2 TIPO_DE_DATO
);
-- migrate:down
DROP TABLE NombreEntidad;

3. Usa tipos de datos apropiados para {db_type.upper()}:
   - Para MySQL/PostgreSQL: INT, VARCHAR(255), TEXT, DATETIME, BOOLEAN
   - Para SQLite: INTEGER, TEXT, REAL, BLOB

4. Convierte los tipos UML a tipos SQL:
   - String → VARCHAR(255) o TEXT
   - Integer → INT o INTEGER
   - Boolean → BOOLEAN o TINYINT(1)
   - Date → DATE
   - DateTime → DATETIME

5. Incluye FOREIGN KEYS para las relaciones detectadas

EJEMPLO CONCRETO:
Para una entidad: User {{id: Integer, name: String, email: String}}  <!-- LLAVES ESCAPADAS -->

Debes generar:
-- migrate:up
CREATE TABLE User (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL
);
-- migrate:down
DROP TABLE User;

AHORA, genera el código SQL para las entidades listadas arriba.

RESPONDE SOLAMENTE con los bloques de código SQL en el formato especificado.
NO añadas explicaciones, comentarios adicionales ni texto fuera del formato.
"""
    
    print("🚀 Generando migraciones SQL con Gemma 3 1B...")
    print("📝 Usando prompt estructurado...")
    
    try:
        response = chain.invoke(query)
        print("✅ Respuesta recibida del modelo")
        return response
    except Exception as e:
        logging.error(f"Error generando migraciones: {e}")
        return f"Error: {e}"
    
# MEJORADO: Parser más robusto
def parse_migration_blocks(complete_migrations):
    """
    Parsea los bloques de migración - versión MUCHO más robusta para Gemma.
    """
    print("\n🔍 DEPURACIÓN: Analizando respuesta del modelo...")
    print("="*60)
    print("RESPUESTA COMPLETA DEL MODELO:")
    print("="*60)
    print(complete_migrations[:2000] + "..." if len(complete_migrations) > 2000 else complete_migrations)
    print("="*60)
    
    # Si es un error, manejarlo
    if complete_migrations.startswith("Error:"):
        logging.error(f"Error del modelo: {complete_migrations}")
        return {}
    
    # Limpiar la respuesta (eliminar texto explicativo de Gemma)
    lines = complete_migrations.split('\n')
    sql_lines = []
    
    # Estados para seguimiento
    in_sql_block = False
    in_create_table = False
    current_sql = []
    all_sql_blocks = []
    
    for line in lines:
        line_stripped = line.strip().lower()
        
        # Detectar inicio de bloque SQL
        if ('-- migrate:up' in line_stripped or 
            'create table' in line_stripped or
            line_stripped.startswith('create table')):
            
            if not in_sql_block:
                in_sql_block = True
                in_create_table = True
                current_sql = [line]  # Iniciar nuevo bloque
            else:
                current_sql.append(line)
                
        elif in_sql_block:
            current_sql.append(line)
            
            # Detectar fin de sentencia CREATE TABLE
            if ';' in line and in_create_table:
                in_create_table = False
            
            # Detectar inicio de DROP TABLE
            if '-- migrate:down' in line_stripped or 'drop table' in line_stripped:
                if ';' in line:
                    # Fin del bloque completo
                    all_sql_blocks.append('\n'.join(current_sql))
                    in_sql_block = False
                    current_sql = []
                else:
                    # Continuar recogiendo DROP TABLE
                    pass
            elif ';' in line and not in_create_table and not in_sql_block:
                # Fin de DROP TABLE
                all_sql_blocks.append('\n'.join(current_sql))
                in_sql_block = False
                current_sql = []
    
    # Si quedó algún bloque sin cerrar
    if current_sql:
        all_sql_blocks.append('\n'.join(current_sql))
    
    print(f"\n📊 Bloques SQL encontrados: {len(all_sql_blocks)}")
    for i, block in enumerate(all_sql_blocks[:3], 1):
        print(f"\nBloque {i}:")
        print("-"*40)
        print(block[:500] + "..." if len(block) > 500 else block)
    
    # Procesar los bloques encontrados
    tables_dict = {}
    seen_tables = set()
    
    for block_idx, sql_block in enumerate(all_sql_blocks, 1):
        # Buscar CREATE TABLE en el bloque
        create_match = re.search(r'(CREATE TABLE[^;]+;)', sql_block, re.IGNORECASE | re.DOTALL)
        
        if not create_match:
            continue
            
        create_stmt = create_match.group(1)
        table_name = extract_table_name(create_stmt)
        
        if not table_name:
            continue
            
        # Evitar duplicados
        if table_name in seen_tables:
            print(f"⚠️  Saltando tabla duplicada: {table_name}")
            continue
            
        seen_tables.add(table_name)
        
        # Buscar DROP TABLE correspondiente
        drop_match = re.search(r'(DROP TABLE[^;]+;)', sql_block, re.IGNORECASE | re.DOTALL)
        if drop_match:
            drop_stmt = drop_match.group(1)
        else:
            # Generar DROP TABLE automáticamente
            drop_stmt = f"DROP TABLE IF EXISTS {table_name};"
        
        # Limpiar y formatear
        clean_create = ' '.join(create_stmt.replace('\n', ' ').split())
        clean_drop = ' '.join(drop_stmt.replace('\n', ' ').split())
        
        # Crear bloque completo
        complete_block = f"-- migrate:up\n\n{create_stmt.strip()}\n\n-- migrate:down\n\n{drop_stmt.strip()}"
        
        tables_dict[block_idx] = {
            'up': clean_create,
            'down': clean_drop,
            'complete_block': complete_block,
            'table_name': table_name
        }
        
        print(f"✅ Procesada tabla {table_name}")
    
    print(f"\n🎯 Total de tablas parseadas: {len(tables_dict)}")
    
    if not tables_dict:
        print("\n⚠️  ADVERTENCIA: No se encontraron tablas. Mostrando patrones detectados...")
        # Intentar búsqueda más agresiva
        aggressive_create_matches = re.findall(r'CREATE\s+TABLE\s+[^;]+;', complete_migrations, re.IGNORECASE)
        print(f"Matches agresivos: {len(aggressive_create_matches)}")
        for match in aggressive_create_matches[:3]:
            print(f"  - {match[:100]}...")
    
    return tables_dict
    """
    Parsea los bloques de migración - versión mejorada para Gemma.
    """
    # Limpiar respuestas verbosas de Gemma
    lines = complete_migrations.split('\n')
    clean_lines = []
    in_sql_block = False
    
    for line in lines:
        # Buscar inicio de bloque SQL
        if '-- migrate:up' in line.lower() or 'create table' in line.lower():
            in_sql_block = True
        
        if in_sql_block:
            clean_lines.append(line)
            
            # Fin de sentencia SQL
            if line.strip().endswith(';'):
                # Verificar si es el final del bloque
                if '-- migrate:down' in line.lower() or 'drop table' in line.lower():
                    in_sql_block = False
    
    clean_migrations = '\n'.join(clean_lines)
    
    # Patrones más flexibles
    patterns = [
        # Patrón con ambos bloques
        r'(--\s*migrate:up[^-]*--\s*migrate:down[^;]+;)',
        # Patrón solo CREATE (generaremos DROP)
        r'(CREATE TABLE[^;]+;)',
    ]
    # ... resto del código igual

def extract_table_name(sql_statement):
    """
    Extrae el nombre de la tabla de una sentencia SQL.
    """
    # Múltiples patrones para diferentes formatos
    patterns = [
        r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?`?([^\s`(;]+)`?',
        r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?([^\s(;]+)',
        r'DROP TABLE\s+(?:IF EXISTS\s+)?`?([^\s`;]+)`?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, sql_statement, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def validate_entity_count(puml_file, tables_dict):
    """Validate that we have the expected number of entities."""
    try:
        with open(puml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        entity_pattern = r'entity\s+(\w+)'
        entities = re.findall(entity_pattern, content, re.IGNORECASE)
        
        expected_count = len(entities)
        actual_count = len(tables_dict)
        
        logging.info(f"Expected entities: {expected_count}, Generated tables: {actual_count}")
        
        if expected_count != actual_count:
            print(f"⚠️  ADVERTENCIA: Se esperaban {expected_count} tablas pero se generaron {actual_count}")
            
            # Mostrar entidades encontradas vs generadas
            generated_tables = [data.get('table_name') for data in tables_dict.values() if data.get('table_name')]
            missing_entities = set(entities) - set(generated_tables)
            
            if missing_entities:
                print(f"📋 Entidades faltantes: {', '.join(missing_entities)}")
            
            if generated_tables:
                print(f"📋 Tablas generadas: {', '.join(generated_tables)}")
        
        return expected_count, actual_count
    except Exception as e:
        logging.error(f"Error validating entity count: {e}")
        return 0, len(tables_dict)

def enforce_original_names(puml_file, tables_dict):
    """Ensure table names match the original PUML entities."""
    try:
        with open(puml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        entity_pattern = r'entity\s+(\w+)'
        original_entities = re.findall(entity_pattern, content, re.IGNORECASE)
        
        corrected_dict = {}
        correction_count = 0
        
        for key, table_data in tables_dict.items():
            current_name = table_data.get('table_name')
            
            # Buscar entidad original que coincida (case insensitive)
            matching_entity = None
            for entity in original_entities:
                if entity.lower() == current_name.lower():
                    matching_entity = entity
                    break
            
            if matching_entity and matching_entity != current_name:
                # Corregir el nombre de la tabla
                correction_count += 1
                corrected_up = re.sub(
                    f'TABLE\\s+{re.escape(current_name)}', 
                    f'TABLE {matching_entity}', 
                    table_data['up'], 
                    flags=re.IGNORECASE
                )
                corrected_down = re.sub(
                    f'TABLE\\s+{re.escape(current_name)}', 
                    f'TABLE {matching_entity}', 
                    table_data['down'], 
                    flags=re.IGNORECASE
                )
                
                # Actualizar bloque completo
                corrected_block = re.sub(
                    f'TABLE\\s+{re.escape(current_name)}', 
                    f'TABLE {matching_entity}', 
                    table_data['complete_block'], 
                    flags=re.IGNORECASE
                )
                
                corrected_dict[key] = {
                    'up': corrected_up,
                    'down': corrected_down,
                    'complete_block': corrected_block,
                    'table_name': matching_entity
                }
                
                print(f"✓ Corregido: '{current_name}' -> '{matching_entity}'")
            else:
                corrected_dict[key] = table_data
        
        if correction_count > 0:
            print(f"✓ Se corrigieron {correction_count} nombres de tabla")
        
        return corrected_dict
    except Exception as e:
        logging.error(f"Error enforcing original names: {e}")
        return tables_dict

def save_migration_files(tables_dict, puml_basename, db_type, complete_migrations, nombre_carpeta):
    """Guardar archivos de migración dentro de una carpeta específica."""
    if not tables_dict:
        print("❌ No hay migraciones para guardar.")
        return False
    
    try:
        # 1. Asegurar que existe la carpeta principal
        os.makedirs(nombre_carpeta, exist_ok=True)
        print(f"📁 Carpeta principal: {nombre_carpeta}")
        
        # 2. Guardar migraciones completas en un solo archivo dentro de la carpeta
        complete_filename = os.path.join(nombre_carpeta, f"complete_migrations_{puml_basename}_{db_type}.sql")
        with open(complete_filename, 'w', encoding='utf-8') as f:
            f.write(f"-- Migraciones generadas desde: {puml_basename}.puml\n")
            f.write(f"-- Tipo de base de datos: {db_type}\n")
            f.write(f"-- Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Total de tablas: {len(tables_dict)}\n")
            f.write(f"-- Carpeta: {nombre_carpeta}\n\n")
            f.write(complete_migrations)
        print(f"✓ Migraciones completas guardadas en: {complete_filename}")
        
        # 3. Crear subcarpeta 'migrations' dentro de la carpeta principal
        migrations_dir = os.path.join(nombre_carpeta, "migrations")
        
        # Limpiar si ya existe
        if os.path.exists(migrations_dir):
            shutil.rmtree(migrations_dir)
            print(f"♻️  Limpiando carpeta migrations existente")
        
        os.makedirs(migrations_dir, exist_ok=True)
        print(f"📂 Subcarpeta migrations creada en: {migrations_dir}")
        
        # 4. Guardar cada migración en archivo individual dentro de migrations/
        base_timestamp = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        saved_count = 0

        for key, table_data in tables_dict.items():
            table_name = table_data.get('table_name')
            if table_name:
                # Formato: timestamp_incremental_create_nombretabla.sql
                timestamp = str(base_timestamp + key)
                migration_filename = os.path.join(migrations_dir, f"{timestamp}_create_{table_name}.sql")

                with open(migration_filename, 'w', encoding='utf-8') as f:
                    f.write(table_data['complete_block'])
                
                saved_count += 1
                print(f"  ✓ Migración {key:2d} ({table_name:20s}) → {migration_filename}")
        
        # 5. Opcional: Crear archivo de resumen/metadatos
        metadata_file = os.path.join(nombre_carpeta, "metadata.json")
        metadata = {
            "puml_file": f"{puml_basename}.puml",
            "database_type": db_type,
            "generation_date": datetime.datetime.now().isoformat(),
            "total_tables": len(tables_dict),
            "saved_files": saved_count,
            "tables": [data.get('table_name') for data in tables_dict.values() if data.get('table_name')]
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"✓ Metadatos guardados en: {metadata_file}")
        
        # 6. Opcional: Crear README en la carpeta principal
        readme_file = os.path.join(nombre_carpeta, "README.md")
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(f"# Migraciones SQL - {puml_basename}\n\n")
            f.write(f"**Fecha de generación:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Tipo de base de datos:** {db_type}\n")
            f.write(f"**Archivo PUML origen:** {puml_basename}.puml\n")
            f.write(f"**Total de tablas generadas:** {len(tables_dict)}\n\n")
            f.write("## Estructura de carpetas\n\n")
            f.write("- `migrations/` - Archivos individuales de migración\n")
            f.write("- `complete_migrations_*.sql` - Todas las migraciones en un archivo\n")
            f.write("- `metadata.json` - Información de generación\n")
            f.write("- `README.md` - Este archivo\n\n")
            f.write("## Tablas generadas\n\n")
            for key, table_data in tables_dict.items():
                table_name = table_data.get('table_name', 'Desconocida')
                f.write(f"{key}. `{table_name}`\n")
        
        print(f"✓ README creado en: {readme_file}")
        print(f"\n{'='*60}")
        print(f"✅ COMPLETADO: {saved_count} archivos guardados en {nombre_carpeta}")
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar archivos: {e}")
        return False

def demo(folder_path, db_type, modelo):
    # Paso 1: Ingresar el tipo de base de datos
    db_type = db_type
    # Paso 2: Ingresar el archivo PUML
    puml_file = os.path.join(modelo)

    # Paso 3: Verificar y gestionar la base vectorial
    vector_db = check_existing_vector_db()
    
    # Check if we need to recreate the vector DB
    if should_recreate_vector_db(puml_file, vector_db):
        print("Creando nueva base de datos vectorial...")
        content = ingest_puml(puml_file)
        if not content:
            return "❌ No se pudo crear la base de datos vectorial.", False
        
        chunks = split_documents(content, puml_file)
        vector_db = create_vector_db(chunks, puml_file)
    else:
        print("Usando base de datos vectorial existente.")

    # Crear el retriever y la cadena
    retriever = create_retriever(vector_db)
    chain = create_chain(retriever)

    # Paso 4: Generar las migraciones SQL
    print(f"Generando migraciones SQL para {puml_file}...")

    # Intentar con RAG primero
    complete_migrations = generate_sql_migrations_with_rag(chain, db_type, puml_file)

    # Verificar si el modelo rechazó la generación
    if "No puedo cumplir" in complete_migrations or "I cannot fulfill" in complete_migrations or complete_migrations.startswith("Error:"):
        print("❌ El modelo rechazó generar migraciones. Usando método alternativo...")
        # complete_migrations = generate_direct_migrations(puml_file, db_type)
        return "❌ No se pudieron generar migraciones.", False
    
    if not complete_migrations or "Error:" in complete_migrations:
        print("❌ No se pudieron generar migraciones.")
        return "❌ No se pudieron generar migraciones.", False

    # Mostrar las migraciones generadas
    print("\n" + "="*60)
    print(f"MIGRACIONES SQL GENERADAS PARA: {puml_file}")
    print("="*60)
    print(complete_migrations)

    # Paso 5: Parsear y organizar en diccionario
    print("\n" + "="*60)
    print("ORGANIZANDO EN DICCIONARIO:")
    print("="*60)
    
    tables_dict = parse_migration_blocks(complete_migrations)
    
    if not tables_dict:
        print("❌ No se pudieron parsear las migraciones.")
        return "❌ No se pudieron parsear las migraciones.", False

    # Validar conteo de entidades
    expected_count, actual_count = validate_entity_count(puml_file, tables_dict)

    print('expected_count: ' + str(expected_count))
    print('actual_count: ' + str(actual_count))
    
    # Forzar nombres originales
    tables_dict = enforce_original_names(puml_file, tables_dict)

    resp = []

    if tables_dict:
        print(f"\n✅ Se procesaron {len(tables_dict)} tablas ÚNICAS:\n")
        
        for key, table_data in tables_dict.items():
            table_name = table_data.get('table_name')
            print(f"Tabla {key} ({table_name}):")
            print(f"  UP:   {table_data['up']}")
            print(f"  DOWN: {table_data['down']}")
            print("-" * 80)
            resp.append(table_data)
    else:
        print("❌ No se pudieron procesar las migraciones.")
        return "❌ No se pudieron procesar las migraciones.", False

    #return resp, True

    # Paso 6: Guardar archivos
    print("Guardando las migraciones en archivos")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Crear nombre de carpeta
    nombre_carpeta = f"{timestamp}_{folder_path}"
    # Crear la carpeta
    os.makedirs(nombre_carpeta, exist_ok=True)

    puml_basename = os.path.splitext(os.path.basename(puml_file))[0]

    save_migration_files(tables_dict, puml_basename, db_type, complete_migrations, nombre_carpeta)

    # Opción adicional: guardar diccionario como JSON
    print("Guardardando diccionario como JSON")
    json_filename = os.path.join(nombre_carpeta, f"migrations_dict_{puml_basename}_{db_type}.json")
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(tables_dict, f, indent=2, ensure_ascii=False)
    print(f"✓ Diccionario guardado en: {json_filename}")

def measuring(folder_path, db_type, archivo_puml, csv_file='measurements.csv'):
    """Ejecuta demo con mediciones de CPU, RAM y GPU - VERSIÓN CORREGIDA."""
    import time
    import csv
    import psutil
    import threading
    import queue
    import datetime
    import traceback

    from gpus_measures import detect_gpu_libraries, get_gpu_info
    
    # Modelo de LLM
    modelo_llm = "gemma3:1b"
    
    # Detectar bibliotecas de GPU disponibles
    gpu_libs = detect_gpu_libraries()
    
    # Variables para mediciones
    total_start_time = time.time()
    
    success = False
    error_message = ""
    num_tables = 0
    expected_tables = 0
    
    # Variables para promedios (INICIALIZADAS CORRECTAMENTE)
    cpu_avg_during_rag = 0.0
    memory_avg_during_rag = 0.0
    gpu_util_avg = 0.0
    gpu_mem_avg = 0.0
    gpu_temp_avg = 0.0
    gpu_util_max = 0.0
    gpu_mem_max = 0.0
    gpu_temp_max = 0.0
    
    # Listas para muestras
    gpu_util_samples = []
    gpu_mem_samples = []
    gpu_temp_samples = []
    
    try:
        print(f"\n{'='*60}")
        print(f"INICIANDO PRUEBA: demo_{folder_path}_{db_type}")
        print(f"Modelo LLM: {modelo_llm}")
        print(f"Base de datos: {db_type}")
        print(f"Archivo PUML: {archivo_puml}")
        print(f"GPU detectada: {', '.join(gpu_libs) if gpu_libs else 'No disponible'}")
        print(f"{'='*60}")
        
        # MEDICIÓN 1: Estado inicial
        memory_before = psutil.virtual_memory().used / (1024 * 1024)
        cpu_before = psutil.cpu_percent(interval=0.1)
        
        # Obtener ruta completa del archivo PUML
        puml_file = os.path.join(archivo_puml)
        print(f"📄 Ruta completa: {os.path.abspath(puml_file)}")
        
        # Verificar que el archivo existe
        if not os.path.exists(puml_file):
            error_message = f"Archivo PUML no encontrado: {puml_file}"
            print(f"❌ {error_message}")
            raise FileNotFoundError(error_message)
        
        # Paso 3: Base de datos vectorial
        vector_db = check_existing_vector_db()
        
        if should_recreate_vector_db(puml_file, vector_db):
            print("🔄 Creando nueva base de datos vectorial...")
            content = ingest_puml(puml_file)
            if not content:
                error_message = "No se pudo crear la base de datos vectorial"
                raise Exception(error_message)
            
            chunks = split_documents(content, puml_file)
            vector_db = create_vector_db(chunks, puml_file)
        else:
            print("✅ Usando base de datos vectorial existente.")

        retriever = create_retriever(vector_db)
        chain = create_chain(retriever)

        # Paso 4: Generación RAG
        print(f"\n🚀 Generando migraciones SQL usando {modelo_llm}...")
        
        # FUNCIÓN DE MONITOREO CORREGIDA
        def monitor_all_resources(cpu_q, ram_q, gpu_q, stop_event, sample_interval=0.3):
            """Monitorea CPU, RAM y GPU periódicamente."""
            cpu_samples_local = []
            ram_samples_local = []
            gpu_util_samples_local = []
            gpu_mem_samples_local = []
            gpu_temp_samples_local = []
            
            while not stop_event.is_set():
                try:
                    # Medir CPU
                    cpu = psutil.cpu_percent(interval=sample_interval)
                    cpu_samples_local.append(float(cpu))
                    
                    # Medir RAM
                    ram = psutil.virtual_memory().used / (1024 * 1024)
                    ram_samples_local.append(float(ram))
                    
                    # Medir GPU
                    gpu_info = get_gpu_info(gpu_libs)
                    if gpu_info:
                        if 'utilization' in gpu_info and gpu_info['utilization'] is not None:
                            gpu_util_samples_local.append(float(gpu_info['utilization']))
                        if 'memory_used' in gpu_info and gpu_info['memory_used'] is not None:
                            gpu_mem_samples_local.append(float(gpu_info['memory_used']))
                        if 'temperature' in gpu_info and gpu_info['temperature'] is not None:
                            gpu_temp_samples_local.append(float(gpu_info['temperature']))
                    
                    # Limitar tamaño
                    max_samples = 50
                    for lst in [cpu_samples_local, ram_samples_local, 
                               gpu_util_samples_local, gpu_mem_samples_local, 
                               gpu_temp_samples_local]:
                        if len(lst) > max_samples:
                            lst.pop(0)
                except Exception as e:
                    # Continuar a pesar de errores menores
                    continue
            
            # CORREGIDO: Asegurar que enviamos listas vacías si no hay datos
            cpu_q.put(cpu_samples_local if cpu_samples_local else [])
            ram_q.put(ram_samples_local if ram_samples_local else [])
            
            gpu_data = {
                'utilization': gpu_util_samples_local if gpu_util_samples_local else [],
                'memory': gpu_mem_samples_local if gpu_mem_samples_local else [],
                'temperature': gpu_temp_samples_local if gpu_temp_samples_local else []
            }
            gpu_q.put(gpu_data)
        
        # Iniciar monitoreo
        print("📈 Iniciando monitoreo de CPU, RAM y GPU durante RAG...")
        cpu_queue = queue.Queue()
        ram_queue = queue.Queue()
        gpu_queue = queue.Queue()
        stop_event = threading.Event()
        
        monitor_thread = threading.Thread(
            target=monitor_all_resources,
            args=(cpu_queue, ram_queue, gpu_queue, stop_event, 0.3)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Pequeña pausa
        time.sleep(0.1)
        
        # MEDICIÓN 2: Ejecutar RAG
        rag_start_time = time.time()
        
        try:
            complete_migrations = generate_sql_migrations_with_rag(chain, db_type, puml_file)
        finally:
            # Detener monitoreo
            stop_event.set()
            monitor_thread.join(timeout=2.0)
            
            # Obtener muestras de forma segura
            try:
                cpu_samples = cpu_queue.get(timeout=1.0)
                ram_samples = ram_queue.get(timeout=1.0)
                gpu_data = gpu_queue.get(timeout=1.0) if gpu_libs else {}
                
                # Calcular promedios de forma SEGURA
                if cpu_samples and len(cpu_samples) > 0:
                    # Asegurar que todos son números
                    cpu_numeric = [float(x) for x in cpu_samples if isinstance(x, (int, float))]
                    if cpu_numeric:
                        cpu_avg_during_rag = sum(cpu_numeric) / len(cpu_numeric)
                
                if ram_samples and len(ram_samples) > 0:
                    ram_numeric = [float(x) for x in ram_samples if isinstance(x, (int, float))]
                    if ram_numeric:
                        memory_avg_during_rag = sum(ram_numeric) / len(ram_numeric)
                
                if gpu_data:
                    # GPU utilization
                    if 'utilization' in gpu_data and gpu_data['utilization']:
                        util_numeric = [float(x) for x in gpu_data['utilization'] if isinstance(x, (int, float))]
                        if util_numeric:
                            gpu_util_samples = util_numeric
                            gpu_util_avg = sum(util_numeric) / len(util_numeric)
                            gpu_util_max = max(util_numeric) if util_numeric else 0.0
                    
                    # GPU memory
                    if 'memory' in gpu_data and gpu_data['memory']:
                        mem_numeric = [float(x) for x in gpu_data['memory'] if isinstance(x, (int, float))]
                        if mem_numeric:
                            gpu_mem_samples = mem_numeric
                            gpu_mem_avg = sum(mem_numeric) / len(mem_numeric)
                            gpu_mem_max = max(mem_numeric) if mem_numeric else 0.0
                    
                    # GPU temperature
                    if 'temperature' in gpu_data and gpu_data['temperature']:
                        temp_numeric = [float(x) for x in gpu_data['temperature'] if isinstance(x, (int, float))]
                        if temp_numeric:
                            gpu_temp_samples = temp_numeric
                            gpu_temp_avg = sum(temp_numeric) / len(temp_numeric)
                            gpu_temp_max = max(temp_numeric) if temp_numeric else 0.0
                            
            except queue.Empty:
                print("⚠️  Timeout al obtener muestras")
            except Exception as e:
                print(f"⚠️  Error procesando muestras: {e}")
        
        rag_end_time = time.time()
        rag_time_ms = (rag_end_time - rag_start_time) * 1000
        
        # MOSTRAR MÉTRICAS CORREGIDAS - ¡ESTA ES LA PARTE IMPORTANTE!
        print(f"\n📊 MÉTRICAS DURANTE RAG:")
        print(f"⏱️  Tiempo: {rag_time_ms:.2f} ms")
        print(f"📈 CPU promedio: {cpu_avg_during_rag:.1f}%")
        print(f"💾 RAM promedio: {memory_avg_during_rag:.2f} MB")
        
        # CORREGIDO: Verificar que tenemos muestras antes de imprimir
        if gpu_libs:
            if gpu_util_samples:
                print(f"🎮 GPU uso promedio: {gpu_util_avg:.1f}%")
                print(f"   GPU uso máximo: {gpu_util_max:.1f}%")
            if gpu_mem_samples:
                print(f"💾 GPU memoria promedio: {gpu_mem_avg:.2f} MB")
                print(f"   GPU memoria máxima: {gpu_mem_max:.2f} MB")
            if gpu_temp_samples:
                print(f"🌡️  GPU temperatura promedio: {gpu_temp_avg:.1f}°C")
                print(f"   GPU temperatura máxima: {gpu_temp_max:.1f}°C")
        else:
            print("🎮 GPU: No disponible para monitoreo")

        # Verificar resultado del RAG
        if not complete_migrations or complete_migrations.startswith("Error:"):
            error_message = "No se pudieron generar migraciones"
            print(f"❌ {error_message}")
            raise Exception(error_message)
        
        if "No puedo cumplir" in complete_migrations or "I cannot fulfill" in complete_migrations:
            error_message = "El modelo rechazó generar migraciones"
            print(f"❌ {error_message}")
            raise Exception(error_message)

        # Paso 5: Parsear migraciones
        parsing_start_time = time.time()
        tables_dict = parse_migration_blocks(complete_migrations)
        parsing_end_time = time.time()
        parsing_time_ms = (parsing_end_time - parsing_start_time) * 1000
        
        if not tables_dict:
            error_message = "No se pudieron parsear las migraciones"
            raise Exception(error_message)

        # Validar conteo
        expected_count, actual_count = validate_entity_count(puml_file, tables_dict)
        expected_tables = expected_count
        num_tables = actual_count
        
        tables_dict = enforce_original_names(puml_file, tables_dict)
        
        if tables_dict:
            print(f"\n✅ Se generaron {len(tables_dict)} tablas:")
            for i, (key, table_data) in enumerate(list(tables_dict.items())[:5], 1):
                table_name = table_data.get('table_name')
                print(f"  {i}. {table_name}")
            
            if len(tables_dict) > 5:
                print(f"  ... y {len(tables_dict) - 5} tablas más")
        else:
            raise Exception("No se pudieron procesar las migraciones")

        # Paso 6: Guardar archivos
        print("\n💾 Guardando las migraciones en archivos...")
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_carpeta = f"{timestamp}_{folder_path}_{db_type}"
        os.makedirs(nombre_carpeta, exist_ok=True)

        puml_basename = os.path.splitext(os.path.basename(puml_file))[0]
        save_migration_files(tables_dict, puml_basename, db_type, complete_migrations, nombre_carpeta)

        json_filename = os.path.join(nombre_carpeta, f"migrations_dict_{puml_basename}_{db_type}.json")
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(tables_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Archivos guardados en: {nombre_carpeta}")
        success = True
        
    except Exception as e:
        if not error_message:
            error_message = str(e)
        print(f"\n❌ ERROR: {error_message}")
        success = False
        traceback.print_exc()  # Esto mostrará exactamente dónde está el error
    
    finally:
        # MEDICIÓN FINAL
        total_end_time = time.time()
        total_time_ms = (total_end_time - total_start_time) * 1000
        
        memory_final = psutil.virtual_memory().used / (1024 * 1024)
        cpu_final = psutil.cpu_percent(interval=0.1)
        
        # Preparar datos para CSV
        test_id = f"{folder_path}_{db_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_name = f"demo_{folder_path}_{db_type}"
        
        csv_columns = [
            'test_id', 'test_name', 'modelo_llm', 'db_type', 'archivo_puml',
            'total_time_ms', 'rag_time_ms', 'parsing_time_ms',
            'memory_before_mb', 'memory_avg_during_rag_mb', 'memory_final_mb',
            'cpu_before', 'cpu_avg_during_rag', 'cpu_final',
            'success', 'error_message', 'num_tables', 'expected_tables',
            'timestamp'
        ]
        
        # Añadir columnas de GPU si está disponible
        if gpu_libs:
            csv_columns[14:14] = [  # Insertar antes de 'success'
                'gpu_util_avg_rag', 'gpu_mem_avg_rag', 'gpu_temp_avg_rag',
                'gpu_util_max_rag', 'gpu_mem_max_rag', 'gpu_temp_max_rag'
            ]
        
        csv_data = [
            test_id,
            test_name,
            modelo_llm,
            db_type,
            archivo_puml,
            total_time_ms,
            rag_time_ms,
            parsing_time_ms,
            memory_before,
            memory_avg_during_rag,
            memory_final,
            cpu_before,
            cpu_avg_during_rag,
            cpu_final
        ]
        
        # Añadir datos de GPU si están disponibles
        if gpu_libs:
            csv_data.extend([
                gpu_util_avg,
                gpu_mem_avg,
                gpu_temp_avg,
                gpu_util_max,
                gpu_mem_max,
                gpu_temp_max
            ])
        
        csv_data.extend([
            success,
            error_message,
            num_tables,
            expected_tables,
            datetime.datetime.now().isoformat()
        ])
        
        # Guardar en CSV
        try:
            # Crear archivo si no existe
            file_exists = os.path.exists(csv_file)
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(csv_columns)
                writer.writerow(csv_data)
            
            print(f"\n📊 Métricas guardadas en CSV: {csv_file}")
            
            # Mostrar resumen
            print(f"\n{'='*60}")
            print("📈 RESUMEN DE MÉTRICAS:")
            print(f"{'='*60}")
            print(f"✅ Éxito: {'SÍ' if success else 'NO'}")
            print(f"🤖 Modelo LLM: {modelo_llm}")
            print(f"🗄️  Base de datos: {db_type}")
            print(f"\n⏱️  Tiempos:")
            print(f"  - Total: {total_time_ms:.2f} ms")
            print(f"  - RAG:   {rag_time_ms:.2f} ms")
            print(f"  - Parseo: {parsing_time_ms:.2f} ms")
            
            print(f"\n💾 RAM:")
            print(f"  - Inicio: {memory_before:.2f} MB")
            print(f"  - Promedio: {memory_avg_during_rag:.2f} MB")
            print(f"  - Final: {memory_final:.2f} MB")
            
            print(f"\n📈 CPU:")
            print(f"  - Inicio: {cpu_before:.1f}%")
            print(f"  - Promedio: {cpu_avg_during_rag:.1f}%")
            print(f"  - Final: {cpu_final:.1f}%")
            
            if gpu_libs:
                print(f"\n🎮 GPU:")
                print(f"  - Uso promedio: {gpu_util_avg:.1f}%")
                print(f"  - Memoria promedio: {gpu_mem_avg:.2f} MB")
                print(f"  - Temp promedio: {gpu_temp_avg:.1f}°C")
            
            print(f"\n📊 Resultados:")
            print(f"  - Tablas generadas: {num_tables}")
            print(f"  - Tablas esperadas: {expected_tables}")
            
            if not success and error_message:
                print(f"\n⚠️  ERROR: {error_message}")
            
            print(f"{'='*60}")
            
        except Exception as csv_error:
            print(f"❌ Error al guardar en CSV: {csv_error}")
            traceback.print_exc()
    
    if success:
        # Crear lista de respuestas
        resp = []
        for key, table_data in tables_dict.items():
            resp.append(table_data)
        return resp, True
    else:
        return f"Error: {error_message}", False
    