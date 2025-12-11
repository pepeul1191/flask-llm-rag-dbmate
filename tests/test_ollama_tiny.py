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
MODEL_NAME = "llama3.2:1b"
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
    """Ejecuta demo con mediciones de CPU, RAM y GPU."""
    import time
    import csv
    import psutil
    import threading
    import queue
    import datetime

    from gpus_measures import detect_gpu_libraries, print_resumen_metricas, get_gpu_info
    
    # Modelo de LLM (Ollama) - ahora es una variable del método
    modelo_llm = "llama3.2:1b"  # O el modelo que estés usando
    
    # Detectar bibliotecas de GPU disponibles
    gpu_libs = detect_gpu_libraries()
    
    # Crear o inicializar CSV con columnas actualizadas
    csv_columns = [
        'test_id', 'test_name', 'modelo_llm', 'db_type', 'archivo_puml',
        'total_time_ms', 'rag_time_ms', 'parsing_time_ms',
        'memory_before_mb', 'memory_avg_during_rag_mb', 'memory_final_mb',
        'cpu_before', 'cpu_avg_during_rag', 'cpu_final'
    ]
    
    # Añadir columnas de GPU según lo disponible
    if 'nvidia' in gpu_libs:
        csv_columns.extend([
            'gpu_util_avg_rag', 'gpu_mem_avg_rag', 'gpu_temp_avg_rag',
            'gpu_util_max_rag', 'gpu_mem_max_rag', 'gpu_temp_max_rag'
        ])
    elif 'amd' in gpu_libs:
        csv_columns.extend(['gpu_util_avg_rag', 'gpu_mem_avg_rag', 'gpu_temp_avg_rag'])
    elif 'intel' in gpu_libs:
        csv_columns.extend(['gpu_util_avg_rag', 'gpu_mem_avg_rag'])
    
    csv_columns.extend([
        'num_tables', 'expected_tables', 'success', 'error_message',
        'timestamp'
    ])
    
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(csv_columns)
    
    # Generar ID único
    test_id = f"{folder_path}_{db_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_name = f"demo_{folder_path}_{db_type}"
    
    # Variables para mediciones
    total_start_time = time.time()
    
    success = False
    error_message = ""
    num_tables = 0
    expected_tables = 0
    
    # Variables para muestras
    cpu_samples = []
    ram_samples = []
    gpu_util_samples = []
    gpu_mem_samples = []
    gpu_temp_samples = []
    
    # Variables para promedios
    cpu_avg_during_rag = 0
    memory_avg_during_rag = 0
    gpu_util_avg = 0
    gpu_mem_avg = 0
    gpu_temp_avg = 0
    # dbmate
    migrations_status = ''
    migrations_error = 'error'
    
    try:
        print(f"\n{'='*60}")
        print(f"INICIANDO PRUEBA: {test_name}")
        print(f"Modelo LLM: {modelo_llm}")
        print(f"Base de datos: {db_type}")
        print(f"Archivo PUML: {archivo_puml}")
        print(f"GPU detectada: {', '.join(gpu_libs) if gpu_libs else 'No disponible'}")
        print(f"{'='*60}")
        
        # MEDICIÓN 1: Estado inicial
        memory_before = psutil.virtual_memory().used / (1024 * 1024)
        cpu_before = psutil.cpu_percent(interval=0.1)
        
        # Medición inicial de GPU si está disponible
        gpu_info_before = get_gpu_info(gpu_libs)
        
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

        # Paso 4: Generación RAG con medición completa
        print(f"\n🚀 Generando migraciones SQL usando {modelo_llm}...")
        
        # Función para monitorear todos los recursos
        def monitor_all_resources(cpu_q, ram_q, gpu_q, stop_event, sample_interval=0.3):
            """Monitorea CPU, RAM y GPU periódicamente."""
            cpu_samples_local = []
            ram_samples_local = []
            gpu_util_samples_local = []
            gpu_mem_samples_local = []
            gpu_temp_samples_local = []
            
            while not stop_event.is_set():
                # Medir CPU (esto bloquea por sample_interval segundos)
                cpu = psutil.cpu_percent(interval=sample_interval)
                cpu_samples_local.append(cpu)
                
                # Medir RAM inmediatamente después
                ram = psutil.virtual_memory().used / (1024 * 1024)
                ram_samples_local.append(ram)
                
                # Medir GPU si está disponible
                gpu_info = get_gpu_info(gpu_libs)
                if gpu_info:
                    if 'utilization' in gpu_info:
                        gpu_util_samples_local.append(gpu_info['utilization'])
                    if 'memory_used' in gpu_info:
                        gpu_mem_samples_local.append(gpu_info['memory_used'])
                    if 'temperature' in gpu_info:
                        gpu_temp_samples_local.append(gpu_info['temperature'])
                
                # Limitar tamaño de muestras
                max_samples = 100
                for lst in [cpu_samples_local, ram_samples_local, 
                           gpu_util_samples_local, gpu_mem_samples_local, 
                           gpu_temp_samples_local]:
                    if len(lst) > max_samples:
                        lst.pop(0)
            
            # Enviar muestras a las colas
            cpu_q.put(cpu_samples_local)
            ram_q.put(ram_samples_local)
            
            gpu_data = {
                'utilization': gpu_util_samples_local,
                'memory': gpu_mem_samples_local,
                'temperature': gpu_temp_samples_local
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
        
        # Pequeña pausa para que el thread comience
        time.sleep(0.1)
        
        # MEDICIÓN 2: Ejecutar RAG
        rag_start_time = time.time()
        
        try:
            complete_migrations = generate_sql_migrations_with_rag(chain, db_type, puml_file)
        finally:
            # Detener monitoreo
            stop_event.set()
            monitor_thread.join(timeout=2.0)
            
            # Obtener muestras
            try:
                cpu_samples = cpu_queue.get(timeout=1.0)
                ram_samples = ram_queue.get(timeout=1.0)
                gpu_data = gpu_queue.get(timeout=1.0) if gpu_libs else {}
                
                # Calcular promedios
                if cpu_samples:
                    cpu_avg_during_rag = sum(cpu_samples) / len(cpu_samples)
                
                if ram_samples:
                    memory_avg_during_rag = sum(ram_samples) / len(ram_samples)
                
                if 'utilization' in gpu_data and gpu_data['utilization']:
                    gpu_util_samples = gpu_data['utilization']
                    gpu_util_avg = sum(gpu_util_samples) / len(gpu_util_samples)
                
                if 'memory' in gpu_data and gpu_data['memory']:
                    gpu_mem_samples = gpu_data['memory']
                    gpu_mem_avg = sum(gpu_mem_samples) / len(gpu_mem_samples)
                
                if 'temperature' in gpu_data and gpu_data['temperature']:
                    gpu_temp_samples = gpu_data['temperature']
                    gpu_temp_avg = sum(gpu_temp_samples) / len(gpu_temp_samples)
                    
            except queue.Empty:
                print("⚠️  Timeout al obtener muestras")
        
        rag_end_time = time.time()
        rag_time_ms = (rag_end_time - rag_start_time) * 1000
        
        # Mostrar métricas
        print(f"\n📊 MÉTRICAS DURANTE RAG:")
        print(f"⏱️  Tiempo: {rag_time_ms:.2f} ms")
        print(f"📈 CPU promedio: {cpu_avg_during_rag:.1f}%")
        print(f"💾 RAM promedio: {memory_avg_during_rag:.2f} MB")
        
        if gpu_libs:
            if gpu_util_samples:
                print(f"🎮 GPU uso promedio: {gpu_util_avg:.1f}%")
                print(f"   GPU uso máximo: {max(gpu_util_samples) if gpu_util_samples else 0:.1f}%")
            if gpu_mem_samples:
                print(f"💾 GPU memoria promedio: {gpu_mem_avg:.2f} MB")
                print(f"   GPU memoria máxima: {max(gpu_mem_samples) if gpu_mem_samples else 0:.2f} MB")
            if gpu_temp_samples:
                print(f"🌡️  GPU temperatura promedio: {gpu_temp_avg:.1f}°C")
                print(f"   GPU temperatura máxima: {max(gpu_temp_samples) if gpu_temp_samples else 0:.1f}°C")
        else:
            print("🎮 GPU: No disponible para monitoreo")

        # Verificar resultado del RAG
        if "No puedo cumplir" in complete_migrations or "I cannot fulfill" in complete_migrations or complete_migrations.startswith("Error:"):
            error_message = "El modelo rechazó generar migraciones"
            print(f"❌ {error_message}")
            raise Exception(error_message)
        
        if not complete_migrations or "Error:" in complete_migrations:
            error_message = "No se pudieron generar migraciones"
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
        resp = []
        
        if tables_dict:
            print(f"\n✅ Se generaron {len(tables_dict)} tablas:")
            for i, (key, table_data) in enumerate(list(tables_dict.items())[:5], 1):
                table_name = table_data.get('table_name')
                print(f"  {i}. {table_name}")
            
            if len(tables_dict) > 5:
                print(f"  ... y {len(tables_dict) - 5} tablas más")
            
            for key, table_data in tables_dict.items():
                resp.append(table_data)
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

        # Migraciones DBMate
        # .env de dbmate
        url = ''
        if db_type == 'mysql':
            url = f"mysql://root:123@localhost:3306/{timestamp}"
        elif db_type == 'sqlite':
            current_dir = os.getcwd()
            url = f"sqlite://{os.path.join(current_dir, nombre_carpeta, f'{timestamp}.db')}"
        elif db_type == 'postgres':
            url = f"postgres://root:123@localhost:5432/{timestamp}"
        else:
            pass

        if url != '':
            env_path = os.path.join(nombre_carpeta, '.env')
            with open(env_path, "w") as archivo:
                archivo.write('DATABASE_URL=' + url)
        import subprocess
        # Ejecutar dbmate up especificando el directorio de migraciones
        print(f"Ejecutando dbmate up en: {nombre_carpeta + '/migrations'}")
        result = subprocess.run(
            ['dbmate', '--migrations-dir', nombre_carpeta + '/migrations', 'up'],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, 'DATABASE_URL': url}
        )
        print("dbmate output:", result.stdout)
        if result.stderr:
            print("dbmate errors:", result.stderr)
            migrations_error = result.stderr
            migrations_status = 'error'
        else:
            migrations_status = 'success'

        success = True
        
    except Exception as e:
        if not error_message:
            error_message = str(e)
        print(f"\n❌ ERROR: {error_message}")
        success = False
    
    finally:
        # MEDICIÓN FINAL
        total_end_time = time.time()
        total_time_ms = (total_end_time - total_start_time) * 1000
        
        memory_final = psutil.virtual_memory().used / (1024 * 1024)
        cpu_final = psutil.cpu_percent(interval=0.1)
        
        # Medición final de GPU
        gpu_info_final = get_gpu_info(gpu_libs)
        
        # Preparar datos para CSV
        csv_data = [
            test_id,
            test_name,
            modelo_llm,          # Nueva columna: modelo de LLM
            db_type,
            archivo_puml,        # Nueva columna: nombre del archivo PUML
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
        
        # Añadir datos de GPU según lo disponible
        if 'nvidia' in gpu_libs:
            csv_data.extend([
                gpu_util_avg,
                gpu_mem_avg,
                gpu_temp_avg,
                max(gpu_util_samples) if gpu_util_samples else 0,
                max(gpu_mem_samples) if gpu_mem_samples else 0,
                max(gpu_temp_samples) if gpu_temp_samples else 0
            ])
        elif 'amd' in gpu_libs or 'intel' in gpu_libs:
            csv_data.extend([
                gpu_util_avg,
                gpu_mem_avg,
                gpu_temp_avg if 'amd' in gpu_libs else 0
            ])
        
        csv_data.extend([
            num_tables,
            expected_tables,
            success,
            error_message,
            datetime.datetime.now().isoformat(),
            migrations_status,
            migrations_error,
        ])
        
        # Guardar en CSV
        try:
            with open(csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(csv_data)
            
            print(f"\n📊 Métricas guardadas en CSV: {csv_file}")
            
            # Mostrar resumen detallado
            print(f"\n{'='*60}")
            print("📈 RESUMEN COMPLETO DE MÉTRICAS:")
            print(f"{'='*60}")
            print(f"✅ Éxito: {'SÍ' if success else 'NO'}")
            print(f"🤖 Modelo LLM: {modelo_llm}")
            print(f"🗄️  Base de datos: {db_type}")
            print(f"📄 Archivo PUML: {archivo_puml}")
            print(f"\n⏱️  Tiempos:")
            print(f"  - Total: {total_time_ms:.2f} ms")
            print(f"  - RAG:   {rag_time_ms:.2f} ms")
            print(f"  - Parseo: {parsing_time_ms:.2f} ms")
            
            print(f"\n💾 RAM:")
            print(f"  - Antes RAG:       {memory_before:.2f} MB")
            print(f"  - Promedio durante RAG: {memory_avg_during_rag:.2f} MB")
            print(f"  - Final:           {memory_final:.2f} MB")
            
            print(f"\n📈 CPU:")
            print(f"  - Antes RAG:       {cpu_before:.1f}%")
            print(f"  - Promedio durante RAG: {cpu_avg_during_rag:.1f}%")
            print(f"  - Final:           {cpu_final:.1f}%")
            
            if gpu_libs:
                print(f"\n🎮 GPU ({', '.join(gpu_libs)}):")
                if gpu_util_samples:
                    print(f"  - Uso promedio:    {gpu_util_avg:.1f}%")
                if gpu_mem_samples:
                    print(f"  - Memoria promedio: {gpu_mem_avg:.2f} MB")
                if gpu_temp_samples and gpu_temp_avg > 0:
                    print(f"  - Temp promedio:    {gpu_temp_avg:.1f}°C")
            
            print(f"\n📊 Resultados:")
            print(f"  - Tablas generadas: {num_tables}")
            print(f"  - Tablas esperadas: {expected_tables}")
            
            if not success and error_message:
                print(f"\n⚠️  ERROR: {error_message}")
            
            print(f"{'='*60}")
            
        except Exception as csv_error:
            print(f"❌ Error al guardar en CSV: {csv_error}")
    
    if success:
        return resp, True
    else:
        return f"Error: {error_message}", False