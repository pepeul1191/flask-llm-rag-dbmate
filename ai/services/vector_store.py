# ai/services/vector_store.py
import os
import shutil
import logging
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

EMBEDDING_MODEL = "nomic-embed-text"
VECTOR_STORE_NAME = "puml-rag"
PERSIST_DIRECTORY = "./chroma_db"

logger = logging.getLogger(__name__)


def get_puml_file_hash(puml_path: str) -> int | None:
  """Calcula un hash simple del contenido del archivo PUML."""
  if os.path.exists(puml_path):
    with open(puml_path, 'r', encoding='utf-8') as f:
      return hash(f.read())
  return None


def should_recreate_vector_db(puml_file: str, vector_db) -> bool:
  """Determina si la base vectorial debe recrearse por cambios en el archivo."""
  if not vector_db:
    return True

  current_hash = get_puml_file_hash(puml_file)
  try:
    docs = vector_db.similarity_search("test", k=1)
    if docs and 'source_file_hash' in docs[0].metadata:
      stored_hash = docs[0].metadata.get('source_file_hash')
      return current_hash != stored_hash
  except:
    pass
  return True


def clear_vector_db() -> bool:
  """Elimina el directorio de la base vectorial de forma segura."""
  if os.path.exists(PERSIST_DIRECTORY):
    try:
      shutil.rmtree(PERSIST_DIRECTORY)
      logger.info("Cleared existing vector database.")
      return True
    except Exception as e:
      logger.error(f"Error clearing vector DB: {e}")
      try:
        import subprocess
        subprocess.run(['rm', '-rf', PERSIST_DIRECTORY], check=True)
        logger.info("Cleared vector database using alternative method.")
        return True
      except:
        logger.error("Failed to clear vector database.")
        return False
  return True


def check_existing_vector_db():
  """Carga la base vectorial existente si existe."""
  if os.path.exists(PERSIST_DIRECTORY):
    try:
      vector_db = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
        collection_name=VECTOR_STORE_NAME
      )
      if vector_db._collection.count() > 0:
        logger.info("Found existing vector database.")
        return vector_db
    except Exception as e:
      logger.warning(f"Existing DB issue: {e}")
  return None


def create_vector_db(chunks, puml_path: str):
  """Crea una nueva base vectorial a partir de los fragmentos."""
  if not clear_vector_db():
    logger.error("Failed to clear existing vector database. Creating in memory only.")
    return Chroma.from_documents(
      documents=chunks,
      embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
      collection_name=VECTOR_STORE_NAME
    )

  try:
    os.makedirs(PERSIST_DIRECTORY, exist_ok=True, mode=0o755)
    vector_db = Chroma.from_documents(
      documents=chunks,
      embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
      collection_name=VECTOR_STORE_NAME,
      persist_directory=PERSIST_DIRECTORY
    )
    vector_db.persist()
    logger.info(f"Vector database created and persisted for {puml_path}.")
    return vector_db
  except Exception as e:
    logger.error(f"Error creating persistent vector DB: {e}. Using in-memory fallback.")
    return Chroma.from_documents(
      documents=chunks,
      embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
      collection_name=VECTOR_STORE_NAME
    )


def load_vector_db():
  """Carga la base vectorial desde disco."""
  try:
    return Chroma(
      persist_directory=PERSIST_DIRECTORY,
      embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
      collection_name=VECTOR_STORE_NAME
    )
  except Exception as e:
    logger.error(f"Error loading vector DB: {e}")
    return None