# application/ai/chain_services.py
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from .llm_services import LLMServices
from .prompt_templates import PromptTemplates

class ChainServices:
  """Servicios para crear y gestionar cadenas de LangChain"""
  
  @staticmethod
  def create_retriever(vector_db, search_k=5):
    """Crea un multi-query retriever para RAG"""
    llm = LLMServices.get_chat_model()
    prompt = PromptTemplates.get_multi_query_prompt()
    
    retriever = MultiQueryRetriever.from_llm(
      vector_db.as_retriever(search_kwargs={"k": search_k}),
      llm,
      prompt=prompt
    )
    
    return retriever
  
  @staticmethod
  def create_sql_generation_chain(retriever):
    """Crea la cadena RAG para generación de SQL"""
    llm = LLMServices.get_chat_model()
    prompt = PromptTemplates.get_sql_generation_prompt()
    
    chain = (
      {"context": retriever, "question": RunnablePassthrough()}
      | prompt
      | llm
      | StrOutputParser()
    )
    
    return chain
  
  @staticmethod
  def create_custom_rag_chain(retriever, custom_prompt):
    """Crea una cadena RAG personalizada"""
    llm = LLMServices.get_chat_model()
    
    chain = (
      {"context": retriever, "question": RunnablePassthrough()}
      | custom_prompt
      | llm
      | StrOutputParser()
    )
    
    return chain