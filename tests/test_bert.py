import os
import logging
import re
import shutil
import datetime
import json
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
MODEL_NAME = "bert-base-uncased"
VECTOR_STORE_NAME = "puml-rag"
PERSIST_DIRECTORY = "./chroma_db"

class BERTRAGModel:
    """Modelo BERT mejorado para RAG que realmente usa el contexto recuperado"""
    
    def __init__(self, model_name="bert-base-uncased"):
        self.model_name = model_name
        
        # Cargar modelo para generación de texto (BERT no es bueno para esto,
        # pero usaremos un modelo seq2seq basado en BERT)
        try:
            # Intentar cargar un modelo T5 pequeño que es mejor para generación
            self.generation_model = pipeline(
                "text2text-generation",
                model="t5-small",  # Modelo pequeño pero bueno para generación
                tokenizer="t5-small"
            )
            self.use_t5 = True
            print("✅ Usando modelo T5 para generación")
        except:
            # Fallback a BERT para QA
            self.qa_pipeline = pipeline(
                "question-answering",
                model=model_name,
                tokenizer=model_name
            )
            self.use_t5 = False
            print("⚠️  Usando BERT para QA (generación limitada)")
        
    def invoke(self, prompt):
        """Generar SQL usando el contexto proporcionado por RAG"""
        try:
            # Extraer el contexto de RAG del prompt
            # El prompt viene en formato: "CONTEXTO: ...\n\nPREGUNTA: ..."
            if "CONTEXTO" in prompt and "PREGUNTA" in prompt:
                # Dividir en contexto y pregunta
                parts = prompt.split("PREGUNTA:")
                if len(parts) >= 2:
                    context_part = parts[0].replace("CONTEXTO:", "").strip()
                    question = parts[1].strip()
                    
                    # Limpiar y preparar el contexto
                    context_lines = context_part.split('\n')
                    clean_context = []
                    
                    # Filtrar y limpiar el contexto
                    for line in context_lines:
                        if line.strip() and len(line.strip()) > 10:  # Filtrar líneas muy cortas
                            clean_context.append(line.strip())
                    
                    context = "\n".join(clean_context[:20])  # Limitar a 20 líneas
                    
                    print(f"📊 Contexto RAG recibido: {len(context.split())} palabras")
                    print(f"❓ Pregunta: {question[:100]}...")
                    
                    if self.use_t5:
                        # Usar T5 para generación con el contexto
                        return self._generate_with_t5(context, question)
                    else:
                        # Usar BERT para QA
                        return self._generate_with_bert(context, question)
            
            # Si no hay formato claro, procesar todo como contexto
            print("⚠️  No se encontró formato CONTEXTO/PREGUNTA, procesando como texto completo")
            
            if self.use_t5:
                return self._generate_with_t5(prompt[:1000], "Generate SQL CREATE TABLE statements")
            else:
                return self._generate_with_bert(prompt[:512], "Generate SQL")
                
        except Exception as e:
            logging.error(f"Error en invoke: {str(e)}")
            return f"-- Error generando SQL: {str(e)}\n-- Usando generación basada en reglas..."
    
    def _generate_with_t5(self, context, question):
        """Generar usando T5 (mejor para generación)"""
        # Preparar prompt para T5
        input_text = f"Generate SQL CREATE TABLE statements based on this UML diagram context:\n\nContext: {context[:500]}\n\nQuestion: {question}"
        
        try:
            result = self.generation_model(
                input_text,
                max_length=500,
                min_length=100,
                do_sample=True,
                temperature=0.7,
                top_p=0.9
            )
            
            generated_text = result[0]['generated_text']
            
            # Mejorar el SQL generado
            improved_sql = self._improve_generated_sql(generated_text, context)
            
            return improved_sql
            
        except Exception as e:
            logging.error(f"Error con T5: {e}")
            return self._generate_fallback_sql(context)
    
    def _generate_with_bert(self, context, question):
        """Generar usando BERT QA (limitado pero funcional)"""
        try:
            # Hacer múltiples preguntas a BERT para construir el SQL
            sql_parts = []
            
            # Pregunta 1: ¿Qué entidades hay?
            entities_answer = self._ask_bert(context, "What are the entity names in this UML diagram?")
            entities = self._extract_entities(entities_answer)
            
            if not entities:
                entities = self._extract_entities_from_context(context)
            
            print(f"🔍 Entidades encontradas por BERT: {len(entities)}")
            
            # Para cada entidad, preguntar por sus atributos
            for entity in entities[:10]:  # Limitar a 10 entidades
                # Preguntar por atributos
                attr_question = f"What are the attributes of entity {entity}?"
                attr_answer = self._ask_bert(context, attr_question)
                
                # Preguntar por tipo de datos
                type_question = f"What are the data types for attributes of {entity}?"
                type_answer = self._ask_bert(context, type_question)
                
                # Generar CREATE TABLE para esta entidad
                create_sql = self._generate_table_sql(entity, attr_answer, type_answer)
                if create_sql:
                    sql_parts.append(create_sql)
            
            if sql_parts:
                return "\n\n".join(sql_parts)
            else:
                return self._generate_fallback_sql(context)
                
        except Exception as e:
            logging.error(f"Error con BERT QA: {e}")
            return self._generate_fallback_sql(context)
    
    def _ask_bert(self, context, question):
        """Hacer una pregunta a BERT"""
        if not hasattr(self, 'qa_pipeline') or self.qa_pipeline is None:
            return ""
        
        try:
            result = self.qa_pipeline({
                'context': context[:512],
                'question': question[:128]
            })
            return result['answer']
        except:
            return ""
    
    def _extract_entities(self, text):
        """Extraer nombres de entidades del texto"""
        # Buscar palabras que parezcan nombres de entidades (mayúsculas, sustantivos)
        words = re.findall(r'\b[A-Z][a-z]+\b|\b[A-Z]+\b', text)
        
        # Filtrar palabras comunes
        common_words = {'THE', 'AND', 'FOR', 'WITH', 'THAT', 'THIS', 'HAVE', 'FROM'}
        entities = [word for word in words if word.upper() not in common_words and len(word) > 2]
        
        return list(set(entities))  # Eliminar duplicados
    
    def _extract_entities_from_context(self, context):
        """Extraer entidades directamente del contexto usando regex"""
        patterns = [
            r'entity\s+(\w+)',
            r'class\s+(\w+)',
            r'table\s+(\w+)',
            r'Entity\s+(\w+)',
            r'CREATE TABLE\s+(\w+)',
            r'TABLE\s+(\w+)\s*\(',
        ]
        
        entities = []
        for pattern in patterns:
            found = re.findall(pattern, context, re.IGNORECASE)
            entities.extend(found)
        
        return list(set(entities))
    
    def _generate_table_sql(self, entity_name, attributes_text, types_text):
        """Generar SQL para una tabla específica"""
        # Extraer atributos y tipos
        attrs = []
        
        # Buscar patrones comunes
        attr_patterns = [
            r'(\w+)\s*:\s*(\w+)',
            r'(\w+)\s+(\w+)',
            r'attribute\s+(\w+)\s+(\w+)',
            r'(\w+)\s+of\s+type\s+(\w+)',
        ]
        
        for pattern in attr_patterns:
            matches = re.findall(pattern, attributes_text + " " + types_text, re.IGNORECASE)
            for attr_name, attr_type in matches:
                if attr_name.lower() not in ['id', 'the', 'and', 'for']:
                    attrs.append((attr_name, attr_type))
        
        # Si no se encontraron atributos, usar algunos por defecto
        if not attrs:
            attrs = [('name', 'VARCHAR'), ('description', 'TEXT')]
        
        # Construir columnas SQL
        columns = ["id INT PRIMARY KEY AUTO_INCREMENT"]
        
        for attr_name, attr_type in attrs:
            sql_type = self._map_to_sql_type(attr_type)
            columns.append(f"    {attr_name} {sql_type}")
        
        # Añadir timestamps
        columns.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        columns.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        
        columns_sql = ",\n".join(columns)
        
        return f"""-- migrate:up

CREATE TABLE {entity_name} (
{columns_sql}
);

-- migrate:down

DROP TABLE {entity_name};"""
    
    def _map_to_sql_type(self, type_str):
        """Mapear tipo a SQL"""
        type_str = type_str.lower()
        
        mappings = {
            'string': 'VARCHAR(255)',
            'str': 'VARCHAR(255)',
            'text': 'TEXT',
            'int': 'INT',
            'integer': 'INT',
            'number': 'INT',
            'float': 'FLOAT',
            'double': 'DOUBLE',
            'decimal': 'DECIMAL(10,2)',
            'bool': 'BOOLEAN',
            'boolean': 'BOOLEAN',
            'date': 'DATE',
            'datetime': 'DATETIME',
            'timestamp': 'TIMESTAMP',
            'time': 'TIME',
            'json': 'JSON',
        }
        
        for key, value in mappings.items():
            if key in type_str:
                return value
        
        return 'VARCHAR(255)'
    
    def _improve_generated_sql(self, sql_text, context):
        """Mejorar el SQL generado basándose en el contexto"""
        # Buscar entidades en el contexto que no estén en el SQL
        context_entities = self._extract_entities_from_context(context)
        sql_entities = self._extract_entities_from_context(sql_text)
        
        missing_entities = [e for e in context_entities if e not in sql_entities]
        
        # Si faltan entidades, añadirlas
        if missing_entities and len(sql_entities) < len(context_entities):
            additional_sql = []
            for entity in missing_entities[:5]:  # Máximo 5 adicionales
                additional_sql.append(self._generate_basic_table(entity))
            
            if additional_sql:
                sql_text += "\n\n" + "\n\n".join(additional_sql)
        
        return sql_text
    
    def _generate_basic_table(self, entity_name):
        """Generar una tabla básica"""
        return f"""-- migrate:up

CREATE TABLE {entity_name} (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- migrate:down

DROP TABLE {entity_name};"""
    
    def _generate_fallback_sql(self, context):
        """Generación de fallback cuando todo lo demás falla"""
        entities = self._extract_entities_from_context(context)
        
        if not entities:
            entities = ['users', 'products', 'orders']  # Tablas por defecto
        
        sql_parts = []
        for entity in entities[:8]:  # Máximo 8 tablas
            sql_parts.append(self._generate_basic_table(entity))
        
        return "\n\n".join(sql_parts)
    
    def __call__(self, messages):
        """Para compatibilidad con LangChain"""
        if isinstance(messages, list) and messages:
            # Convertir mensajes a prompt
            prompt_parts = []
            for msg in messages[-3:]:  # Últimos 3 mensajes
                if hasattr(msg, 'content'):
                    prompt_parts.append(msg.content)
                else:
                    prompt_parts.append(str(msg))
            
            prompt = "\n\n".join(prompt_parts)
        else:
            prompt = str(messages)
        
        return self.invoke(prompt)


