# application/ai/utils/text_processing.py
import re
import logging

class TextProcessing:
  """Utilidades para procesamiento de texto"""
  
  @staticmethod
  def enforce_original_names(puml_file, tables_dict):
    """Asegura que los nombres de tabla coincidan con las entidades PUML originales"""
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
  
  @staticmethod
  def map_puml_to_sql(puml_type, db_type):
    """Mapea tipos PUML a tipos SQL apropiados"""
    puml_type = puml_type.lower().strip()
    
    type_mappings = {
      'sqlite': {
        'string': 'TEXT',
        'int': 'INTEGER', 
        'integer': 'INTEGER',
        'boolean': 'INTEGER',
        'date': 'TEXT',
        'datetime': 'TEXT',
        'float': 'REAL',
        'double': 'REAL',
        'text': 'TEXT'
      },
      'mysql': {
        'string': 'VARCHAR(255)',
        'int': 'INT',
        'integer': 'INT',
        'boolean': 'BOOLEAN',
        'date': 'DATE',
        'datetime': 'DATETIME',
        'float': 'FLOAT',
        'double': 'DOUBLE',
        'text': 'TEXT'
      },
      'postgres': {
        'string': 'VARCHAR(255)',
        'int': 'INTEGER',
        'integer': 'INTEGER',
        'boolean': 'BOOLEAN',
        'date': 'DATE',
        'datetime': 'TIMESTAMP',
        'float': 'REAL',
        'double': 'DOUBLE PRECISION',
        'text': 'TEXT'
      }
    }
    
    return type_mappings.get(db_type, {}).get(puml_type, 'TEXT')