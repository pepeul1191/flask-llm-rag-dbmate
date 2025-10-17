from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnablePassthrough
from langchain.retrievers.multi_query import MultiQueryRetriever
import ollama
import logging
import os

# configure logging
logging.basicConfig(level=logging.INFO)

# constants
DOC_PATH = "articulo.pdf"
MODEL_NAME = "llama3.2"
EMBEDDING_MODEL = "nomic-embed-text"
VECTOR_STORE_NAME = "simple-rag"
PERSIST_DIRECTORY = "./chroma_db"  # Nueva carpeta para persistencia

def check_existing_vector_db():
    """Check if vector database already exists"""
    if os.path.exists(PERSIST_DIRECTORY):
        # Verificar que la colección existe y tiene documentos
        try:
            vector_db = Chroma(
                persist_directory=PERSIST_DIRECTORY,
                embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
                collection_name=VECTOR_STORE_NAME
            )
            # Verificar si hay documentos
            if vector_db._collection.count() > 0:
                logging.info("Found existing vector database.")
                return vector_db
        except Exception as e:
            logging.warning(f"Existing DB issue: {e}")
    return None

def ingest_pdf(doc_path):
    """Load PDF documents."""
    if os.path.exists(doc_path):
        loader = UnstructuredPDFLoader(file_path=doc_path)
        data = loader.load()
        logging.info("PDF loaded successfully.")
        return data
    else:
        logging.error(f"PDF file not found at path: {doc_path}")
        return None

def split_documents(documents):
    """Split documents into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=300)
    chunks = text_splitter.split_documents(documents)
    logging.info("Documents split into chunks.")
    return chunks

def create_vector_db(chunks):
    """Create a vector database from document chunks."""
    # pull the embedding model if not already available
    ollama.pull(EMBEDDING_MODEL)

    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
        collection_name=VECTOR_STORE_NAME,
        persist_directory=PERSIST_DIRECTORY  # ¡Esto es clave!
    )
    
    # Persistir la base de datos
    vector_db.persist()
    
    logging.info("Vector database created and persisted.")
    return vector_db

def load_vector_db():
    """Load existing vector database"""
    vector_db = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
        collection_name=VECTOR_STORE_NAME
    )
    logging.info("Vector database loaded from disk.")
    return vector_db

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

def create_chain(retriever):
    """Create the chain"""
    llm = ChatOllama(model=MODEL_NAME)
    
    template = """Responde la pregunta basándote SÓLO en el siguiente contexto: {context}
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

def main():
    # Paso 1: Verificar si ya existe la base de datos vectorial
    vector_db = check_existing_vector_db()
    
    if vector_db is None:
        # Procesar el PDF solo si no existe la DB
        logging.info("No existing vector DB found. Processing PDF...")
        data = ingest_pdf(DOC_PATH)
        if data is None:
            return

        chunks = split_documents(data)
        vector_db = create_vector_db(chunks)
    else:
        logging.info("Using existing vector database.")
    
    # Paso 2: Crear el retriever y la cadena (esto es rápido)
    retriever = create_retriever(vector_db)
    chain = create_chain(retriever)

    # Paso 3: Interactuar con el usuario
    question = 'XD'
    while question != '0':
        question = input("\nHaz tu pregunta sobre el documento (0 para salir): ")
        if question != '0':
            res = chain.invoke(input=question)
            print("\nRespuesta:")
            print(res)

if __name__ == "__main__":
    main()