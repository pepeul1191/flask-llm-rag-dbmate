# ai/services/fallback.py
import re
import logging

logger = logging.getLogger(__name__)


def map_puml_to_sql(puml_type: str, db_type: str) -> str:
  """Mapea tipos PUML a tipos SQL según la base de datos."""
  puml_type = puml_type.lower().strip()
  type_mappings = {
    'sqlite': {
      'string': 'TEXT', 'int': 'INTEGER', 'integer': 'INTEGER',
      'boolean': 'INTEGER', 'date': 'TEXT', 'datetime': 'TEXT',
      'float': 'REAL', 'double': 'REAL', 'text': 'TEXT'
    },
    'mysql': {
      'string': 'VARCHAR(255)', 'int': 'INT', 'integer': 'INT',
      'boolean': 'BOOLEAN', 'date': 'DATE', 'datetime': 'DATETIME',
      'float': 'FLOAT', 'double': 'DOUBLE', 'text': 'TEXT'
    },
    'postgres': {
      'string': 'VARCHAR(255)', 'int': 'INTEGER', 'integer': 'INTEGER',
      'boolean': 'BOOLEAN', 'date': 'DATE', 'datetime': 'TIMESTAMP',
      'float': 'REAL', 'double': 'DOUBLE PRECISION', 'text': 'TEXT'
    }
  }
  return type_mappings.get(db_type, {}).get(puml_type, 'TEXT')


def generate_direct_migrations(puml_file: str, db_type: str) -> str:
  """Genera migraciones directamente desde el PUML (fallback)."""
  logger.info("Using direct migration generation as fallback...")
  try:
    with open(puml_file, 'r', encoding='utf-8') as f:
      content = f.read()

    entity_pattern = r'entity\s+(\w+)\s*\{([^}]+)\}'
    entities = re.findall(entity_pattern, content, re.IGNORECASE | re.DOTALL)
    migrations = []

    for entity_name, entity_content in entities:
      attr_pattern = r'\s*(\w+)\s*:\s*([^\n]+)'
      attributes = re.findall(attr_pattern, entity_content)

      create_lines = [f"CREATE TABLE {entity_name} ("]
      create_lines.append("  id SERIAL PRIMARY KEY," if db_type == 'postgres' else "  id INTEGER PRIMARY KEY AUTOINCREMENT,")

      for attr_name, attr_type in attributes:
        sql_type = map_puml_to_sql(attr_type, db_type)
        create_lines.append(f"  {attr_name} {sql_type},")

      create_lines[-1] = create_lines[-1].rstrip(',')
      create_lines.append(");")
      create_stmt = "\n".join(create_lines)
      drop_stmt = f"DROP TABLE IF EXISTS {entity_name};"
      migration_block = f"-- migrate:up\n\n{create_stmt}\n\n-- migrate:down\n\n{drop_stmt}\n"
      migrations.append(migration_block)

    return "\n".join(migrations)
  except Exception as e:
    logger.error(f"Error in direct migration generation: {e}")
    return ""