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
MODEL_NAME = "llama3.2"
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
        
        Genera 3 variaciones diferentes:"""
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
    
    template = """Eres un experto en bases de datos y diagramas UML. 
Tu tarea es ANALIZAR el diagrama PUML proporcionado y GENERAR código SQL.

CONTEXTO del diagrama PUML:
{context}

INSTRUCCIONES para la pregunta: {question}

- Analiza las entidades (entity) y sus relaciones del diagrama
- Genera código SQL funcional y válido
- Especifica el tipo de base de datos objetivo
- Incluye todas las tablas, relaciones y constraints necesarios
- SÉ ESPECÍFICO y PRÁCTICO"""

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
    """Generate SQL migrations using a more direct approach."""
    
    # Primero, analizar el contenido del archivo PUML
    with open(puml_file, 'r', encoding='utf-8') as f:
        puml_content = f.read()
    
    # Extraer entidades para mostrar al modelo
    entity_pattern = r'entity\s+(\w+)\s*\{([^}]+)\}'
    entities = re.findall(entity_pattern, puml_content, re.IGNORECASE | re.DOTALL)
    
    entity_info = []
    for entity_name, entity_content in entities:
        # Extraer atributos
        attributes = re.findall(r'\s*(\w+)\s*:\s*([^\n]+)', entity_content)
        entity_info.append(f"Entidad: {entity_name}, Atributos: {attributes}")
    
    entities_summary = "\n".join(entity_info)
    
    query = f"""
ANÁLISIS DE DIAGRAMA UML Y GENERACIÓN DE MIGRACIONES SQL

ARCHIVO: {puml_file}
TIPO DE BASE DE DATOS: {db_type.upper()}

ENTIDADES ENCONTRADAS EN EL DIAGRAMA:
{entities_summary}

INSTRUCCIONES ESPECÍFICAS:

1. ANALIZA cada entidad del diagrama UML y conviértela en una sentencia CREATE TABLE
2. USA el formato EXACTO de migración que se muestra a continuación
3. PRESERVA los nombres ORIGINALES de las entidades y atributos
4. GENERA código SQL VÁLIDO para {db_type.upper()}

FORMATO REQUERIDO para CADA tabla:

-- migrate:up

CREATE TABLE nombre_tabla (
  id TIPO_PRIMARY_KEY,
  columna1 TIPO_DATO,
  columna2 TIPO_DATO,
  PRIMARY KEY (id),
  FOREIGN KEY (columna_relacionada) REFERENCES tabla_relacionada(id)
);

-- migrate:down

DROP TABLE nombre_tabla;

REQUISITOS TÉCNICOS:
- Para {db_type.upper()}, usa tipos de datos apropiados
- Incluye PRIMARY KEY autoincremental para cada tabla
- Incluye FOREIGN KEYS basadas en las relaciones del diagrama
- Mantén los nombres ORIGINALES en inglés (NO traduzcas)
- Genera EXACTAMENTE una migración por cada entidad encontrada

