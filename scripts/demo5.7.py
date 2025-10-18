import os
import logging
import re
import shutil
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

# Split the PUML document into chunks and convert to Document objects
def split_documents(content, puml_path):
    """Split PUML content into smaller chunks as Document objects."""
    # Calculate file hash for change detection
    file_hash = hash(content)
    
    # Split by lines and create chunks
    lines = content.splitlines()
    chunk_size = 20
    chunks = []
    
    for i in range(0, len(lines), chunk_size):
        chunk_lines = lines[i:i + chunk_size]
        chunk_text = "\n".join(chunk_lines)
        chunks.append(Document(
            page_content=chunk_text,
            metadata={
                "source": "puml_file", 
                "chunk_id": len(chunks),
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
    if os.path.exists(PERSIST_DIRECTORY):
        shutil.rmtree(PERSIST_DIRECTORY)
        logging.info("Cleared existing vector database.")
    
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
        collection_name=VECTOR_STORE_NAME,
        persist_directory=PERSIST_DIRECTORY
    )
    vector_db.persist()
    logging.info(f"Vector database created and persisted for {puml_path}.")
    return vector_db

# Load the vector database
def load_vector_db():
    """Load existing vector database."""
    vector_db = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
        collection_name=VECTOR_STORE_NAME
    )
    logging.info("Vector database loaded from disk.")
    return vector_db

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
        vector_db.as_retriever(search_kwargs={"k": 3}), 
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
Responde la pregunta basándote en el siguiente contexto del diagrama PUML:

{context}

Pregunta: {question}

Instrucciones:
- Genera código SQL válido y funcional
- Especifica el tipo de base de datos objetivo
- Incluye todas las tablas, relaciones y constraints necesarios"""

    prompt = ChatPromptTemplate.from_template(template=template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    logging.info("Chain created successfully.")
    return chain

# OPTIMIZED RAG VERSION - Genera migraciones en formato específico
def generate_sql_migrations_with_rag(chain, db_type, puml_file):
    """Generate SQL migrations in specific format using optimized RAG."""
    query = f"""
    Basado en el diagrama UML del archivo {puml_file}, genera archivos de migración SQL para {db_type.upper()} en el siguiente formato:

    Para CADA tabla, genera un bloque con este formato exacto:

    -- migrate:up

    CREATE TABLE nombre_tabla (
      columna1 TIPO_DATO RESTRICCIONES,
      columna2 TIPO_DATO RESTRICCIONES,
      FOREIGN KEY (columna) REFERENCES otra_tabla (id)
    );

    -- migrate:down

    DROP TABLE nombre_tabla;

    REQUISITOS:
    - Genera UN bloque completo por cada tabla del diagrama UML
    - Mantén los nombres de tablas y atributos originales del archivo .puml
    - Usa tipos de datos apropiados para {db_type}
    - Incluye claves primarias, foráneas y constraints necesarios
    - Usa el formato EXACTO mostrado arriba
    - Incluye todas las tablas del diagrama
    - Separa cada bloque de tabla con una línea en blanco

    Responde SOLO con los bloques de migración en el formato especificado, sin explicaciones adicionales.
    """
    
    response = chain.invoke(query)
    return response

def parse_migration_blocks(complete_migrations):
    """
    Parsea los bloques de migración y crea el diccionario de tablas.
    
    Args:
        complete_migrations (str): Migraciones completas en el formato especificado
        
    Returns:
        dict: Diccionario con tablas organizadas
    """
    # Patrón para encontrar cada bloque de migración completo
    pattern = r'-- migrate:up\s*(CREATE TABLE[^;]+;)\s*-- migrate:down\s*(DROP TABLE[^;]+;)'
    
    matches = re.findall(pattern, complete_migrations, re.IGNORECASE | re.DOTALL)
    
    tables_dict = {}
    
    for i, (create_stmt, drop_stmt) in enumerate(matches, 1):
        # Limpiar y formatear las sentencias
        clean_create = re.sub(r'\s+', ' ', create_stmt.strip())
        clean_drop = re.sub(r'\s+', ' ', drop_stmt.strip())
        
        tables_dict[i] = {
            'up': clean_create,
            'down': clean_drop,
            'complete_block': f"-- migrate:up\n\n{create_stmt.strip()}\n\n-- migrate:down\n\n{drop_stmt.strip()}"
        }
    
    return tables_dict

def extract_table_name(sql_statement):
    """
    Extrae el nombre de la tabla de una sentencia SQL.
    
    Args:
        sql_statement (str): Sentencia SQL (CREATE TABLE o DROP TABLE)
        
    Returns:
        str: Nombre de la tabla
    """
    # Patrón para CREATE TABLE y DROP TABLE
    pattern = r'(?:CREATE|DROP) TABLE\s+(?:IF NOT EXISTS\s+|IF EXISTS\s+)?([^\s(;]+)'
    match = re.search(pattern, sql_statement, re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    return None

# Main logic
def main():
    # Paso 1: Ingresar el tipo de base de datos
    db_type = input("Por favor, ingresa el tipo de base de datos (sqlite, mysql, postgres): ").strip().lower()
    if db_type not in ['sqlite', 'mysql', 'postgres']:
        print("Tipo de base de datos no válido. Selecciona entre 'sqlite', 'mysql', 'postgres'.")
        return

    # Paso 2: Ingresar el archivo PUML
    puml_file = input("Por favor, ingresa la ruta al archivo PUML (presiona Enter para usar 'schema.puml'): ").strip()
    
    if not puml_file:
        puml_file = "schema.puml"
    
    if not os.path.exists(puml_file):
        print(f"El archivo PUML no existe en la ruta {puml_file}.")
        return

    # Paso 3: Verificar y gestionar la base vectorial
    vector_db = check_existing_vector_db()
    
    # Check if we need to recreate the vector DB
    if should_recreate_vector_db(puml_file, vector_db):
        print("Creando nueva base de datos vectorial...")
        # Procesar el archivo PUML y crear la base vectorial
        content = ingest_puml(puml_file)
        if not content:
            return
        
        # Dividir el contenido en fragmentos
        chunks = split_documents(content, puml_file)
        
        # Crear la base de datos vectorial
        vector_db = create_vector_db(chunks, puml_file)
    else:
        print("Usando base de datos vectorial existente.")
        logging.info("Usando base de datos vectorial existente.")

    # Crear el retriever y la cadena
    retriever = create_retriever(vector_db)
    chain = create_chain(retriever)

    # Paso 4: Generar las migraciones SQL
    print(f"Generando migraciones SQL para {puml_file}...")

    # Usar RAG optimizado para el formato específico
    complete_migrations = generate_sql_migrations_with_rag(chain, db_type, puml_file)

    # Mostrar las migraciones completas generadas
    print("\n" + "="*60)
    print(f"MIGRACIONES SQL GENERADAS PARA: {puml_file}")
    print("="*60)
    print(complete_migrations)

    # Paso 5: Parsear y organizar en diccionario
    print("\n" + "="*60)
    print("ORGANIZANDO EN DICCIONARIO:")
    print("="*60)
    
    tables_dict = parse_migration_blocks(complete_migrations)
    
    if tables_dict:
        print(f"Se procesaron {len(tables_dict)} tablas:\n")
        
        for key, table_data in tables_dict.items():
            table_name = extract_table_name(table_data['up'])
            print(f"Tabla {key} ({table_name}):")
            print(f"  UP:   {table_data['up']}")
            print(f"  DOWN: {table_data['down']}")
            print("-" * 80)
    else:
        print("No se pudieron parsear las migraciones del formato generado.")
        # Fallback: buscar CREATE TABLE individuales
        print("Usando método de extracción alternativa...")
        create_tables = re.findall(r'CREATE TABLE[^;]+;', complete_migrations, re.IGNORECASE | re.DOTALL)
        tables_dict = {}
        
        for i, create_stmt in enumerate(create_tables, 1):
            table_name = extract_table_name(create_stmt)
            drop_stmt = f"DROP TABLE {table_name};" if table_name else "-- Error: nombre no extraído"
            
            # Crear bloque completo en el formato requerido
            complete_block = f"-- migrate:up\n\n{create_stmt.strip()}\n\n-- migrate:down\n\n{drop_stmt}"
            
            tables_dict[i] = {
                'up': create_stmt.strip(),
                'down': drop_stmt,
                'complete_block': complete_block
            }
            
            print(f"Tabla {i} ({table_name}):")
            print(f"  UP:   {tables_dict[i]['up']}")
            print(f"  DOWN: {tables_dict[i]['down']}")
            print("-" * 80)

    # Paso 6: Guardar archivos
    save_file = input("\n¿Guardar las migraciones en archivos? (s/n): ").strip().lower()
    if save_file == 's':
        # Create directory name based on PUML file
        puml_basename = os.path.splitext(os.path.basename(puml_file))[0]
        
        # Guardar migraciones completas en un solo archivo
        '''
        complete_filename = f"complete_migrations_{puml_basename}_{db_type}.sql"
        with open(complete_filename, 'w', encoding='utf-8') as f:
            f.write(f"-- Migraciones generadas desde: {puml_file}\n")
            f.write(f"-- Tipo de base de datos: {db_type}\n")
            f.write(f"-- Fecha: {import datetime; datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(complete_migrations)
        print(f"✓ Migraciones completas guardadas en: {complete_filename}")
        '''
        # Guardar cada migración en archivo individual
        migrations_dir = f"migrations_{puml_basename}_{db_type}"
        os.makedirs(migrations_dir, exist_ok=True)
        
        import datetime
        base_timestamp = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

        for key, table_data in tables_dict.items():
            table_name = extract_table_name(table_data['up'])
            if table_name:
                # Nombre de archivo con timestamp para orden de migración
                timestamp = str(base_timestamp + key)
                migration_filename = f"{migrations_dir}/{timestamp}_create_{table_name}.sql"

                with open(migration_filename, 'w', encoding='utf-8') as f:
                    f.write(table_data['complete_block'])
                
                print(f"✓ Migración {key} ({table_name}) guardada en: {migration_filename}")

        # Opción adicional: guardar diccionario como JSON
        save_json = input("¿Guardar diccionario como JSON? (s/n): ").strip().lower()
        if save_json == 's':
            import json
            json_filename = f"migrations_dict_{puml_basename}_{db_type}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(tables_dict, f, indent=2, ensure_ascii=False)
            print(f"✓ Diccionario guardado en: {json_filename}")

if __name__ == "__main__":
    main()