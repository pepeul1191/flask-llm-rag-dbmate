# 1.ingest pdf
# 2.extract text from pdf files and split in small chunks
# 3. send chunks to the embedding model
# 4. save the embedding to vector database
# 5. perform similarity search on the vector database to find similarities
# 6. retrive the similar documents and present them to the user

from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.document_loaders import OnlinePDFLoader

doc_path = "articulo.pdf"
model = "llama3.2"

# local pdf file
if doc_path:
  loader = UnstructuredPDFLoader(file_path=doc_path)
  data = loader.load()
  print("done loading")
else:
  print("upload a pdf file")

content = data[0].page_content
#print(content[:100])

# pdf ingestion

from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# split and chunk

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=300)
chunks = text_splitter.split_documents(data)
print("done splitting...")

#print(f"Number of chunks: {len(chunks)}")
#print(f"Example chunk: {chunks[0]}")

# add to vector database

import ollama

# ollma pull nomic-embed-text

vector_db = Chroma.from_documents(
  documents=chunks,
  embedding=OllamaEmbeddings(model="nomic-embed-text"),
  collection_name="simple-rag"
)

print("done adding to vector database...")

# retrival 
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnablePassthrough
from langchain.retrievers.multi_query import MultiQueryRetriever

llm = ChatOllama(model=model)

QUERY_PROMPT = PromptTemplate(
  input_variables=["question"],
  template="""Eres el tesista autor del documento y vas a explicar el contenido del documento de manera puntual (menos de 100 caracteres). Pregunta: {question}"""
)

retriver = MultiQueryRetriever.from_llm(
  vector_db.as_retriever(), llm, prompt=QUERY_PROMPT
)

# RAG prompt
template = """Responde la pregunta basándote SÓLO en el siguiente contexto: {context}
Pregunta: {question}"""

prompt = ChatPromptTemplate.from_template(template=template)

chain = (
  {"context": retriver, "question": RunnablePassthrough()}
  | prompt
  | llm
  | StrOutputParser()
)

res = chain.invoke(input=("qué aporte tenemos?"))
print(res)