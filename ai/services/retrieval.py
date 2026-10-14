# ai/services/retrieval.py
import os
import logging
from langchain_ollama import ChatOllama
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ..prompts.templates import QUERY_PROMPT, CHAIN_PROMPT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración del LLM (GPU)
# ---------------------------------------------------------------------------
# Valores por defecto (pueden sobreescribirse con variables de entorno)
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.2")
TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))
NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
NUM_GPU = int(os.getenv("OLLAMA_NUM_GPU", "99"))     # 99 => forzar GPU
VERBOSE = os.getenv("OLLAMA_VERBOSE", "true").lower() == "true"


def create_llm() -> ChatOllama:
  """
  Instancia única de ChatOllama configurada para usar la GPU.

  Equivalente a:
    ChatOllama(
      model="llama3.2",
      temperature=0.2,
      num_ctx=2048,
      num_gpu=99,
      verbose=True
    )
  """
  logger.info(
    "Creating ChatOllama (model=%s, num_gpu=%s, num_ctx=%s)",
    MODEL_NAME, NUM_GPU, NUM_CTX
  )
  return ChatOllama(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    num_ctx=NUM_CTX,
    num_gpu=NUM_GPU,
    verbose=VERBOSE,
  )


# Alias retro-compatible por si algún módulo importa _crear_llm
_crear_llm = create_llm


# ---------------------------------------------------------------------------
# Chains
# ---------------------------------------------------------------------------
def create_retriever(vector_db):
  """Crea un retriever con múltiples variaciones de consulta (usa el LLM con GPU)."""
  llm = create_llm()
  retriever = MultiQueryRetriever.from_llm(
    vector_db.as_retriever(search_kwargs={"k": 5}),
    llm,
    prompt=QUERY_PROMPT
  )
  logger.info("Retriever created (MultiQuery + GPU LLM).")
  return retriever


def create_chain(retriever):
  """Cadena RAG: retriever + prompt + LLM (GPU) + parser."""
  llm = create_llm()
  chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | CHAIN_PROMPT
    | llm
    | StrOutputParser()
  )
  logger.info("RAG chain created successfully.")
  return chain


def create_direct_chain():
  """
  Cadena sin RAG (modo llm_only), usando la misma instancia GPU.
  El input debe ser un dict {"context": str, "question": str}.
  """
  llm = create_llm()
  chain = CHAIN_PROMPT | llm | StrOutputParser()
  logger.info("Direct chain (no RAG) created with GPU LLM.")
  return chain