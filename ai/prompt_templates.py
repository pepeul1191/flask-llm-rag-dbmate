# application/ai/prompt_templates.py
from langchain.prompts import PromptTemplate, ChatPromptTemplate

class PromptTemplates:
  """Plantillas de prompts para diferentes tareas"""
  
  @staticmethod
  def get_multi_query_prompt():
    """Prompt para el multi-query retriever"""
    return PromptTemplate(
      input_variables=["question"],
      template="""Eres un asistente especializado en diagramas UML y bases de datos. 
      Genera 3 versiones diferentes de la siguiente pregunta para mejorar la búsqueda de información relevante.
      
      Pregunta original: {question}
      
      Genera 3 variaciones diferentes:"""
    )
  
  @staticmethod
  def get_sql_generation_prompt():
    """Prompt para generación de SQL"""
    template = """Eres un experto en bases de datos y diagramas UML. 
Tu tarea es ANALIZAR el diagrama PUML proporcionado y GENERAR código SQL.

CONTEXTO del diagrama PUML:
{context}

INSTRUCCIONES para la pregunta: {question}

- Analiza las entidades (entity) y sus relaciones del diagrama
- Genera código SQL funcional y válido
- Especifica el tipo de base de datos objetivo
- Incluye todas las tablas, relaciones y constraints necesarios
- SÉ ESPECÍFICO y PRÁCTICO"""

    return ChatPromptTemplate.from_template(template=template)
  
  @staticmethod
  def get_migration_generation_prompt(db_type, puml_file, entities_summary):
    """Prompt específico para generación de migraciones"""
    return f"""
ANÁLISIS DE DIAGRAMA UML Y GENERACIÓN DE MIGRACIONES SQL

ARCHIVO: {puml_file}
TIPO DE BASE DE DATOS: {db_type.upper()}

ENTIDADES ENCONTRADAS EN EL DIAGRAMA:
{entities_summary}

INSTRUCCIONES ESPECÍFICAS:

1. ANALIZA cada entidad del diagrama UML y conviértela en una sentencia CREATE TABLE
2. USA el formato EXACTO de migración que se muestra a continuación
3. PRESERVA los nombres ORIGINALES de las entidades y atributos
4. GENERA código SQL VÁLIDO para {db_type.upper()}

FORMATO REQUERIDO para CADA tabla:

-- migrate:up

CREATE TABLE nombre_tabla (
  id TIPO_PRIMARY_KEY,
  columna1 TIPO_DATO,
  columna2 TIPO_DATO,
  PRIMARY KEY (id),
  FOREIGN KEY (columna_relacionada) REFERENCES tabla_relacionada(id)
);

-- migrate:down

DROP TABLE nombre_tabla;

REQUISITOS TÉCNICOS:
- Para {db_type.upper()}, usa tipos de datos apropiados
- Incluye PRIMARY KEY autoincremental para cada tabla
- Incluye FOREIGN KEYS basadas en las relaciones del diagrama
- Mantén los nombres ORIGINALES en inglés (NO traduzcas)
- Genera EXACTAMENTE una migración por cada entidad encontrada

RESPONDE ÚNICAMENTE con las sentencias SQL en el formato especificado, sin explicaciones.
"""