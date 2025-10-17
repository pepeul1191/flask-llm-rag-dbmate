import os
import logging
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import UnstructuredTextLoader
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
PUML_FILE_PATH = "schema.puml"
MODEL_NAME = "llama3.2"
EMBEDDING_MODEL = "nomic-embed-text"
VECTOR_STORE_NAME = "puml-rag"
PERSIST_DIRECTORY = "./chroma_db"  # Directory for storing vector DB

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

# Split the PUML document into chunks
def split_documents(content):
    """Split PUML content into smaller chunks."""
    # Basic split by lines (this can be enhanced for more granular chunks)
    lines = content.splitlines()
    chunk_size = 1200
    chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]
    logging.info("PUML content split into chunks.")
    return chunks

# Create a vector database from PUML content
def create_vector_db(chunks):
    """Create a vector database from PUML content chunks."""
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
        collection_name=VECTOR_STORE_NAME,
        persist_directory=PERSIST_DIRECTORY  # Store DB persistently
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
        template="""Eres el tesista autor del documento y vas a explicar el contenido del documento de manera puntual (menos de 100 caracteres). Pregunta: {question}"""
    )

    retriever = MultiQueryRetriever.from_llm(
        vector_db.as_retriever(), llm, prompt=QUERY_PROMPT
    )

    logging.info("Retriever created.")
    return retriever

# Create the chain for LLM + retrieval
def create_chain(retriever):
    """Create the chain to process queries."""
    llm = ChatOllama(model=MODEL_NAME)
    
    template = """Responde la pregunta basándote en el siguiente contexto: {context}
Pregunta: {question}"""

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
    # Create a prompt for the LLM to generate the SQL schema based on user input
    prompt = f"""
    Tienes la siguiente información de un diagrama UML que describe una base de datos:

    {schema}

    El tipo de base de datos es {db_type}. Genera el esquema SQL correspondiente para este tipo de base de datos.

    Asegúrate de tener en cuenta las siguientes consideraciones:
    - Para {db_type}, usa la sintaxis correcta para la definición de tipos de datos, claves primarias y foráneas.
    - Para {db_type}, utiliza los tipos de datos apropiados (por ejemplo, `INTEGER`, `TEXT`, `VARCHAR`, `BOOLEAN`, etc.).
    """

    # Enviar el prompt al LLM para que genere el SQL
    llm = ChatOllama(model=MODEL_NAME)
    response = llm.call(prompt)
    
    # Devuelve la respuesta generada por el modelo
    return response

# Main logic
def main():
    # Paso 1: Ingresar el tipo de base de datos
    db_type = input("Por favor, ingresa el tipo de base de datos (sqlite, mysql, postgres): ").strip().lower()
    if db_type not in ['sqlite', 'mysql', 'postgres']:
        print("Tipo de base de datos no válido. Selecciona entre 'sqlite', 'mysql', 'postgres'.")
        return

    # Paso 2: Ingresar el archivo PUML
    puml_file = input("Por favor, ingresa la ruta al archivo PUML: ").strip()
    
    if not os.path.exists(puml_file):
        print(f"El archivo PUML no existe en la ruta {puml_file}.")
        return

    # Paso 3: Procesar el archivo PUML y obtener el esquema
    content = ingest_puml(puml_file)
    if not content:
        return
    
    # Paso 4: Dividir el contenido en fragmentos más pequeños
    chunks = split_documents(content)
    
    # Crear la base de datos vectorial
    vector_db = create_vector_db(chunks)
    
    # Crear el retriever
    retriever = create_retriever(vector_db)
    chain = create_chain(retriever)

    # Paso 5: Preguntar al modelo para generar el SQL
    print("Generando esquema SQL...")

    # Consultar al modelo para generar el SQL
    sql_schema = generate_sql_schema_via_llm(content, db_type)

    # Mostrar el SQL generado
    print("\nEsquema SQL generado:")
    print(sql_schema)

if __name__ == "__main__":
    main()
