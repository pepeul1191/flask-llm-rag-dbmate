# ai/services/sql_parser.py
import re
import logging
from ai.models.schema import (
  ColumnSchema,
  ForeignKeySchema,
  TableSchema,
  SchemaModel
)

logger = logging.getLogger(__name__)


CONSTRAINT_KEYWORDS = {
  'PRIMARY', 'NOT', 'NULL', 'UNIQUE', 'DEFAULT',
  'AUTOINCREMENT', 'AUTO_INCREMENT', 'REFERENCES',
  'CHECK', 'CONSTRAINT', 'GENERATED', 'COLLATE'
}

TABLE_CONSTRAINT_PREFIXES = (
  'PRIMARY KEY',
  'FOREIGN KEY',
  'UNIQUE',
  'CONSTRAINT',
  'CHECK'
)


def _tokenize(part: str) -> list[str]:
  """Divide respetando paréntesis balanceados."""
  tokens, buf, depth = [], '', 0
  for ch in part:
    if ch == '(':
      depth += 1
      buf += ch
    elif ch == ')':
      depth -= 1
      buf += ch
    elif ch.isspace() and depth == 0:
      if buf:
        tokens.append(buf)
        buf = ''
    else:
      buf += ch
  if buf:
    tokens.append(buf)
  return tokens


def _split_top_level(body: str) -> list[str]:
  """Separa por comas de primer nivel."""
  parts, current, depth = [], [], 0
  for ch in body:
    if ch == '(':
      depth += 1
      current.append(ch)
    elif ch == ')':
      depth -= 1
      current.append(ch)
    elif ch == ',' and depth == 0:
      parts.append(''.join(current).strip())
      current = []
    else:
      current.append(ch)
  if current:
    parts.append(''.join(current).strip())
  return [p for p in parts if p]


def _normalize_sql_type(raw: str) -> str:
  """Normaliza el tipo SQL a una etiqueta comparable con el PUML."""
  if not raw:
    return 'string'
  t = raw.strip().lower()
  t = re.sub(r'\(.*\)', '', t).strip()  # quitar tamaño
  aliases = {
    'varchar': 'string',
    'char': 'string',
    'nvarchar': 'string',
    'text': 'string',
    'string': 'string',
    'int': 'int',
    'integer': 'int',
    'bigint': 'int',
    'smallint': 'int',
    'serial': 'int',
    'bigserial': 'int',
    'float': 'float',
    'double': 'float',
    'double precision': 'float',
    'real': 'float',
    'decimal': 'float',
    'numeric': 'float',
    'boolean': 'boolean',
    'bool': 'boolean',
    'date': 'date',
    'datetime': 'datetime',
    'timestamp': 'datetime',
    'time': 'time',
    'uuid': 'uuid',
    'blob': 'blob',
  }
  return aliases.get(t, t)


def _parse_column_definition(part: str) -> ColumnSchema | None:
  """Convierte una definición de columna en ColumnSchema."""
  tokens = _tokenize(part)
  if len(tokens) < 2:
    return None
  name = tokens[0].strip('`"[]').strip()
  if not name:
    return None

  type_tokens = []
  rest_tokens = []
  i = 1
  while i < len(tokens):
    tok_upper = tokens[i].upper()
    if tok_upper in CONSTRAINT_KEYWORDS:
      break
    type_tokens.append(tokens[i])
    i += 1
  rest_tokens = tokens[i:]

  raw_type = ' '.join(type_tokens) if type_tokens else 'text'
  rest = ' '.join(rest_tokens).upper()

  is_pk = 'PRIMARY KEY' in rest
  is_not_null = 'NOT NULL' in rest
  is_unique = 'UNIQUE' in rest
  default_match = re.search(r'DEFAULT\s+(.+?)(?:\s+(?:NOT|NULL|UNIQUE|PRIMARY|REFERENCES|CHECK)\b|$)', rest)
  default_value = default_match.group(1) if default_match else None

  return ColumnSchema(
    name=name,
    type=_normalize_sql_type(raw_type),
    is_pk=is_pk,
    is_nullable=not is_not_null and not is_pk,
    is_unique=is_unique,
    default=default_value
  )


def _parse_primary_key_constraint(part: str) -> list[str]:
  m = re.search(r'PRIMARY\s+KEY\s*\(([^)]+)\)', part, re.IGNORECASE)
  if not m:
    return []
  return [c.strip().strip('`"[]') for c in m.group(1).split(',')]


def _parse_foreign_key_constraint(part: str) -> ForeignKeySchema | None:
  m = re.search(
    r'FOREIGN\s+KEY\s*\(\s*[`"\[]?(\w+)[`"\]]?\s*\)\s*'
    r'REFERENCES\s+[`"\[]?(\w+)[`"\]]?\s*\(\s*[`"\[]?(\w+)[`"\]]?\s*\)',
    part,
    re.IGNORECASE
  )
  if not m:
    return None
  return ForeignKeySchema(column=m.group(1), ref_table=m.group(2), ref_column=m.group(3))


def _parse_create_body(table_name: str, body: str) -> TableSchema:
  """Construye TableSchema a partir del cuerpo de un CREATE TABLE."""
  table = TableSchema(name=table_name)
  column_pks = []
  table_level_pks = []

  for part in _split_top_level(body):
    upper = part.upper().lstrip()
    if upper.startswith('PRIMARY KEY'):
      table_level_pks.extend(_parse_primary_key_constraint(part))
      continue
    if upper.startswith('FOREIGN KEY'):
      fk = _parse_foreign_key_constraint(part)
      if fk:
        table.foreign_keys.append(fk)
      continue
    if upper.startswith('CONSTRAINT'):
      # CONSTRAINT name FOREIGN KEY (...) REFERENCES ...
      fk = _parse_foreign_key_constraint(part)
      if fk:
        table.foreign_keys.append(fk)
      pks = _parse_primary_key_constraint(part)
      if pks:
        table_level_pks.extend(pks)
      continue
    if upper.startswith('UNIQUE') or upper.startswith('CHECK'):
      continue

    col = _parse_column_definition(part)
    if col is None:
      continue
    table.columns[col.name.lower()] = col
    if col.is_pk:
      column_pks.append(col.name)

  # Si hay PK a nivel tabla, marcar las columnas
  for pk_name in set(table_level_pks + column_pks):
    key = pk_name.lower()
    if key in table.columns:
      table.columns[key].is_pk = True
      table.columns[key].is_nullable = False
    else:
      table.columns[key] = ColumnSchema(
        name=pk_name, type='int', is_pk=True, is_nullable=False
      )

  return table


def _extract_create_statements(sql_text: str) -> list[tuple[str, str]]:
  """Devuelve [(nombre_tabla, cuerpo_create)] de todo el SQL."""
  pattern = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?'
    r'[`"\[]?(\w+)[`"\]]?\s*\((.*?)\)\s*;',
    re.IGNORECASE | re.DOTALL
  )
  results = []
  for m in pattern.finditer(sql_text):
    results.append((m.group(1), m.group(2)))
  return results


def parse_sql_schema(sql_text: str, db_type: str = 'sqlite') -> SchemaModel:
  """Parsea el SQL generado y devuelve un SchemaModel."""
  schema = SchemaModel()
  if not sql_text:
    return schema

  for table_name, body in _extract_create_statements(sql_text):
    try:
      table = _parse_create_body(table_name, body)
      schema.add_table(table)
    except Exception as e:
      logger.warning("Error parseando tabla %s: %s", table_name, e)

  logger.info("SQL parsed: %d tables", len(schema.tables))
  return schema