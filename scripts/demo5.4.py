import os
import logging
import re
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
def split_documents(content):
    """Split PUML content into smaller chunks as Document objects."""
    # Split by lines and create chunks
    lines = content.splitlines()
    chunk_size = 20  # Reduced for better context
    chunks = []
    
    for i in range(0, len(lines), chunk_size):
        chunk_lines = lines[i:i + chunk_size]
        chunk_text = "\n".join(chunk_lines)
        # Create Document object with metadata
        chunks.append(Document(
            page_content=chunk_text,
            metadata={"source": "puml_file", "chunk_id": len(chunks)}
        ))
    
    logging.info(f"PUML content split into {len(chunks)} chunks.")
    return chunks

# Create a vector database from PUML content
def create_vector_db(chunks):
    """Create a vector database from PUML content chunks."""
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
        collection_name=VECTOR_STORE_NAME,
        persist_directory=PERSIST_DIRECTORY
    )
    vector_db.persist()
    logging.info("Vector database created and persisted.")
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
- Incluye todas las tablas, relaciones y constraints necesarios
- Proporciona una explicación breve del esquema"""

    prompt = ChatPromptTemplate.from_template(template=template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    logging.info("Chain created successfully.")
    return chain

# Function to ask the LLM to generate the SQL schema based on the PUML and DB type
def generate_sql_schema_via_llm(schema, db_type="sqlite"):
    """
    Use LLM to generate the SQL schema based on the PUML schema and database type.
    """
    prompt = f"""
    Eres un experto en bases de datos y diagramas UML. Tienes la siguiente información de un diagrama UML en formato PUML:

    {schema}

    El tipo de base de datos es: {db_type}

    Genera el esquema SQL correspondiente para {db_type.upper()} considerando:

    1. Usa la sintaxis correcta para {db_type}
    2. Utiliza los tipos de datos apropiados
    3. Incluye claves primarias y foráneas
    4. Considera las relaciones entre tablas
    5. Incluye constraints necesarios

    Responde SOLO con el código SQL, sin explicaciones adicionales.
    """

    llm = ChatOllama(model=MODEL_NAME)
    response = llm.invoke(prompt)
    
    return response.content

# Enhanced version using RAG chain
def generate_sql_schema_with_rag(chain, db_type):
    """Generate SQL schema using the RAG chain for better context."""
    query = f"""
    Genera un esquema SQL completo para {db_type} basado en el diagrama UML proporcionado.
    Incluye:
    - Los nombres de las tablas y atributos se deben de mantener originales al archivo .puml
    - Definición de tablas
    - Claves primarias y foráneas
    - Tipos de datos apropiados para {db_type}
    - Constraints necesarios
    - Relaciones entre tablas
    - No incluir indices adicionales
    """
    
    response = chain.invoke(query)
    return response

def extract_create_tables(sql_schema):
    """
    Extrae todas las sentencias CREATE TABLE del esquema SQL y las devuelve en una lista.
    
    Args:
        sql_schema (str): El esquema SQL completo como string
        
    Returns:
        list: Lista de strings con cada sentencia CREATE TABLE
    """
    # Patrón regex para encontrar CREATE TABLE (maneja múltiples líneas)
    pattern = r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?[^;]+;'
    
    # Encontrar todas las coincidencias
    create_tables = re.findall(pattern, sql_schema, re.IGNORECASE | re.DOTALL)
    
    # Limpiar y formatear cada sentencia
    cleaned_tables = []
    for table in create_tables:
        # Limpiar espacios en blanco excesivos y saltos de línea múltiples
        cleaned = re.sub(r'\s+', ' ', table.strip())
        cleaned_tables.append(cleaned)
    
    return cleaned_tables

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

    # Paso 3: Verificar si ya existe la base vectorial
    vector_db = check_existing_vector_db()
    
    if not vector_db:
        # Procesar el archivo PUML y crear la base vectorial
        content = ingest_puml(puml_file)
        if not content:
            return
        
        # Dividir el contenido en fragmentos
        chunks = split_documents(content)
        
        # Crear la base de datos vectorial
        vector_db = create_vector_db(chunks)
    else:
        logging.info("Usando base de datos vectorial existente.")

    # Crear el retriever y la cadena
    retriever = create_retriever(vector_db)
    chain = create_chain(retriever)

    # Paso 4: Generar el esquema SQL
    print("Generando esquema SQL...")

    # Opción 1: Usar RAG para mejor contexto
    use_rag = input("¿Usar búsqueda mejorada con RAG? (s/n): ").strip().lower()
    
    if use_rag == 's':
        sql_schema = generate_sql_schema_with_rag(chain, db_type)
    else:
        # Opción 2: Método directo
        content = ingest_puml(puml_file)
        sql_schema = generate_sql_schema_via_llm(content, db_type)

    # Mostrar el SQL generado
    print("\n" + "="*50)
    print("ESQUEMA SQL GENERADO:")
    print("="*50)
    print(sql_schema)

    # Paso 5: Extraer y mostrar las tablas CREATE TABLE
    print("\n" + "="*50)
    print("TABLAS EXTRAÍDAS:")
    print("="*50)
    
    create_tables = extract_create_tables(sql_schema)
    
    if create_tables:
        print(f"Se encontraron {len(create_tables)} tablas:\n")
        for i, table in enumerate(create_tables, 1):
            print(f"Tabla {i}:")
            print(table)
            print("-" * 80)
    else:
        print("No se encontraron sentencias CREATE TABLE en el esquema generado.")

    # Opción para guardar en archivo
    save_file = input("\n¿Guardar el esquema en un archivo? (s/n): ").strip().lower()
    if save_file == 's':
        filename = f"schema_{db_type}.sql"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(sql_schema)
        print(f"Esquema guardado en: {filename}")
        
        # También guardar las tablas individuales si el usuario quiere
        save_tables = input("¿Guardar las tablas individualmente? (s/n): ").strip().lower()
        if save_tables == 's' and create_tables:
            for i, table in enumerate(create_tables, 1):
                table_filename = f"tabla_{i}_{db_type}.sql"
                with open(table_filename, 'w', encoding='utf-8') as f:
                    f.write(table)
                print(f"Tabla {i} guardada en: {table_filename}")

if __name__ == "__main__":
    main()