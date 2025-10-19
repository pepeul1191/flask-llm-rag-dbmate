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

# === FUNCIONES DE GESTIÓN DE VECTOR DB ===

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

# === FUNCIONES DE RAG Y CADENA ===

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

# === FUNCIONES MEJORADAS PARA EXTRACCIÓN Y GENERACIÓN ===

def extract_entities_from_puml(puml_file):
    """
    Extrae explícitamente SOLO las entidades definidas en el archivo PUML.
    Retorna una lista de diccionarios con información estructurada de cada entidad.
    """
    try:
        with open(puml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        entities = []
        
        # Patrón mejorado para capturar entidades y sus atributos
        entity_pattern = r'entity\s+(\w+)\s*\{([^}]+)\}'
        matches = re.findall(entity_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for entity_name, entity_content in matches:
            # Extraer atributos de la entidad
            attr_pattern = r'\s*(\w+)\s*:\s*([^\n,]+)'
            attributes = re.findall(attr_pattern, entity_content)
            
            # Limpiar y estructurar los atributos
            clean_attributes = []
            for attr_name, attr_type in attributes:
                clean_attributes.append({
                    'name': attr_name.strip(),
                    'type': attr_type.strip()
                })
            
            entities.append({
                'name': entity_name.strip(),
                'attributes': clean_attributes,
                'raw_content': entity_content.strip()
            })
        
        logging.info(f"Extraídas {len(entities)} entidades del archivo PUML")
        return entities
        
    except Exception as e:
        logging.error(f"Error extrayendo entidades del PUML: {e}")
        return []

def create_focused_prompt(entities, db_type):
    """
    Crea un prompt MUY específico que se enfoca únicamente en las entidades extraídas.
    """
    entities_description = ""
    
    for i, entity in enumerate(entities, 1):
        entities_description += f"\n--- ENTIDAD {i}: {entity['name']} ---\n"
        entities_description += f"Atributos:\n"
        for attr in entity['attributes']:
            entities_description += f"  - {attr['name']}: {attr['type']}\n"
    
    prompt = f"""
INSTRUCCIONES ESTRICTAS PARA GENERACIÓN DE MIGRACIONES SQL:

TIPO DE BASE DE DATOS: {db_type.upper()}

ENTIDADES EXTRACTAS DEL DIAGRAMA UML:
{entities_description}

REQUISITOS ABSOLUTOS:

1. GENERAR EXCLUSIVAMENTE las siguientes tablas: {', '.join([e['name'] for e in entities])}
2. NO INVENTAR tablas adicionales
3. NO INCLUIR tablas que no estén en la lista anterior
4. BASARSE ÚNICAMENTE en los atributos proporcionados

FORMATO EXACTO para cada tabla:

-- migrate:up

CREATE TABLE nombre_tabla (
  id [TIPO_PRIMARY_KEY],
  [atributos específicos de la entidad],
  PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE nombre_tabla;

ESPECIFICACIONES TÉCNICAS:
- Para {db_type.upper()}, usar tipos de datos apropiados
- PRIMARY KEY autoincremental
- SOLO incluir los atributos listados para cada entidad
- NO agregar atributos adicionales
- NO crear tablas de relación a menos que se especifiquen en el PUML

GENERAR EXACTAMENTE UNA MIGRACIÓN POR CADA ENTIDAD LISTADA.

RESPONDER ÚNICAMENTE CON EL CÓDIGO SQL EN EL FORMATO ESPECIFICADO.
"""
    return prompt

def validate_generated_tables(generated_sql, expected_entities):
    """
    Valida que las tablas generadas coincidan exactamente con las entidades esperadas.
    """
    # Extraer nombres de tablas del SQL generado
    table_pattern = r'CREATE TABLE\s+(\w+)'
    generated_tables = re.findall(table_pattern, generated_sql, re.IGNORECASE)
    
    expected_table_names = [entity['name'] for entity in expected_entities]
    
    # Verificar tablas faltantes
    missing_tables = set(expected_table_names) - set(generated_tables)
    
    # Verificar tablas extrañas (no debería haber)
    extra_tables = set(generated_tables) - set(expected_table_names)
    
    validation_result = {
        'expected_count': len(expected_table_names),
        'generated_count': len(generated_tables),
        'missing_tables': list(missing_tables),
        'extra_tables': list(extra_tables),
        'is_valid': len(missing_tables) == 0 and len(extra_tables) == 0
    }
    
    return validation_result

def enforce_exact_entities(generated_sql, expected_entities, db_type):
    """
    Fuerza que el SQL generado contenga EXACTAMENTE las entidades esperadas.
    Si faltan tablas, las genera automáticamente.
    """
    validation = validate_generated_tables(generated_sql, expected_entities)
    
    if validation['is_valid']:
        return generated_sql
    
    logging.warning(f"Validación fallida: Tablas faltantes: {validation['missing_tables']}, Tablas extra: {validation['extra_tables']}")
    
    # Filtrar solo las tablas válidas
    valid_tables = []
    table_blocks = re.split(r'-- migrate:up', generated_sql)
    
    for block in table_blocks:
        if not block.strip():
            continue
            
        table_match = re.search(r'CREATE TABLE\s+(\w+)', block, re.IGNORECASE)
        if table_match and table_match.group(1) in [e['name'] for e in expected_entities]:
            valid_tables.append(f"-- migrate:up{block}")
    
    # Generar tablas faltantes automáticamente
    for missing_table in validation['missing_tables']:
        entity = next((e for e in expected_entities if e['name'] == missing_table), None)
        if entity:
            migration_block = generate_simple_migration(entity, db_type)
            valid_tables.append(migration_block)
            logging.info(f"Generada migración automática para tabla faltante: {missing_table}")
    
    return "\n\n".join(valid_tables)

def generate_simple_migration(entity, db_type):
    """
    Genera una migración simple y directa para una entidad específica.
    """
    # Mapeo de tipos
    type_mapping = {
        'sqlite': {
            'string': 'TEXT', 'int': 'INTEGER', 'integer': 'INTEGER',
            'boolean': 'INTEGER', 'date': 'TEXT', 'datetime': 'TEXT',
            'float': 'REAL', 'double': 'REAL', 'text': 'TEXT'
        },
        'mysql': {
            'string': 'VARCHAR(255)', 'int': 'INT', 'integer': 'INT',
            'boolean': 'BOOLEAN', 'date': 'DATE', 'datetime': 'DATETIME',
            'float': 'FLOAT', 'double': 'DOUBLE', 'text': 'TEXT'
        },
        'postgres': {
            'string': 'VARCHAR(255)', 'int': 'INTEGER', 'integer': 'INTEGER',
            'boolean': 'BOOLEAN', 'date': 'DATE', 'datetime': 'TIMESTAMP',
            'float': 'REAL', 'double': 'DOUBLE PRECISION', 'text': 'TEXT'
        }
    }
    
    # Determinar tipo de primary key
    if db_type == 'sqlite':
        pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
    elif db_type == 'mysql':
        pk_type = "INT AUTO_INCREMENT PRIMARY KEY"
    elif db_type == 'postgres':
        pk_type = "SERIAL PRIMARY KEY"
    else:
        pk_type = "INTEGER PRIMARY KEY"
    
    # Construir CREATE TABLE
    create_lines = [f"CREATE TABLE {entity['name']} ("]
    create_lines.append(f"  id {pk_type},")
    
    for attr in entity['attributes']:
        sql_type = type_mapping.get(db_type, {}).get(attr['type'].lower(), 'TEXT')
        create_lines.append(f"  {attr['name']} {sql_type},")
    
    # Remover última coma y cerrar
    if create_lines[-1].endswith(','):
        create_lines[-1] = create_lines[-1][:-1]
    create_lines.append(");")
    
    create_stmt = "\n".join(create_lines)
    drop_stmt = f"DROP TABLE IF EXISTS {entity['name']};"
    
    return f"-- migrate:up\n\n{create_stmt}\n\n-- migrate:down\n\n{drop_stmt}"

def generate_direct_migrations_from_entities(entities, db_type):
    """
    Genera migraciones directamente desde las entidades extraídas.
    """
    migrations = []
    
    for entity in entities:
        migration_block = generate_simple_migration(entity, db_type)
        migrations.append(migration_block)
    
    return "\n\n".join(migrations)

def generate_fallback_migrations(puml_file, db_type):
    """
    Fallback completo si todo lo demás falla.
    """
    try:
        with open(puml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        entities = []
        entity_pattern = r'entity\s+(\w+)\s*\{([^}]+)\}'
        matches = re.findall(entity_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for entity_name, entity_content in matches:
            attr_pattern = r'\s*(\w+)\s*:\s*([^\n,]+)'
            attributes = re.findall(attr_pattern, entity_content)
            
            entities.append({
                'name': entity_name.strip(),
                'attributes': [{'name': a[0].strip(), 'type': a[1].strip()} for a in attributes]
            })
        
        return generate_direct_migrations_from_entities(entities, db_type)
        
    except Exception as e:
        logging.error(f"Error en fallback completo: {e}")
        return "-- Error: No se pudieron generar migraciones"

def improved_sql_generation_with_rag(chain, db_type, puml_file):
    """
    Versión mejorada que se enfoca exclusivamente en las entidades del PUML.
    """
    # Extraer entidades del archivo PUML
    entities = extract_entities_from_puml(puml_file)
    
    if not entities:
        logging.error("No se pudieron extraer entidades del archivo PUML")
        return generate_fallback_migrations(puml_file, db_type)
    
    # Crear prompt específico y enfocado
    focused_prompt = create_focused_prompt(entities, db_type)
    
    print("Generando migraciones SQL enfocadas...")
    try:
        response = chain.invoke(focused_prompt)
        
        # Validar y corregir las tablas generadas
        corrected_response = enforce_exact_entities(response, entities, db_type)
        
        # Validación final
        final_validation = validate_generated_tables(corrected_response, entities)
        
        if not final_validation['is_valid']:
            logging.warning(f"Aún hay discrepancias después de la corrección: {final_validation}")
            # Usar generación directa como último recurso
            return generate_direct_migrations_from_entities(entities, db_type)
        
        return corrected_response
        
    except Exception as e:
        logging.error(f"Error en generación mejorada: {e}")
        return generate_direct_migrations_from_entities(entities, db_type)

# === FUNCIONES DE PARSEO Y GUARDADO ===

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

# === FUNCIÓN MAIN MEJORADA ===

def main():
    # Configuración inicial
    db_type = input("Por favor, ingresa el tipo de base de datos (sqlite, mysql, postgres): ").strip().lower()
    if db_type not in ['sqlite', 'mysql', 'postgres']:
        print("Tipo de base de datos no válido.")
        return

    puml_file = input("Por favor, ingresa la ruta al archivo PUML (presiona Enter para usar 'schema.puml'): ").strip()
    if not puml_file:
        puml_file = "schema.puml"
    
    if not os.path.exists(puml_file):
        print(f"El archivo PUML no existe en la ruta {puml_file}.")
        return

    # Extraer entidades para mostrar al usuario
    entities = extract_entities_from_puml(puml_file)
    if not entities:
        print("❌ No se pudieron extraer entidades del archivo PUML.")
        return
    
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
            
            # Opción adicional: guardar diccionario como JSON
            save_json = input("¿Guardar diccionario como JSON? (s/n): ").strip().lower()
            if save_json == 's':
                json_filename = f"migrations_dict_{puml_basename}_{db_type}.json"
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(tables_dict, f, indent=2, ensure_ascii=False)
                print(f"✓ Diccionario guardado en: {json_filename}")
    else:
        print("❌ No se pudieron procesar las migraciones.")

if __name__ == "__main__":
    main()