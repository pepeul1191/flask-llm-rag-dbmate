# ai/services/retrieval.py
import logging
from langchain_ollama import ChatOllama
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ..prompts.templates import QUERY_PROMPT, CHAIN_PROMPT

MODEL_NAME = "llama3.2"
logger = logging.getLogger(__name__)


def create_retriever(vector_db):
  """Crea un retriever con múltiples variaciones de consulta."""
  llm = ChatOllama(model=MODEL_NAME)
  retriever = MultiQueryRetriever.from_llm(
    vector_db.as_retriever(search_kwargs={"k": 5}),
    llm,
    prompt=QUERY_PROMPT
  )
  logger.info("Retriever created.")
  return retriever


def create_chain(retriever):
  """Crea la cadena completa (retriever + prompt + LLM + parser)."""
  llm = ChatOllama(model=MODEL_NAME)
  chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | CHAIN_PROMPT
    | llm
    | StrOutputParser()
  )
  logger.info("Chain created successfully.")
  return chain