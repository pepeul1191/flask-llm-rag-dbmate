# 1.ingest pdf
# 2.extract text from pdf files and split in small chunks
# 3. send chunks to the embedding model
# 4. save the embedding to vector database
# 5. perform similarity search on the vector database to find similarities
# 6. retrive the similar documents and present them to the user

from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.document_loaders import OnlinePDFLoader
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
    collection_name=VECTOR_STORE_NAME
  )

  logging.info("Vector database created.")
  return vector_db

def create_retriever(vector_db, llm):
  """Create a multi-query retriever."""
  llm = ChatOllama(model=MODEL_NAME)

  QUERY_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""Eres el tesista autor del documento y vas a explicar el contenido del documento de manera puntual (menos de 100 caracteres). Pregunta: {question}"""
  )

  retriver = MultiQueryRetriever.from_llm(
    vector_db.as_retriever(), llm, prompt=QUERY_PROMPT
  )

  logging.info("Retriever created.")
  return retriver

def create_chain(retriever, llm):
  """Create the chain"""
  # RAG prompt
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
  data = ingest_pdf(DOC_PATH)
  if data is None:
    return

  chunks = split_documents(data)

  vector_db = create_vector_db(chunks)

  llm = ChatOllama(model=MODEL_NAME)

  retriever = create_retriever(vector_db, llm)

  chain = create_chain(retriever, llm)

  question = "qué aporte tenemos?"

  res = chain.invoke(input=question)
  print("Response:")
  print(res)

if __name__ == "__main__":
  main()