RESPONDE ÚNICAMENTE con las sentencias SQL en el formato especificado, sin explicaciones.
"""
    
    print("Generando migraciones SQL... Esto puede tomar unos momentos.")
    try:
        response = chain.invoke(query)
        return response
    except Exception as e:
        logging.error(f"Error generating migrations: {e}")
        return f"Error: {e}"

# MEJORADO: Parser más robusto
def parse_migration_blocks(complete_migrations):
    """
    Parsea los bloques de migración y crea el diccionario de tablas.
    """
    # Si la respuesta es un error, manejarlo
    if complete_migrations.startswith("Error:") or "No puedo cumplir" in complete_migrations:
        logging.error(f"Model refused to generate migrations: {complete_migrations}")
        return {}
    
    # Patrones más flexibles para diferentes formatos
    patterns = [
        # Patrón para formato completo con migrate:up y migrate:down
        r'--\s*migrate:up\s*(CREATE TABLE[^;]+;)\s*--\s*migrate:down\s*(DROP TABLE[^;]+;)',
        # Patrón solo para CREATE TABLE (generaremos DROP automáticamente)
        r'(CREATE TABLE[^;]+;)',
    ]
    
    tables_dict = {}
    seen_tables = set()
    
    for pattern in patterns:
        matches = re.findall(pattern, complete_migrations, re.IGNORECASE | re.DOTALL)
        if matches:
            logging.info(f"Found {len(matches)} matches using pattern")
            
            for i, match in enumerate(matches, len(tables_dict) + 1):
                if isinstance(match, tuple):
                    # Formato completo con up y down
                    create_stmt, drop_stmt = match
                else:
                    # Solo CREATE TABLE, generar DROP
                    create_stmt = match
                    table_name = extract_table_name(create_stmt)
                    drop_stmt = f"DROP TABLE IF EXISTS {table_name};" if table_name else "DROP TABLE unknown_table;"
                
                table_name = extract_table_name(create_stmt)
                
                # Evitar duplicados
                if table_name and table_name in seen_tables:
                    logging.info(f"Skipping duplicate table: {table_name}")
                    continue
                    
                seen_tables.add(table_name)
                
                # Clean and format
                clean_create = re.sub(r'\s+', ' ', create_stmt.strip())
                clean_drop = re.sub(r'\s+', ' ', drop_stmt.strip())
                
                # Create complete block
                complete_block = f"-- migrate:up\n\n{create_stmt.strip()}\n\n-- migrate:down\n\n{drop_stmt.strip()}"
                
                tables_dict[i] = {
                    'up': clean_create,
                    'down': clean_drop,
                    'complete_block': complete_block,
                    'table_name': table_name
                }
    
    logging.info(f"Se encontraron {len(tables_dict)} tablas únicas.")
    return tables_dict

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

def save_migration_files(tables_dict, puml_basename, db_type, complete_migrations):
    """Guardar archivos de migración."""
    if not tables_dict:
        print("❌ No hay migraciones para guardar.")
        return
    
    # Guardar migraciones completas en un solo archivo
    complete_filename = f"complete_migrations_{puml_basename}_{db_type}.sql"
    with open(complete_filename, 'w', encoding='utf-8') as f:
        f.write(f"-- Migraciones generadas desde: {puml_basename}.puml\n")
        f.write(f"-- Tipo de base de datos: {db_type}\n")
        f.write(f"-- Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Total de tablas: {len(tables_dict)}\n\n")
        f.write(complete_migrations)
    print(f"✓ Migraciones completas guardadas en: {complete_filename}")
    
    # Guardar cada migración en archivo individual
    migrations_dir = f"migrations_{puml_basename}_{db_type}"
    if os.path.exists(migrations_dir):
        shutil.rmtree(migrations_dir)
    os.makedirs(migrations_dir, exist_ok=True)
    
    base_timestamp = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    saved_count = 0

    for key, table_data in tables_dict.items():
        table_name = table_data.get('table_name')
        if table_name:
            timestamp = str(base_timestamp + key)
            migration_filename = f"{migrations_dir}/{timestamp}_create_{table_name}.sql"

            with open(migration_filename, 'w', encoding='utf-8') as f:
                f.write(table_data['complete_block'])
            
            saved_count += 1
            print(f"✓ Migración {key} ({table_name}) guardada en: {migration_filename}")

    print(f"✓ Total de archivos guardados: {saved_count}")

# FALLBACK: Generación directa si RAG falla
def generate_direct_migrations(puml_file, db_type):
    """Generate migrations directly from PUML file as fallback."""
    print("Usando método de generación directa como fallback...")
    
    try:
        with open(puml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer entidades
        entity_pattern = r'entity\s+(\w+)\s*\{([^}]+)\}'
        entities = re.findall(entity_pattern, content, re.IGNORECASE | re.DOTALL)
        
        migrations = []
        
        for entity_name, entity_content in entities:
            # Extraer atributos
            attr_pattern = r'\s*(\w+)\s*:\s*([^\n]+)'
            attributes = re.findall(attr_pattern, entity_content)
            
            # Generar CREATE TABLE
            create_lines = [f"CREATE TABLE {entity_name} ("]
            create_lines.append("  id SERIAL PRIMARY KEY," if db_type == 'postgres' else "  id INTEGER PRIMARY KEY AUTOINCREMENT,")
            
            for attr_name, attr_type in attributes:
                # Mapear tipos PUML a SQL
                sql_type = map_puml_to_sql(attr_type, db_type)
                create_lines.append(f"  {attr_name} {sql_type},")
            
            # Remover última coma y cerrar
            create_lines[-1] = create_lines[-1].rstrip(',')
            create_lines.append(");")
            
            create_stmt = "\n".join(create_lines)
            drop_stmt = f"DROP TABLE IF EXISTS {entity_name};"
            
            # Crear bloque completo
            migration_block = f"-- migrate:up\n\n{create_stmt}\n\n-- migrate:down\n\n{drop_stmt}\n"
            migrations.append(migration_block)
        
        return "\n".join(migrations)
    
    except Exception as e:
        logging.error(f"Error in direct migration generation: {e}")
        return ""

def map_puml_to_sql(puml_type, db_type):
    """Map PUML types to SQL types."""
    puml_type = puml_type.lower().strip()
    
    type_mappings = {
        'sqlite': {
            'string': 'TEXT',
            'int': 'INTEGER', 
            'integer': 'INTEGER',
            'boolean': 'INTEGER',
            'date': 'TEXT',
            'datetime': 'TEXT',
            'float': 'REAL',
            'double': 'REAL',
            'text': 'TEXT'
        },
        'mysql': {
            'string': 'VARCHAR(255)',
            'int': 'INT',
            'integer': 'INT',
            'boolean': 'BOOLEAN',
            'date': 'DATE',
            'datetime': 'DATETIME',
            'float': 'FLOAT',
            'double': 'DOUBLE',
            'text': 'TEXT'
        },
        'postgres': {
            'string': 'VARCHAR(255)',
            'int': 'INTEGER',
            'integer': 'INTEGER',
            'boolean': 'BOOLEAN',
            'date': 'DATE',
            'datetime': 'TIMESTAMP',
            'float': 'REAL',
            'double': 'DOUBLE PRECISION',
            'text': 'TEXT'
        }
    }
    
    return type_mappings.get(db_type, {}).get(puml_type, 'TEXT')
# === FUNCIÓN MAIN MEJORADA ===

def demo(folder_path, db_type):
    # Paso 1: Ingresar el tipo de base de datos
    db_type = db_type
    # Paso 2: Ingresar el archivo PUML
    puml_file = os.path.join(folder_path, "modelo.puml")

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
        complete_migrations = generate_direct_migrations(puml_file, db_type)
    
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
    
    # Forzar nombres originales
    tables_dict = enforce_original_names(puml_file, tables_dict)

    if tables_dict:
        print(f"\n✅ Se procesaron {len(tables_dict)} tablas ÚNICAS:\n")
        
        for key, table_data in tables_dict.items():
            table_name = table_data.get('table_name')
            print(f"Tabla {key} ({table_name}):")
            print(f"  UP:   {table_data['up']}")
            print(f"  DOWN: {table_data['down']}")
            print("-" * 80)
    else:
        print("❌ No se pudieron procesar las migraciones.")
        return "❌ No se pudieron procesar las migraciones.", False

    return tables_dict, True

    # Paso 6: Guardar archivos
    save_file = input("\n¿Guardar las migraciones en archivos? (s/n): ").strip().lower()
    if save_file == 's':
        puml_basename = os.path.splitext(os.path.basename(puml_file))[0]

        save_migration_files(tables_dict, puml_basename, db_type, complete_migrations)

        # Opción adicional: guardar diccionario como JSON
        save_json = input("¿Guardar diccionario como JSON? (s/n): ").strip().lower()
        if save_json == 's':
            json_filename = f"migrations_dict_{puml_basename}_{db_type}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(tables_dict, f, indent=2, ensure_ascii=False)
            print(f"✓ Diccionario guardado en: {json_filename}")


def demo2(folder_path, db_type):
    # Paso 1: Ingresar el tipo de base de datos
    db_type = db_type
    # Paso 2: Ingresar el archivo PUML
    puml_file = os.path.join(folder_path, "modelo.puml")

    print('A ------------------------------------')
    print(puml_file)
    print('B ------------------------------------')
    entities = extract_entities_from_puml(puml_file)
    if not entities:
        print("❌ No se pudieron extraer entidades del archivo PUML.")
        return "❌ No se pudieron extraer entidades del archivo PUML.", False
    
    print(f"\n📋 ENTIDADES ENCONTRADAS EN EL ARCHIVO PUML:")
    for entity in entities:
        print(f"  - {entity['name']}: {len(entity['attributes'])} atributos")
    
    # Configuración de RAG
    vector_db = check_existing_vector_db()
    
    if should_recreate_vector_db(puml_file, vector_db):
        print("Creando nueva base de datos vectorial...")
        content = ingest_puml(puml_file)
        if not content:
            return
        chunks = split_documents(content, puml_file)
        vector_db = create_vector_db(chunks, puml_file)
    else:
        print("Usando base de datos vectorial existente.")

    retriever = create_retriever(vector_db)
    chain = create_chain(retriever)

    # Generar migraciones con el método mejorado
    print(f"\n🔄 Generando migraciones SQL para {db_type.upper()}...")
    complete_migrations = improved_sql_generation_with_rag(chain, db_type, puml_file)

    # Validación final
    final_validation = validate_generated_tables(complete_migrations, entities)
    
    print(f"\n✅ VALIDACIÓN FINAL:")
    print(f"   Entidades esperadas: {final_validation['expected_count']}")
    print(f"   Tablas generadas: {final_validation['generated_count']}")
    
    if final_validation['missing_tables']:
        print(f"   ⚠️  Tablas faltantes: {final_validation['missing_tables']}")
    if final_validation['extra_tables']:
        print(f"   ⚠️  Tablas extrañas: {final_validation['extra_tables']}")
    
    if final_validation['is_valid']:
        print("   ✅ Todas las entidades fueron convertidas correctamente a tablas")
    else:
        print("   ⚠️  Hay discrepancias en la conversión")

    # Mostrar resultado
    print("\n" + "="*60)
    print("MIGRACIONES SQL GENERADAS:")
    print("="*60)
    print(complete_migrations)

    # Continuar con el procesamiento normal (parseo, guardado, etc.)
    tables_dict = parse_migration_blocks(complete_migrations)
    
    if tables_dict:
        # Guardar archivos
        save_file = input("\n¿Guardar las migraciones en archivos? (s/n): ").strip().lower()
        if save_file == 's':
            puml_basename = os.path.splitext(os.path.basename(puml_file))[0]
            save_migration_files(tables_dict, puml_basename, db_type, complete_migrations)
            
            return tables_dict, True
    else:
        print("❌ No se pudieron procesar las migraciones.")
        return "❌ No se pudieron procesar las migraciones.", False