# application/ai/rag_services.py
import os
import logging
import shutil
from langchain_community.vectorstores import Chroma

from .llm_services import LLMServices
from .agents.data_processor import DataProcessor

VECTOR_STORE_NAME = "puml-rag"
PERSIST_DIRECTORY = "./chroma_db"

class RAGServices:
  """Servicios para el sistema RAG (Retrieval-Augmented Generation)"""
  
  @staticmethod
  def get_puml_file_hash(puml_path):
    """Calcula un hash del archivo PUML para detectar cambios"""
    if os.path.exists(puml_path):
      with open(puml_path, 'r', encoding='utf-8') as file:
        content = file.read()
      return hash(content)
    return None
  
  @staticmethod
  def should_recreate_vector_db(puml_file, vector_db):
    """Verifica si se debe recrear la base vectorial por cambios en el archivo"""
    if not vector_db:
      return True
    
    current_hash = RAGServices.get_puml_file_hash(puml_file)
    
    try:
      docs = vector_db.similarity_search("test", k=1)
      if docs and 'source_file_hash' in docs[0].metadata:
        stored_hash = docs[0].metadata.get('source_file_hash')
        return current_hash != stored_hash
    except:
      pass
    
    return True
  
  @staticmethod
  def clear_vector_db():
    """Limpia de forma segura el directorio de la base vectorial"""
    if os.path.exists(PERSIST_DIRECTORY):
      try:
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
        try:
          import subprocess
          subprocess.run(['rm', '-rf', PERSIST_DIRECTORY], check=True)
          logging.info("Cleared vector database using alternative method.")
          return True
        except:
          logging.error("Failed to clear vector database.")
          return False
    return True
  
  @staticmethod
  def check_existing_vector_db():
    """Verifica si existe una base de datos vectorial"""
    if os.path.exists(PERSIST_DIRECTORY):
      try:
        vector_db = Chroma(
          persist_directory=PERSIST_DIRECTORY,
          embedding_function=LLMServices.get_embedding_model(),
          collection_name=VECTOR_STORE_NAME
        )
        if vector_db._collection.count() > 0:
          logging.info("Found existing vector database.")
          return vector_db
      except Exception as e:
        logging.warning(f"Existing DB issue: {e}")
    return None
  
  @staticmethod
  def create_vector_db_from_puml(puml_file):
    """Crea una base de datos vectorial a partir de un archivo PUML"""
    if not os.path.exists(puml_file):
      logging.error(f"PUML file not found at path: {puml_file}")
      return None
    
    with open(puml_file, 'r', encoding='utf-8') as file:
      content = file.read()
    
    chunks = DataProcessor.split_puml_content(content, puml_file)
    
    if not RAGServices.clear_vector_db():
      logging.error("Failed to clear existing vector database. Creating in memory only.")
      vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=LLMServices.get_embedding_model(),
        collection_name=VECTOR_STORE_NAME
      )
      logging.info("In-memory vector database created.")
      return vector_db
    
    try:
      os.makedirs(PERSIST_DIRECTORY, exist_ok=True, mode=0o755)
      
      vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=LLMServices.get_embedding_model(),
        collection_name=VECTOR_STORE_NAME,
        persist_directory=PERSIST_DIRECTORY
      )
      vector_db.persist()
      logging.info(f"Vector database created and persisted for {puml_file}.")
      return vector_db
    except Exception as e:
      logging.error(f"Error creating persistent vector DB: {e}. Using in-memory fallback.")
      vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=LLMServices.get_embedding_model(),
        collection_name=VECTOR_STORE_NAME
      )
      logging.info("In-memory vector database created as fallback.")
      return vector_db
  
  @staticmethod
  def load_vector_db():
    """Carga una base de datos vectorial existente"""
    try:
      vector_db = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=LLMServices.get_embedding_model(),
        collection_name=VECTOR_STORE_NAME
      )
      logging.info("Vector database loaded from disk.")
      return vector_db
    except Exception as e:
      logging.error(f"Error loading vector DB: {e}")
      return None
  
  @staticmethod
  def similarity_search(vector_db, query, k=3):
    """Realiza búsqueda por similitud en la base vectorial"""
    try:
      results = vector_db.similarity_search(query, k=k)
      return results
    except Exception as e:
      logging.error(f"Error in similarity search: {e}")
      return []
  
  @staticmethod
  def get_vector_db_info(vector_db):
    """Obtiene información sobre la base de datos vectorial"""
    try:
      count = vector_db._collection.count()
      return {
        "document_count": count,
        "collection_name": VECTOR_STORE_NAME,
        "persist_directory": PERSIST_DIRECTORY
      }
    except:
      return {"error": "Could not retrieve vector DB info"}