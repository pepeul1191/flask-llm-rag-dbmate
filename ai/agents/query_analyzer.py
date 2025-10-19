# application/ai/agents/query_analyzer.py
import re
import logging

class QueryAnalyzer:
  """Agente especializado en análisis y procesamiento de consultas"""
  
  @staticmethod
  def parse_migration_blocks(complete_migrations):
    """Parsea bloques de migración y crea diccionario de tablas"""
    if complete_migrations.startswith("Error:") or "No puedo cumplir" in complete_migrations:
      logging.error(f"Model refused to generate migrations: {complete_migrations}")
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
        logging.info(f"Found {len(matches)} matches using pattern")
        
        for i, match in enumerate(matches, len(tables_dict) + 1):
          if isinstance(match, tuple):
            create_stmt, drop_stmt = match
          else:
            create_stmt = match
            table_name = QueryAnalyzer.extract_table_name(create_stmt)
            drop_stmt = f"DROP TABLE IF EXISTS {table_name};" if table_name else "DROP TABLE unknown_table;"
          
          table_name = QueryAnalyzer.extract_table_name(create_stmt)
          
          if table_name and table_name in seen_tables:
            logging.info(f"Skipping duplicate table: {table_name}")
            continue
            
          seen_tables.add(table_name)
          
          clean_create = re.sub(r'\s+', ' ', create_stmt.strip())
          clean_drop = re.sub(r'\s+', ' ', drop_stmt.strip())
          
          complete_block = f"-- migrate:up\n\n{create_stmt.strip()}\n\n-- migrate:down\n\n{drop_stmt.strip()}"
          
          tables_dict[i] = {
            'up': clean_create,
            'down': clean_drop,
            'complete_block': complete_block,
            'table_name': table_name
          }
    
    logging.info(f"Se encontraron {len(tables_dict)} tablas únicas.")
    return tables_dict
  
  @staticmethod
  def extract_table_name(sql_statement):
    """Extrae el nombre de la tabla de una sentencia SQL"""
    patterns = [
      r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?`?([^\s`(;]+)`?',
      r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?([^\s(;]+)',
      r'DROP TABLE\s+(?:IF EXISTS\s+)?`?([^\s`;]+)`?',
    ]
    
    for pattern in patterns:
      match = re.search(pattern, sql_statement, re.IGNORECASE)
      if match:
        return match.group(1).strip()
    return None
  
  @staticmethod
  def validate_entity_count(puml_file, tables_dict):
    """Valida que el número de entidades generadas coincida con el esperado"""
    try:
      with open(puml_file, 'r', encoding='utf-8') as f:
        content = f.read()
      
      from .data_processor import DataProcessor
      expected_count = DataProcessor.count_entities(content)
      actual_count = len(tables_dict)
      
      logging.info(f"Expected entities: {expected_count}, Generated tables: {actual_count}")
      
      if expected_count != actual_count:
        print(f"⚠️  ADVERTENCIA: Se esperaban {expected_count} tablas pero se generaron {actual_count}")
        
        generated_tables = [data.get('table_name') for data in tables_dict.values() if data.get('table_name')]
        entity_pattern = r'entity\s+(\w+)'
        entities = re.findall(entity_pattern, content, re.IGNORECASE)
        missing_entities = set(entities) - set(generated_tables)
        
        if missing_entities:
          print(f"📋 Entidades faltantes: {', '.join(missing_entities)}")
        
        if generated_tables:
          print(f"📋 Tablas generadas: {', '.join(generated_tables)}")
      
      return expected_count, actual_count
    except Exception as e:
      logging.error(f"Error validating entity count: {e}")
      return 0, len(tables_dict)