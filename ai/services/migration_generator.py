# ai/services/migration_generator.py
import os
import re
import json
import shutil
import logging
import datetime
from typing import Dict, List, Tuple
from ..models.migration import TableMigration
from .fallback import generate_direct_migrations

logger = logging.getLogger(__name__)


def generate_sql_migrations_with_rag(chain, db_type: str, puml_file: str) -> str:
  """Genera migraciones usando la cadena RAG."""
  with open(puml_file, 'r', encoding='utf-8') as f:
    puml_content = f.read()

  entity_pattern = r'entity\s+(\w+)\s*\{([^}]+)\}'
  entities = re.findall(entity_pattern, puml_content, re.IGNORECASE | re.DOTALL)
  entity_info = []
  for entity_name, entity_content in entities:
    attributes = re.findall(r'\s*(\w+)\s*:\s*([^\n]+)', entity_content)
    entity_info.append(f"Entidad: {entity_name}, Atributos: {attributes}")
  entities_summary = "\n".join(entity_info)

  query = f"""
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
  logger.info("Generating SQL migrations...")
  try:
    response = chain.invoke(query)
    return response
  except Exception as e:
    logger.error(f"Error generating migrations: {e}")
    return f"Error: {e}"


def extract_table_name(sql_statement: str) -> str | None:
  """Extrae el nombre de la tabla de una sentencia SQL."""
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


def parse_migration_blocks(complete_migrations: str) -> Dict[int, TableMigration]:
  """Parsea el texto de migraciones en un diccionario de TableMigration."""
  if complete_migrations.startswith("Error:") or "No puedo cumplir" in complete_migrations:
    logger.error(f"Model refused to generate migrations: {complete_migrations}")
    return {}

  patterns = [
    r'--\s*migrate:up\s*(CREATE TABLE[^;]+;)\s*--\s*migrate:down\s*(DROP TABLE[^;]+;)',
    r'(CREATE TABLE[^;]+;)',
  ]

  tables = {}
  seen_tables = set()

  for pattern in patterns:
    matches = re.findall(pattern, complete_migrations, re.IGNORECASE | re.DOTALL)
    if matches:
      logger.info(f"Found {len(matches)} matches using pattern")
      for i, match in enumerate(matches, len(tables) + 1):
        if isinstance(match, tuple):
          create_stmt, drop_stmt = match
        else:
          create_stmt = match
          table_name = extract_table_name(create_stmt)
          drop_stmt = f"DROP TABLE IF EXISTS {table_name};" if table_name else "DROP TABLE unknown_table;"

        table_name = extract_table_name(create_stmt)
        if table_name and table_name in seen_tables:
          logger.info(f"Skipping duplicate table: {table_name}")
          continue
        seen_tables.add(table_name)

        clean_create = re.sub(r'\s+', ' ', create_stmt.strip())
        clean_drop = re.sub(r'\s+', ' ', drop_stmt.strip())
        complete_block = f"-- migrate:up\n\n{create_stmt.strip()}\n\n-- migrate:down\n\n{drop_stmt.strip()}"

        tables[i] = TableMigration(
          table_name=table_name,
          up=clean_create,
          down=clean_drop,
          complete_block=complete_block,
          index=i
        )
  logger.info(f"Se encontraron {len(tables)} tablas únicas.")
  return tables


def validate_entity_count(puml_file: str, tables_dict: Dict[int, TableMigration]) -> Tuple[int, int]:
  """Valida que el número de entidades coincida con el de tablas generadas."""
  try:
    with open(puml_file, 'r', encoding='utf-8') as f:
      content = f.read()
    entity_pattern = r'entity\s+(\w+)'
    entities = re.findall(entity_pattern, content, re.IGNORECASE)
    expected = len(entities)
    actual = len(tables_dict)
    logger.info(f"Expected entities: {expected}, Generated tables: {actual}")
    if expected != actual:
      print(f"⚠️  ADVERTENCIA: Se esperaban {expected} tablas pero se generaron {actual}")
      generated = [t.table_name for t in tables_dict.values() if t.table_name]
      missing = set(entities) - set(generated)
      if missing:
        print(f"📋 Entidades faltantes: {', '.join(missing)}")
      if generated:
        print(f"📋 Tablas generadas: {', '.join(generated)}")
    return expected, actual
  except Exception as e:
    logger.error(f"Error validating entity count: {e}")
    return 0, len(tables_dict)


def enforce_original_names(puml_file: str, tables_dict: Dict[int, TableMigration]) -> Dict[int, TableMigration]:
  """Corrige los nombres de tabla para que coincidan exactamente con las entidades del PUML."""
  try:
    with open(puml_file, 'r', encoding='utf-8') as f:
      content = f.read()
    entity_pattern = r'entity\s+(\w+)'
    original_entities = re.findall(entity_pattern, content, re.IGNORECASE)

    corrected = {}
    for key, table in tables_dict.items():
      current = table.table_name
      matching = None
      for entity in original_entities:
        if entity.lower() == current.lower():
          matching = entity
          break
      if matching and matching != current:
        corrected_up = re.sub(
          f'TABLE\\s+{re.escape(current)}',
          f'TABLE {matching}',
          table.up,
          flags=re.IGNORECASE
        )
        corrected_down = re.sub(
          f'TABLE\\s+{re.escape(current)}',
          f'TABLE {matching}',
          table.down,
          flags=re.IGNORECASE
        )
        corrected_block = re.sub(
          f'TABLE\\s+{re.escape(current)}',
          f'TABLE {matching}',
          table.complete_block,
          flags=re.IGNORECASE
        )
        corrected[key] = TableMigration(
          table_name=matching,
          up=corrected_up,
          down=corrected_down,
          complete_block=corrected_block,
          index=table.index
        )
        print(f"✓ Corregido: '{current}' -> '{matching}'")
      else:
        corrected[key] = table
    return corrected
  except Exception as e:
    logger.error(f"Error enforcing original names: {e}")
    return tables_dict


def save_migration_files(tables_dict: Dict[int, TableMigration], puml_basename: str, db_type: str, complete_migrations: str):
  """Guarda las migraciones en archivos individuales y un resumen completo."""
  if not tables_dict:
    print("❌ No hay migraciones para guardar.")
    return

  complete_filename = f"complete_migrations_{puml_basename}_{db_type}.sql"
  with open(complete_filename, 'w', encoding='utf-8') as f:
    f.write(f"-- Migraciones generadas desde: {puml_basename}.puml\n")
    f.write(f"-- Tipo de base de datos: {db_type}\n")
    f.write(f"-- Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"-- Total de tablas: {len(tables_dict)}\n\n")
    f.write(complete_migrations)
  print(f"✓ Migraciones completas guardadas en: {complete_filename}")

  migrations_dir = f"migrations_{puml_basename}_{db_type}"
  if os.path.exists(migrations_dir):
    shutil.rmtree(migrations_dir)
  os.makedirs(migrations_dir, exist_ok=True)

  base_ts = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
  for key, table in tables_dict.items():
    ts = str(base_ts + key)
    filename = f"{migrations_dir}/{ts}_create_{table.table_name}.sql"
    with open(filename, 'w', encoding='utf-8') as f:
      f.write(table.complete_block)
    print(f"✓ Migración {key} ({table.table_name}) guardada en: {filename}")

def generate_sql_migrations_direct(chain, db_type: str, puml_file: str) -> str:
  """
  Igual que generate_sql_migrations_with_rag pero sin retriever.
  Se usa en el modo llm_only para la comparación pedida por el Reviewer 1.
  """
  with open(puml_file, 'r', encoding='utf-8') as f:
    puml_content = f.read()

  entity_pattern = r'entity\s+(\w+)\s*\{([^}]+)\}'
  entities = re.findall(entity_pattern, puml_content, re.IGNORECASE | re.DOTALL)
  entity_info = []
  for entity_name, entity_content in entities:
    attributes = re.findall(r'\s*(\w+)\s*:\s*([^\n]+)', entity_content)
    entity_info.append(f"Entidad: {entity_name}, Atributos: {attributes}")
  entities_summary = "\n".join(entity_info)

  query = f"""
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

RESPONDE ÚNICAMENTE con las sentencias SQL en el formato especificado, sin explicaciones.
"""
  logger.info("Generating SQL migrations (direct, no RAG)...")
  try:
    response = chain.invoke({"context": "(sin contexto RAG)", "question": query})
    return response
  except Exception as e:
    logger.error(f"Error generating migrations (direct): {e}")
    return f"Error: {e}"