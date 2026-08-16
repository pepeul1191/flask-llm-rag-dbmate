# ai/prompts/templates.py
from langchain.prompts import PromptTemplate, ChatPromptTemplate

# Plantilla para generar variaciones de preguntas (MultiQueryRetriever)
QUERY_PROMPT = PromptTemplate(
  input_variables=["question"],
  template="""Eres un asistente especializado en diagramas UML y bases de datos. 
  Genera 3 versiones diferentes de la siguiente pregunta para mejorar la búsqueda de información relevante.
  
  Pregunta original: {question}
  
  Genera 3 variaciones diferentes:"""
)

# Plantilla principal para la cadena RAG (generación de SQL)
CHAIN_TEMPLATE = """Eres un experto en bases de datos y diagramas UML. 
Tu tarea es ANALIZAR el diagrama PUML proporcionado y GENERAR código SQL.

CONTEXTO del diagrama PUML:
{context}

INSTRUCCIONES para la pregunta: {question}

- Analiza las entidades (entity) y sus relaciones del diagrama
- Genera código SQL funcional y válido
- Especifica el tipo de base de datos objetivo
- Incluye todas las tablas, relaciones y constraints necesarios
- SÉ ESPECÍFICO y PRÁCTICO"""

CHAIN_PROMPT = ChatPromptTemplate.from_template(template=CHAIN_TEMPLATE)