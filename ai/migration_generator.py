# application/ai/migration_generator.py
import re
import logging
from .chain_services import ChainServices
from .prompt_templates import PromptTemplates
from .agents.data_processor import DataProcessor
from .agents.query_analyzer import QueryAnalyzer
from .utils.validation import Validation
from .utils.text_processing import TextProcessing

class MigrationGenerator:
  """Generador de migraciones SQL usando RAG"""
  
  def __init__(self, vector_db):
    self.vector_db = vector_db
    self.retriever = ChainServices.create_retriever(vector_db)
    self.chain = ChainServices.create_sql_generation_chain(self.retriever)
  
  def generate_sql_migrations_with_rag(self, db_type, puml_file):
    """Genera migraciones SQL usando RAG"""
    with open(puml_file, 'r', encoding='utf-8') as f:
      puml_content = f.read()
    
    entities_info = DataProcessor.extract_entities_info(puml_content)
    entities_summary = "\n".join([
      f"Entidad: {entity['name']}, Atributos: {entity['attributes']}" 
      for entity in entities_info
    ])
    
    query = PromptTemplates.get_migration_generation_prompt(db_type, puml_file, entities_summary)
    
    print("Generando migraciones SQL con RAG... Esto puede tomar unos momentos.")
    try:
      response = self.chain.invoke(query)
      return response
    except Exception as e:
      logging.error(f"Error generating migrations with RAG: {e}")
      return f"Error: {e}"
  
  def generate_direct_migrations(self, puml_file, db_type):
    """Genera migraciones directamente del archivo PUML (fallback)"""
    print("Usando método de generación directa como fallback...")
    
    try:
      with open(puml_file, 'r', encoding='utf-8') as f:
        content = f.read()
      
      entities_info = DataProcessor.extract_entities_info(content)
      migrations = []
      
      for entity in entities_info:
        entity_name = entity['name']
        attributes = entity['attributes']
        
        create_lines = [f"CREATE TABLE {entity_name} ("]
        
        if db_type == 'postgres':
          create_lines.append("  id SERIAL PRIMARY KEY,")
        elif db_type == 'mysql':
          create_lines.append("  id INT AUTO_INCREMENT PRIMARY KEY,")
        else:
          create_lines.append("  id INTEGER PRIMARY KEY AUTOINCREMENT,")
        
        for attr_name, attr_type in attributes:
          sql_type = TextProcessing.map_puml_to_sql(attr_type, db_type)
          create_lines.append(f"  {attr_name} {sql_type},")
        
        create_lines[-1] = create_lines[-1].rstrip(',')
        create_lines.append(");")
        
        create_stmt = "\n".join(create_lines)
        drop_stmt = f"DROP TABLE IF EXISTS {entity_name};"
        
        migration_block = f"-- migrate:up\n\n{create_stmt}\n\n-- migrate:down\n\n{drop_stmt}\n"
        migrations.append(migration_block)
      
      return "\n".join(migrations)
    
    except Exception as e:
      logging.error(f"Error in direct migration generation: {e}")
      return ""
  
  def process_migrations(self, complete_migrations, puml_file, db_type):
    """Procesa las migraciones generadas"""
    if Validation.is_model_refusal(complete_migrations) or complete_migrations.startswith("Error:"):
      print("❌ El modelo rechazó generar migraciones. Usando método alternativo...")
      complete_migrations = self.generate_direct_migrations(puml_file, db_type)
    
    if not complete_migrations or "Error:" in complete_migrations:
      print("❌ No se pudieron generar migraciones.")
      return None
    
    tables_dict = QueryAnalyzer.parse_migration_blocks(complete_migrations)
    
    if not tables_dict:
      print("❌ No se pudieron parsear las migraciones.")
      return None
    
    expected_count, actual_count = QueryAnalyzer.validate_entity_count(puml_file, tables_dict)
    
    tables_dict = TextProcessing.enforce_original_names(puml_file, tables_dict)
    
    return {
      'tables_dict': tables_dict,
      'complete_migrations': complete_migrations,
      'expected_count': expected_count,
      'actual_count': actual_count
    }