# Resto del código con RAG real

def get_puml_file_hash(puml_path):
    """Calculate a simple hash of the PUML file to detect changes."""
    if os.path.exists(puml_path):
        with open(puml_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return hash(content)
    return None


def should_recreate_vector_db(puml_file, vector_db):
    """Check if vector DB should be recreated based on file changes."""
    if not vector_db:
        return True
    
    current_hash = get_puml_file_hash(puml_file)
    
    try:
        docs = vector_db.similarity_search("test", k=1)
        if docs and 'source_file_hash' in docs[0].metadata:
            stored_hash = docs[0].metadata.get('source_file_hash')
            return current_hash != stored_hash
    except:
        pass
    
    return True


def clear_vector_db():
    """Safely clear the vector database directory."""
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


def check_existing_vector_db():
    """Check if vector database already exists"""
    if os.path.exists(PERSIST_DIRECTORY):
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name="bert-base-uncased",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            vector_db = Chroma(
                persist_directory=PERSIST_DIRECTORY,
                embedding_function=embeddings,
                collection_name=VECTOR_STORE_NAME
            )
            if vector_db._collection.count() > 0:
                logging.info("Found existing vector database.")
                return vector_db
        except Exception as e:
            logging.warning(f"Existing DB issue: {e}")
    return None


def ingest_puml(puml_path):
    """Load PUML content and split into manageable chunks."""
    if os.path.exists(puml_path):
        with open(puml_path, 'r', encoding='utf-8') as file:
            content = file.read()
        logging.info("PUML file loaded successfully.")
        return content
    else:
        logging.error(f"PUML file not found at path: {puml_path}")
        return None


def split_documents(content, puml_path):
    """Split PUML content into smaller chunks as Document objects."""
    file_hash = hash(content)
    chunks = []
    
    # Strategy 1: Split by entities (more semantic)
    print(f"\n📊 SPLIT_DOCUMENTS DEBUG:")
    print(f"Contenido total: {len(content)} caracteres")
    
    # Strategy 1: Split by entities
    entity_pattern = r'(entity\s+\w+\s*\{[^}]+\})'
    entities = re.findall(entity_pattern, content, re.IGNORECASE | re.DOTALL)
    
    print(f"Entidades encontradas (regex): {len(entities)}")
    for i, entity in enumerate(entities[:3]):  # Mostrar primeras 3
        print(f"  Entidad {i+1}: {entity[:100]}...")
    
    # Strategy 2: Split by relationships
    relationship_pattern = r'(\w+\s+--\s+\w+|"\w+"\s+--\s+"\w+")'
    relationships = re.findall(relationship_pattern, content)
    
    if relationships:
        logging.info(f"Found {len(relationships)} relationships")
        relationship_chunk = "Relationships:\n" + "\n".join(relationships)
        chunks.append(Document(
            page_content=relationship_chunk,
            metadata={
                "source": "puml_file", 
                "chunk_id": len(chunks),
                "chunk_type": "relationships",
                "source_file": puml_path,
                "source_file_hash": file_hash
            }
        ))
    
    # Strategy 3: Split by @startuml sections
    section_pattern = r'(@startuml[^@]+?@enduml)'
    sections = re.findall(section_pattern, content, re.DOTALL)
    
    if sections and len(chunks) < 5:  # Solo si no hay muchos chunks ya
        logging.info(f"Found {len(sections)} UML sections")
        for i, section in enumerate(sections[:5]):  # Máximo 5 secciones
            chunks.append(Document(
                page_content=section[:1000],  # Limitar tamaño
                metadata={
                    "source": "puml_file", 
                    "chunk_id": len(chunks),
                    "chunk_type": "section",
                    "source_file": puml_path,
                    "source_file_hash": file_hash
                }
            ))
    
    # Strategy 4: Fallback - split by lines
    if not chunks:
        logging.info("Using line-based chunking as fallback")
        lines = content.splitlines()
        chunk_size = 10
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunk_text = "\n".join(chunk_lines)
            if chunk_text.strip():
                chunks.append(Document(
                    page_content=chunk_text,
                    metadata={
                        "source": "puml_file", 
                        "chunk_id": len(chunks),
                        "chunk_type": "line_chunk",
                        "source_file": puml_path,
                        "source_file_hash": file_hash
                    }
                ))
    
    logging.info(f"PUML content split into {len(chunks)} chunks.")
    return chunks


def create_vector_db(chunks, puml_path):
    """Create a vector database from PUML content chunks."""
    if not clear_vector_db():
        logging.error("Failed to clear existing vector database. Creating in memory only.")
    
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="bert-base-uncased",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True, mode=0o755)
        
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=VECTOR_STORE_NAME,
            persist_directory=PERSIST_DIRECTORY
        )
        vector_db.persist()
        logging.info(f"Vector database created and persisted for {puml_path}.")
        return vector_db
    except Exception as e:
        logging.error(f"Error creating persistent vector DB: {e}. Using in-memory fallback.")
        
        embeddings = HuggingFaceEmbeddings(
            model_name="bert-base-uncased",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=VECTOR_STORE_NAME
        )
        logging.info("In-memory vector database created as fallback.")
        return vector_db


