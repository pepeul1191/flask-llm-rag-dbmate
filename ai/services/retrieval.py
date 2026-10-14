# ai/services/retrieval.py
import os
from langchain_ollama import ChatOllama
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ..prompts.templates import QUERY_PROMPT, CHAIN_PROMPT

MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.2")
TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))
NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
NUM_GPU = int(os.getenv("OLLAMA_NUM_GPU", "99"))
VERBOSE = os.getenv("OLLAMA_VERBOSE", "true").lower() == "true"


def create_llm() -> ChatOllama:
  return ChatOllama(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    num_ctx=NUM_CTX,
    num_gpu=NUM_GPU,
    verbose=VERBOSE,
  )


def create_retriever(vector_db, source_file: str | None = None):
  """
  Retriever que opcionalmente filtra por archivo fuente.
  Evita devolver chunks de PUMLs anteriores que pudieran quedar en disco.
  """
  search_kwargs = {"k": 5}
  if source_file:
    search_kwargs["filter"] = {"source_file": os.path.abspath(source_file)}

  base = vector_db.as_retriever(search_kwargs=search_kwargs)
  llm = create_llm()
  retriever = MultiQueryRetriever.from_llm(base, llm, prompt=QUERY_PROMPT)
  return retriever


def create_chain(retriever):
  llm = create_llm()
  return (
    {"context": retriever, "question": RunnablePassthrough()}
    | CHAIN_PROMPT
    | llm
    | StrOutputParser()
  )


def create_direct_chain():
  llm = create_llm()
  return CHAIN_PROMPT | llm | StrOutputParser()