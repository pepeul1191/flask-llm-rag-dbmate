# application/ai/llm_services.py
from langchain_ollama import ChatOllama, OllamaEmbeddings

MODEL_NAME = "llama3.2"
EMBEDDING_MODEL = "nomic-embed-text"

class LLMServices:
  """Servicios para interactuar con modelos LLM de Ollama"""
  
  @staticmethod
  def get_chat_model():
    """Obtiene el modelo de chat configurado"""
    return ChatOllama(model=MODEL_NAME)
  
  @staticmethod
  def get_embedding_model():
    """Obtiene el modelo de embeddings configurado"""
    return OllamaEmbeddings(model=EMBEDDING_MODEL)
  
  @staticmethod
  def get_available_models():
    """Retorna los modelos disponibles"""
    return {
      "chat_model": MODEL_NAME,
      "embedding_model": EMBEDDING_MODEL
    }