def create_retriever(vector_db):
    """Create a retriever that actually retrieves relevant chunks."""
    # Configurar retriever para obtener chunks relevantes
    retriever = vector_db.as_retriever(
        search_kwargs={
            "k": 8,  # Más chunks para mejor contexto
        }
    )
    
    logging.info("Retriever created with k=8.")
    return retriever


def create_chain(retriever):
    """Create the RAG chain that actually uses the retrieved context."""
    llm = BERTRAGModel(model_name=MODEL_NAME)
    
    # DEBUG function
    def debug_retrieval(question):
        print(f"\n🔍 DEBUG - RETRIEVAL para pregunta:")
        print(f"Pregunta: {question[:100]}...")
        
        docs = retriever.get_relevant_documents(question)
        print(f"Documentos recuperados: {len(docs)}")
        
        for i, doc in enumerate(docs):
            print(f"\n--- Documento {i+1} ---")
            print(f"Tipo: {doc.metadata.get('chunk_type', 'unknown')}")
            print(f"Contenido: {doc.page_content[:200]}...")
        
        return docs
    
    # Template modificado con DEBUG
    template = """CONTEXTO RELEVANTE DEL DIAGRAMA UML:
{context}

PREGUNTA: {question}

INSTRUCCIONES: Genera SQL específico para CADA entidad encontrada en el contexto."""

    prompt = ChatPromptTemplate.from_template(template=template)
    
    def format_docs(docs):
        formatted = []
        for i, doc in enumerate(docs):
            content = doc.page_content
            chunk_type = doc.metadata.get('chunk_type', 'unknown')
            formatted.append(f"[{chunk_type} {i+1}]:\n{content}\n")
        return "\n".join(formatted)
    
    # Chain con debug
    chain = (
        {
            "context": lambda x: format_docs(debug_retrieval(x["question"])),
            "question": lambda x: x["question"]
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

def generate_sql_migrations_with_rag(chain, db_type, puml_file):
    """Generate SQL migrations usando RAG real."""
    
    # Leer el archivo PUML para análisis inicial
    with open(puml_file, 'r', encoding='utf-8') as f:
        puml_content = f.read()
    
    # Contar entidades para referencia
    entity_pattern = r'entity\s+(\w+)'
    entities = re.findall(entity_pattern, puml_content, re.IGNORECASE)
    
    print(f"📊 Archivo PUML analizado: {len(entities)} entidades encontradas")
    
    # Crear una pregunta específica para el RAG
    query = f"""
Genera migraciones SQL para una base de datos {db_type.upper()} basándote en este diagrama PlantUML.

REQUERIMIENTOS ESPECÍFICOS:
1. Analiza TODAS las entidades y relaciones del diagrama
2. Genera sentencias CREATE TABLE para CADA entidad encontrada
3. Usa tipos de datos apropiados para {db_type.upper()}
4. Incluye PRIMARY KEY autoincremental en cada tabla
5. Agrega FOREIGN KEYS para las relaciones documentadas
6. Formato: -- migrate:up / -- migrate:down para cada tabla

Se esperan aproximadamente {len(entities)} tablas basadas en el análisis inicial.
"""
    
    print(f"🚀 Consultando RAG con {len(entities)} entidades esperadas...")
    
    try:
        # Invocar la cadena RAG con la pregunta
        response = chain.invoke({"question": query})
        
        # Verificar si la respuesta tiene contenido
        if not response or len(response.strip()) < 50:
            print("⚠️  Respuesta RAG muy corta, usando fallback...")
            return generate_fallback_migrations(puml_file, db_type)
        
        return response
        
    except Exception as e:
        logging.error(f"Error en RAG: {e}")
        print("⚠️  Error en RAG, usando generación directa...")
        return generate_fallback_migrations(puml_file, db_type)


def generate_fallback_migrations(puml_file, db_type):
    """Generación de migraciones de fallback cuando RAG falla."""
    with open(puml_file, 'r', encoding='utf-8') as f:
        puml_content = f.read()
    
    # Extraer entidades
    entity_patterns = [
        r'entity\s+(\w+)',
        r'class\s+(\w+)',
        r'table\s+(\w+)',
        r'Entity\s+(\w+)',
    ]
    
    entities = []
    for pattern in entity_patterns:
        found = re.findall(pattern, puml_content, re.IGNORECASE)
        entities.extend(found)
    
    entities = list(set(entities))  # Eliminar duplicados
    
    if not entities:
        entities = ['Users', 'Products', 'Orders', 'Categories']
    
    print(f"🔧 Fallback: generando {len(entities)} tablas directamente")
    
    # Generar SQL básico
    sql_parts = []
    for entity in entities:
        # Determinar tipo de ID según DB
        if db_type.lower() in ["mysql", "mariadb"]:
            id_col = "id INT PRIMARY KEY AUTO_INCREMENT"
        elif db_type.lower() in ["postgresql", "postgres"]:
            id_col = "id SERIAL PRIMARY KEY"
        elif db_type.lower() == "sqlite":
            id_col = "id INTEGER PRIMARY KEY AUTOINCREMENT"
        else:
            id_col = "id INT PRIMARY KEY AUTO_INCREMENT"
        
        sql = f"""-- migrate:up

CREATE TABLE {entity} (
    {id_col},
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- migrate:down

DROP TABLE {entity};"""
        
        sql_parts.append(sql)
    
    return "\n\n".join(sql_parts)


# Parser y funciones auxiliares (las mismas que antes)

def parse_migration_blocks(complete_migrations):
    """Parsea los bloques de migración."""
    if complete_migrations.startswith("Error:") or len(complete_migrations.strip()) < 50:
        return {}
    
    patterns = [
        r'--\s*migrate:up\s*(CREATE TABLE[^;]+;)\s*--\s*migrate:down\s*(DROP TABLE[^;]+;)',
        r'(CREATE TABLE[^;]+;)',
    ]
    
    tables_dict = {}
    seen_tables = set()
    
    for pattern in patterns:
        matches = re.findall(pattern, complete_migrations, re.IGNORECASE | re.DOTALL)
        if matches:
            for i, match in enumerate(matches, len(tables_dict) + 1):
                if isinstance(match, tuple):
                    create_stmt, drop_stmt = match
                else:
                    create_stmt = match
                    table_name = extract_table_name(create_stmt)
                    drop_stmt = f"DROP TABLE IF EXISTS {table_name};" if table_name else "DROP TABLE unknown_table;"
                
                table_name = extract_table_name(create_stmt)
                
                if table_name and table_name.lower() in seen_tables:
                    continue
                    
                seen_tables.add(table_name.lower() if table_name else "")
                
                clean_create = re.sub(r'\s+', ' ', create_stmt.strip())
                clean_drop = re.sub(r'\s+', ' ', drop_stmt.strip())
                
                complete_block = f"-- migrate:up\n\n{create_stmt.strip()}\n\n-- migrate:down\n\n{drop_stmt.strip()}"
                
                tables_dict[i] = {
                    'up': clean_create,
                    'down': clean_drop,
                    'complete_block': complete_block,
                    'table_name': table_name or f"table_{i}"
                }
    
    return tables_dict


def extract_table_name(sql_statement):
    """Extrae el nombre de la tabla."""
    patterns = [
        r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?`?([^\s`(;]+)`?',
        r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?([^\s(;]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, sql_statement, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def validate_entity_count(puml_file, tables_dict):
    """Validate that we have the expected number of entities."""
    try:
        with open(puml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        entity_pattern = r'entity\s+(\w+)'
        entities = re.findall(entity_pattern, content, re.IGNORECASE)
        
        expected_count = len(entities)
        actual_count = len(tables_dict)
        
        logging.info(f"Expected entities: {expected_count}, Generated tables: {actual_count}")
        
        if expected_count != actual_count:
            print(f"⚠️  ADVERTENCIA: Se esperaban {expected_count} tablas pero se generaron {actual_count}")
            
            generated_tables = [data.get('table_name') for data in tables_dict.values() if data.get('table_name')]
            missing_entities = set(entities) - set(generated_tables)
            
            if missing_entities:
                print(f"📋 Entidades faltantes: {', '.join(missing_entities)}")
            
            if generated_tables:
                print(f"📋 Tablas generadas: {', '.join(generated_tables)}")
        
        return expected_count, actual_count
    except Exception as e:
        logging.error(f"Error validating entity count: {e}")
        return 0, len(tables_dict)


def enforce_original_names(puml_file, tables_dict):
    """Ensure table names match the original PUML entities."""
    try:
        with open(puml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        entity_pattern = r'entity\s+(\w+)'
        original_entities = re.findall(entity_pattern, content, re.IGNORECASE)
        
        corrected_dict = {}
        correction_count = 0
        
        for key, table_data in tables_dict.items():
            current_name = table_data.get('table_name')
            
            matching_entity = None
            for entity in original_entities:
                if entity.lower() == current_name.lower():
                    matching_entity = entity
                    break
            
            if matching_entity and matching_entity != current_name:
                correction_count += 1
                corrected_up = re.sub(
                    f'TABLE\\s+{re.escape(current_name)}', 
                    f'TABLE {matching_entity}', 
                    table_data['up'], 
                    flags=re.IGNORECASE
                )
                corrected_down = re.sub(
                    f'TABLE\\s+{re.escape(current_name)}', 
                    f'TABLE {matching_entity}', 
                    table_data['down'], 
                    flags=re.IGNORECASE
                )
                
                corrected_block = re.sub(
                    f'TABLE\\s+{re.escape(current_name)}', 
                    f'TABLE {matching_entity}', 
                    table_data['complete_block'], 
                    flags=re.IGNORECASE
                )
                
                corrected_dict[key] = {
                    'up': corrected_up,
                    'down': corrected_down,
                    'complete_block': corrected_block,
                    'table_name': matching_entity
                }
                
                print(f"✓ Corregido: '{current_name}' -> '{matching_entity}'")
            else:
                corrected_dict[key] = table_data
        
        if correction_count > 0:
            print(f"✓ Se corrigieron {correction_count} nombres de tabla")
        
        return corrected_dict
    except Exception as e:
        logging.error(f"Error enforcing original names: {e}")
        return tables_dict


def save_migration_files(tables_dict, puml_basename, db_type, complete_migrations, nombre_carpeta):
    """Guardar archivos de migración."""
    if not tables_dict:
        print("❌ No hay migraciones para guardar.")
        return False
    
    try:
        os.makedirs(nombre_carpeta, exist_ok=True)
        print(f"📁 Carpeta principal: {nombre_carpeta}")
        
        complete_filename = os.path.join(nombre_carpeta, f"complete_migrations_{puml_basename}_{db_type}.sql")
        with open(complete_filename, 'w', encoding='utf-8') as f:
            f.write(f"-- Migraciones generadas desde: {puml_basename}.puml\n")
            f.write(f"-- Tipo de base de datos: {db_type}\n")
            f.write(f"-- Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Total de tablas: {len(tables_dict)}\n")
            f.write(f"-- Carpeta: {nombre_carpeta}\n\n")
            f.write(complete_migrations)
        print(f"✓ Migraciones completas guardadas en: {complete_filename}")
        
        migrations_dir = os.path.join(nombre_carpeta, "migrations")
        
        if os.path.exists(migrations_dir):
            shutil.rmtree(migrations_dir)
            print(f"♻️  Limpiando carpeta migrations existente")
        
        os.makedirs(migrations_dir, exist_ok=True)
        print(f"📂 Subcarpeta migrations creada en: {migrations_dir}")
        
        base_timestamp = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        saved_count = 0

        for key, table_data in tables_dict.items():
            table_name = table_data.get('table_name')
            if table_name:
                timestamp = str(base_timestamp + key)
                migration_filename = os.path.join(migrations_dir, f"{timestamp}_create_{table_name}.sql")

                with open(migration_filename, 'w', encoding='utf-8') as f:
                    f.write(table_data['complete_block'])
                
                saved_count += 1
                print(f"  ✓ Migración {key:2d} ({table_name:20s}) → {migration_filename}")
        
        metadata_file = os.path.join(nombre_carpeta, "metadata.json")
        metadata = {
            "puml_file": f"{puml_basename}.puml",
            "database_type": db_type,
            "generation_date": datetime.datetime.now().isoformat(),
            "total_tables": len(tables_dict),
            "saved_files": saved_count,
            "tables": [data.get('table_name') for data in tables_dict.values() if data.get('table_name')]
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"✓ Metadatos guardados en: {metadata_file}")
        
        # 6. Opcional: Crear README en la carpeta principal
        readme_file = os.path.join(nombre_carpeta, "README.md")
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(f"# Migraciones SQL - {puml_basename}\n\n")
            f.write(f"**Fecha de generación:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Tipo de base de datos:** {db_type}\n")
            f.write(f"**Archivo PUML origen:** {puml_basename}.puml\n")
            f.write(f"**Total de tablas generadas:** {len(tables_dict)}\n\n")
            f.write("## Estructura de carpetas\n\n")
            f.write("- `migrations/` - Archivos individuales de migración\n")
            f.write("- `complete_migrations_*.sql` - Todas las migraciones en un archivo\n")
            f.write("- `metadata.json` - Información de generación\n")
            f.write("- `README.md` - Este archivo\n\n")
            f.write("## Tablas generadas\n\n")
            for key, table_data in tables_dict.items():
                table_name = table_data.get('table_name', 'Desconocida')
                f.write(f"{key}. `{table_name}`\n")
        
        print(f"✓ README creado en: {readme_file}")
        print(f"\n{'='*60}")
        print(f"✅ COMPLETADO: {saved_count} archivos guardados en {nombre_carpeta}")
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar archivos: {e}")
        return False

def demo(folder_path, db_type, modelo):
    # Paso 1: Ingresar el tipo de base de datos
    db_type = db_type
    # Paso 2: Ingresar el archivo PUML
    puml_file = os.path.join(modelo)

    # Paso 3: Verificar y gestionar la base vectorial
    vector_db = check_existing_vector_db()
    
    # Check if we need to recreate the vector DB
    if should_recreate_vector_db(puml_file, vector_db):
        print("Creando nueva base de datos vectorial...")
        content = ingest_puml(puml_file)
        if not content:
            return "❌ No se pudo crear la base de datos vectorial.", False
        
        chunks = split_documents(content, puml_file)
        vector_db = create_vector_db(chunks, puml_file)
    else:
        print("Usando base de datos vectorial existente.")

    # Crear el retriever y la cadena
    retriever = create_retriever(vector_db)
    chain = create_chain(retriever)

    # Paso 4: Generar las migraciones SQL
    print(f"Generando migraciones SQL para {puml_file}...")

    # Intentar con RAG primero
    complete_migrations = generate_sql_migrations_with_rag(chain, db_type, puml_file)

    # Verificar si el modelo rechazó la generación
    if "No puedo cumplir" in complete_migrations or "I cannot fulfill" in complete_migrations or complete_migrations.startswith("Error:"):
        print("❌ El modelo rechazó generar migraciones. Usando método alternativo...")
        # complete_migrations = generate_direct_migrations(puml_file, db_type)
        return "❌ No se pudieron generar migraciones.", False
    
    if not complete_migrations or "Error:" in complete_migrations:
        print("❌ No se pudieron generar migraciones.")
        return "❌ No se pudieron generar migraciones.", False

    # Mostrar las migraciones generadas
    print("\n" + "="*60)
    print(f"MIGRACIONES SQL GENERADAS PARA: {puml_file}")
    print("="*60)
    print(complete_migrations)

    # Paso 5: Parsear y organizar en diccionario
    print("\n" + "="*60)
    print("ORGANIZANDO EN DICCIONARIO:")
    print("="*60)
    
    tables_dict = parse_migration_blocks(complete_migrations)
    
    if not tables_dict:
        print("❌ No se pudieron parsear las migraciones.")
        return "❌ No se pudieron parsear las migraciones.", False

    # Validar conteo de entidades
    expected_count, actual_count = validate_entity_count(puml_file, tables_dict)

    print('expected_count: ' + str(expected_count))
    print('actual_count: ' + str(actual_count))
    
    # Forzar nombres originales
    tables_dict = enforce_original_names(puml_file, tables_dict)

    resp = []

    if tables_dict:
        print(f"\n✅ Se procesaron {len(tables_dict)} tablas ÚNICAS:\n")
        
        for key, table_data in tables_dict.items():
            table_name = table_data.get('table_name')
            print(f"Tabla {key} ({table_name}):")
            print(f"  UP:   {table_data['up']}")
            print(f"  DOWN: {table_data['down']}")
            print("-" * 80)
            resp.append(table_data)
    else:
        print("❌ No se pudieron procesar las migraciones.")
        return "❌ No se pudieron procesar las migraciones.", False

    #return resp, True

    # Paso 6: Guardar archivos
    print("Guardando las migraciones en archivos")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Crear nombre de carpeta
    nombre_carpeta = f"{timestamp}_{folder_path}"
    # Crear la carpeta
    os.makedirs(nombre_carpeta, exist_ok=True)

    puml_basename = os.path.splitext(os.path.basename(puml_file))[0]

    save_migration_files(tables_dict, puml_basename, db_type, complete_migrations, nombre_carpeta)

    # Opción adicional: guardar diccionario como JSON
    print("Guardardando diccionario como JSON")
    json_filename = os.path.join(nombre_carpeta, f"migrations_dict_{puml_basename}_{db_type}.json")
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(tables_dict, f, indent=2, ensure_ascii=False)
    print(f"✓ Diccionario guardado en: {json_filename}")

def measuring(folder_path, db_type, archivo_puml, csv_file='measurements.csv'):
    """Ejecuta demo con mediciones de CPU, RAM y GPU."""
    import time
    import csv
    import psutil
    import threading
    import queue
    import datetime

    from gpus_measures import detect_gpu_libraries, print_resumen_metricas, get_gpu_info
    
    # Modelo de LLM (Ollama) - ahora es una variable del método
    modelo_llm = "BERT + t5small"  # O el modelo que estés usando
    
    # Detectar bibliotecas de GPU disponibles
    gpu_libs = detect_gpu_libraries()
    
    # Crear o inicializar CSV con columnas actualizadas
    csv_columns = [
        'test_id', 'test_name', 'modelo_llm', 'db_type', 'archivo_puml',
        'total_time_ms', 'rag_time_ms', 'parsing_time_ms',
        'memory_before_mb', 'memory_avg_during_rag_mb', 'memory_final_mb',
        'cpu_before', 'cpu_avg_during_rag', 'cpu_final'
    ]
    
    # Añadir columnas de GPU según lo disponible
    if 'nvidia' in gpu_libs:
        csv_columns.extend([
            'gpu_util_avg_rag', 'gpu_mem_avg_rag', 'gpu_temp_avg_rag',
            'gpu_util_max_rag', 'gpu_mem_max_rag', 'gpu_temp_max_rag'
        ])
    elif 'amd' in gpu_libs:
        csv_columns.extend(['gpu_util_avg_rag', 'gpu_mem_avg_rag', 'gpu_temp_avg_rag'])
    elif 'intel' in gpu_libs:
        csv_columns.extend(['gpu_util_avg_rag', 'gpu_mem_avg_rag'])
    
    csv_columns.extend([
        'num_tables', 'expected_tables', 'success', 'error_message',
        'timestamp'
    ])
    
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(csv_columns)
    
    # Generar ID único
    test_id = f"{folder_path}_{db_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_name = f"demo_{folder_path}_{db_type}"
    
    # Variables para mediciones
    total_start_time = time.time()
    
    success = False
    error_message = ""
    num_tables = 0
    expected_tables = 0
    
    # Variables para muestras
    cpu_samples = []
    ram_samples = []
    gpu_util_samples = []
    gpu_mem_samples = []
    gpu_temp_samples = []
    
    # Variables para promedios
    cpu_avg_during_rag = 0
    memory_avg_during_rag = 0
    gpu_util_avg = 0
    gpu_mem_avg = 0
    gpu_temp_avg = 0
    
    try:
        print(f"\n{'='*60}")
        print(f"INICIANDO PRUEBA: {test_name}")
        print(f"Modelo LLM: {modelo_llm}")
        print(f"Base de datos: {db_type}")
        print(f"Archivo PUML: {archivo_puml}")
        print(f"GPU detectada: {', '.join(gpu_libs) if gpu_libs else 'No disponible'}")
        print(f"{'='*60}")
        
        # MEDICIÓN 1: Estado inicial
        memory_before = psutil.virtual_memory().used / (1024 * 1024)
        cpu_before = psutil.cpu_percent(interval=0.1)
        
        # Medición inicial de GPU si está disponible
        gpu_info_before = get_gpu_info(gpu_libs)
        
        # Obtener ruta completa del archivo PUML
        puml_file = os.path.join(archivo_puml)
        print(f"📄 Ruta completa: {os.path.abspath(puml_file)}")
        
        # Verificar que el archivo existe
        if not os.path.exists(puml_file):
            error_message = f"Archivo PUML no encontrado: {puml_file}"
            print(f"❌ {error_message}")
            raise FileNotFoundError(error_message)
        
        # Paso 3: Base de datos vectorial
        vector_db = check_existing_vector_db()
        
        if should_recreate_vector_db(puml_file, vector_db):
            print("🔄 Creando nueva base de datos vectorial...")
            content = ingest_puml(puml_file)
            if not content:
                error_message = "No se pudo crear la base de datos vectorial"
                raise Exception(error_message)
            
            chunks = split_documents(content, puml_file)
            vector_db = create_vector_db(chunks, puml_file)
        else:
            print("✅ Usando base de datos vectorial existente.")

        retriever = create_retriever(vector_db)
        chain = create_chain(retriever)

        # Paso 4: Generación RAG con medición completa
        print(f"\n🚀 Generando migraciones SQL usando {modelo_llm}...")
        
        # Función para monitorear todos los recursos
        def monitor_all_resources(cpu_q, ram_q, gpu_q, stop_event, sample_interval=0.3):
            """Monitorea CPU, RAM y GPU periódicamente."""
            cpu_samples_local = []
            ram_samples_local = []
            gpu_util_samples_local = []
            gpu_mem_samples_local = []
            gpu_temp_samples_local = []
            
            while not stop_event.is_set():
                # Medir CPU (esto bloquea por sample_interval segundos)
                cpu = psutil.cpu_percent(interval=sample_interval)
                cpu_samples_local.append(cpu)
                
                # Medir RAM inmediatamente después
                ram = psutil.virtual_memory().used / (1024 * 1024)
                ram_samples_local.append(ram)
                
                # Medir GPU si está disponible
                gpu_info = get_gpu_info(gpu_libs)
                if gpu_info:
                    if 'utilization' in gpu_info:
                        gpu_util_samples_local.append(gpu_info['utilization'])
                    if 'memory_used' in gpu_info:
                        gpu_mem_samples_local.append(gpu_info['memory_used'])
                    if 'temperature' in gpu_info:
                        gpu_temp_samples_local.append(gpu_info['temperature'])
                
                # Limitar tamaño de muestras
                max_samples = 100
                for lst in [cpu_samples_local, ram_samples_local, 
                           gpu_util_samples_local, gpu_mem_samples_local, 
                           gpu_temp_samples_local]:
                    if len(lst) > max_samples:
                        lst.pop(0)
            
            # Enviar muestras a las colas
            cpu_q.put(cpu_samples_local)
            ram_q.put(ram_samples_local)
            
            gpu_data = {
                'utilization': gpu_util_samples_local,
                'memory': gpu_mem_samples_local,
                'temperature': gpu_temp_samples_local
            }
            gpu_q.put(gpu_data)
        
        # Iniciar monitoreo
        print("📈 Iniciando monitoreo de CPU, RAM y GPU durante RAG...")
        cpu_queue = queue.Queue()
        ram_queue = queue.Queue()
        gpu_queue = queue.Queue()
        stop_event = threading.Event()
        
        monitor_thread = threading.Thread(
            target=monitor_all_resources,
            args=(cpu_queue, ram_queue, gpu_queue, stop_event, 0.3)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Pequeña pausa para que el thread comience
        time.sleep(0.1)
        
        # MEDICIÓN 2: Ejecutar RAG
        rag_start_time = time.time()
        
        try:
            complete_migrations = generate_sql_migrations_with_rag(chain, db_type, puml_file)
        finally:
            # Detener monitoreo
            stop_event.set()
            monitor_thread.join(timeout=2.0)
            
            # Obtener muestras
            try:
                cpu_samples = cpu_queue.get(timeout=1.0)
                ram_samples = ram_queue.get(timeout=1.0)
                gpu_data = gpu_queue.get(timeout=1.0) if gpu_libs else {}
                
                # Calcular promedios
                if cpu_samples:
                    cpu_avg_during_rag = sum(cpu_samples) / len(cpu_samples)
                
                if ram_samples:
                    memory_avg_during_rag = sum(ram_samples) / len(ram_samples)
                
                if 'utilization' in gpu_data and gpu_data['utilization']:
                    gpu_util_samples = gpu_data['utilization']
                    gpu_util_avg = sum(gpu_util_samples) / len(gpu_util_samples)
                
                if 'memory' in gpu_data and gpu_data['memory']:
                    gpu_mem_samples = gpu_data['memory']
                    gpu_mem_avg = sum(gpu_mem_samples) / len(gpu_mem_samples)
                
                if 'temperature' in gpu_data and gpu_data['temperature']:
                    gpu_temp_samples = gpu_data['temperature']
                    gpu_temp_avg = sum(gpu_temp_samples) / len(gpu_temp_samples)
                    
            except queue.Empty:
                print("⚠️  Timeout al obtener muestras")
        
        rag_end_time = time.time()
        rag_time_ms = (rag_end_time - rag_start_time) * 1000
        
        # Mostrar métricas
        print(f"\n📊 MÉTRICAS DURANTE RAG:")
        print(f"⏱️  Tiempo: {rag_time_ms:.2f} ms")
        print(f"📈 CPU promedio: {cpu_avg_during_rag:.1f}%")
        print(f"💾 RAM promedio: {memory_avg_during_rag:.2f} MB")
        
        if gpu_libs:
            if gpu_util_samples:
                print(f"🎮 GPU uso promedio: {gpu_util_avg:.1f}%")
                print(f"   GPU uso máximo: {max(gpu_util_samples) if gpu_util_samples else 0:.1f}%")
            if gpu_mem_samples:
                print(f"💾 GPU memoria promedio: {gpu_mem_avg:.2f} MB")
                print(f"   GPU memoria máxima: {max(gpu_mem_samples) if gpu_mem_samples else 0:.2f} MB")
            if gpu_temp_samples:
                print(f"🌡️  GPU temperatura promedio: {gpu_temp_avg:.1f}°C")
                print(f"   GPU temperatura máxima: {max(gpu_temp_samples) if gpu_temp_samples else 0:.1f}°C")
        else:
            print("🎮 GPU: No disponible para monitoreo")

        # Verificar resultado del RAG
        if "No puedo cumplir" in complete_migrations or "I cannot fulfill" in complete_migrations or complete_migrations.startswith("Error:"):
            error_message = "El modelo rechazó generar migraciones"
            print(f"❌ {error_message}")
            raise Exception(error_message)
        
        if not complete_migrations or "Error:" in complete_migrations:
            error_message = "No se pudieron generar migraciones"
            print(f"❌ {error_message}")
            raise Exception(error_message)

        # Paso 5: Parsear migraciones
        parsing_start_time = time.time()
        tables_dict = parse_migration_blocks(complete_migrations)
        parsing_end_time = time.time()
        parsing_time_ms = (parsing_end_time - parsing_start_time) * 1000
        
        if not tables_dict:
            error_message = "No se pudieron parsear las migraciones"
            raise Exception(error_message)

        # Validar conteo
        expected_count, actual_count = validate_entity_count(puml_file, tables_dict)
        expected_tables = expected_count
        num_tables = actual_count
        
        tables_dict = enforce_original_names(puml_file, tables_dict)
        resp = []
        
        if tables_dict:
            print(f"\n✅ Se generaron {len(tables_dict)} tablas:")
            for i, (key, table_data) in enumerate(list(tables_dict.items())[:5], 1):
                table_name = table_data.get('table_name')
                print(f"  {i}. {table_name}")
            
            if len(tables_dict) > 5:
                print(f"  ... y {len(tables_dict) - 5} tablas más")
            
            for key, table_data in tables_dict.items():
                resp.append(table_data)
        else:
            raise Exception("No se pudieron procesar las migraciones")

        # Paso 6: Guardar archivos
        print("\n💾 Guardando las migraciones en archivos...")
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_carpeta = f"{timestamp}_{folder_path}_{db_type}"
        os.makedirs(nombre_carpeta, exist_ok=True)

        puml_basename = os.path.splitext(os.path.basename(puml_file))[0]
        save_migration_files(tables_dict, puml_basename, db_type, complete_migrations, nombre_carpeta)

        json_filename = os.path.join(nombre_carpeta, f"migrations_dict_{puml_basename}_{db_type}.json")
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(tables_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Archivos guardados en: {nombre_carpeta}")
        success = True
        
    except Exception as e:
        if not error_message:
            error_message = str(e)
        print(f"\n❌ ERROR: {error_message}")
        success = False
    
    finally:
        # MEDICIÓN FINAL
        total_end_time = time.time()
        total_time_ms = (total_end_time - total_start_time) * 1000
        
        memory_final = psutil.virtual_memory().used / (1024 * 1024)
        cpu_final = psutil.cpu_percent(interval=0.1)
        
        # Medición final de GPU
        gpu_info_final = get_gpu_info(gpu_libs)
        
        # Preparar datos para CSV
        csv_data = [
            test_id,
            test_name,
            modelo_llm,          # Nueva columna: modelo de LLM
            db_type,
            archivo_puml,        # Nueva columna: nombre del archivo PUML
            total_time_ms,
            rag_time_ms,
            parsing_time_ms,
            memory_before,
            memory_avg_during_rag,
            memory_final,
            cpu_before,
            cpu_avg_during_rag,
            cpu_final
        ]
        
        # Añadir datos de GPU según lo disponible
        if 'nvidia' in gpu_libs:
            csv_data.extend([
                gpu_util_avg,
                gpu_mem_avg,
                gpu_temp_avg,
                max(gpu_util_samples) if gpu_util_samples else 0,
                max(gpu_mem_samples) if gpu_mem_samples else 0,
                max(gpu_temp_samples) if gpu_temp_samples else 0
            ])
        elif 'amd' in gpu_libs or 'intel' in gpu_libs:
            csv_data.extend([
                gpu_util_avg,
                gpu_mem_avg,
                gpu_temp_avg if 'amd' in gpu_libs else 0
            ])
        
        csv_data.extend([
            num_tables,
            expected_tables,
            success,
            error_message,
            datetime.datetime.now().isoformat()
        ])
        
        # Guardar en CSV
        try:
            with open(csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(csv_data)
            
            print(f"\n📊 Métricas guardadas en CSV: {csv_file}")
            
            # Mostrar resumen detallado
            print(f"\n{'='*60}")
            print("📈 RESUMEN COMPLETO DE MÉTRICAS:")
            print(f"{'='*60}")
            print(f"✅ Éxito: {'SÍ' if success else 'NO'}")
            print(f"🤖 Modelo LLM: {modelo_llm}")
            print(f"🗄️  Base de datos: {db_type}")
            print(f"📄 Archivo PUML: {archivo_puml}")
            print(f"\n⏱️  Tiempos:")
            print(f"  - Total: {total_time_ms:.2f} ms")
            print(f"  - RAG:   {rag_time_ms:.2f} ms")
            print(f"  - Parseo: {parsing_time_ms:.2f} ms")
            
            print(f"\n💾 RAM:")
            print(f"  - Antes RAG:       {memory_before:.2f} MB")
            print(f"  - Promedio durante RAG: {memory_avg_during_rag:.2f} MB")
            print(f"  - Final:           {memory_final:.2f} MB")
            
            print(f"\n📈 CPU:")
            print(f"  - Antes RAG:       {cpu_before:.1f}%")
            print(f"  - Promedio durante RAG: {cpu_avg_during_rag:.1f}%")
            print(f"  - Final:           {cpu_final:.1f}%")
            
            if gpu_libs:
                print(f"\n🎮 GPU ({', '.join(gpu_libs)}):")
                if gpu_util_samples:
                    print(f"  - Uso promedio:    {gpu_util_avg:.1f}%")
                if gpu_mem_samples:
                    print(f"  - Memoria promedio: {gpu_mem_avg:.2f} MB")
                if gpu_temp_samples and gpu_temp_avg > 0:
                    print(f"  - Temp promedio:    {gpu_temp_avg:.1f}°C")
            
            print(f"\n📊 Resultados:")
            print(f"  - Tablas generadas: {num_tables}")
            print(f"  - Tablas esperadas: {expected_tables}")
            
            if not success and error_message:
                print(f"\n⚠️  ERROR: {error_message}")
            
            print(f"{'='*60}")
            
        except Exception as csv_error:
            print(f"❌ Error al guardar en CSV: {csv_error}")
    
    if success:
        return resp, True
    else:
        return f"Error: {error_message}", False