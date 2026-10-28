# ai/services/puml_parser.py
import os
import re
import logging
from ai.models.schema import (
  ColumnSchema,
  ForeignKeySchema,
  TableSchema,
  SchemaModel
)

logger = logging.getLogger(__name__)


# Tipos PUML aceptados -> etiqueta normalizada interna
PUML_TYPE_ALIASES = {
  'string': 'string',
  'varchar': 'string',
  'text': 'string',
  'int': 'int',
  'integer': 'int',
  'long': 'int',
  'bigint': 'int',
  'smallint': 'int',
  'tinyint': 'int',
  'mediumint': 'int',
  'serial': 'int',
  'bigserial': 'int',
  'float': 'float',
  'double': 'float',
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
  'binary': 'blob',
  'varbinary': 'blob',
}


def _normalize_puml_type(raw: str) -> str:
  """Reduce el tipo PUML a una etiqueta interna."""
  if not raw:
    return 'string'
  clean = raw.strip().lower()
  # Quitar estereotipos y modificadores
  clean = re.sub(r'<<[^>]*>>', '', clean).strip()
  clean = re.sub(r'\{[^}]*\}', '', clean).strip()
  # Quedarse con la primera palabra (ignora "varchar(255)")
  clean = re.split(r'[\(\s]', clean)[0]
  return PUML_TYPE_ALIASES.get(clean, clean or 'string')


def _strip_visibility(token: str) -> str:
  """Quita marcadores de visibilidad y obligatoriedad."""
  return token.lstrip('+-#~*').strip()


def _parse_entity_attributes(body: str) -> list[ColumnSchema]:
    """Extrae columnas del cuerpo de un entity."""
    columns: list[ColumnSchema] = []
    
    # 🔧 NUEVO: detectar la posición del separador '--'
    # Convención PlantUML: todo lo anterior al '--' son claves primarias
    lines = body.splitlines()
    try:
        separator_idx = next(i for i, l in enumerate(lines) if l.strip() == '--')
    except StopIteration:
        separator_idx = -1  # no hay separador
    
    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue
        if line == '--':
            continue
        if line.startswith('--') or line.startswith('..'):
            continue
        if line.startswith("'"):
            continue
        
        line = line.rstrip(',')
        if ':' in line:
            name_part, type_part = line.split(':', 1)
        else:
            name_part, type_part = line, ''
        
        # 🔧 MODIFICADO: PK si está antes del separador, o por marcador, o si se llama 'id'
        is_pk = (
            (separator_idx >= 0 and idx < separator_idx)  # antes del '--'
            or bool(re.search(r'<<\s*PK\s*>>', type_part, re.IGNORECASE))
            or bool(re.search(r'\{\s*PK\s*\}', type_part, re.IGNORECASE))
            or bool(re.search(r'<<\s*id\s*>>', type_part, re.IGNORECASE))
        )
        
        raw_type = re.sub(r'(<<[^>]*>>|\{[^}]*\})', '', type_part).strip()
        clean_name = _strip_visibility(name_part)
        name = clean_name.split()[0] if clean_name.split() else ''
        name = name.split('(')[0].strip()
        if not name:
            continue
        
        normalized_type = _normalize_puml_type(raw_type)
        if name.lower() == 'id' and not is_pk:
            is_pk = True
        
        columns.append(ColumnSchema(
            name=name,
            type=normalized_type,
            is_pk=is_pk,
            is_nullable=not is_pk
        ))
    return columns


def _infer_fk_column(ref_table: str) -> str:
  """Convención: <tabla_referenciada>_id en minúsculas."""
  return f"{ref_table.lower()}_id"

def _find_existing_fk(table: TableSchema, ref_table: str,
                      label: str | None = None) -> str | None:
    # 1. Label tiene prioridad (nombre exacto de la columna FK)
    if label:
        clean = label.lower()
        if clean in table.columns:
            return clean
    # 2. Convención <table>_id / <singular>_id
    ref = ref_table.lower()
    if ref.endswith('ies'):
        singular = ref[:-3] + 'y'
    elif ref.endswith('s'):
        singular = ref[:-1]
    else:
        singular = ref
    for cand in (f"{ref}_id", f"{singular}_id"):
        if cand in table.columns:
            return cand
    return None

def _parse_relationships(content: str) -> list[tuple[str, str, str, str, str]]:
  """Devuelve (left, lcard, rcard, right, label)."""
  pattern = re.compile(
    r'([A-Za-z_]\w*)\s+(["\|o\{\}]+)\s*--\s*(["\|o\{\}]+)\s+([A-Za-z_]\w*)'
    r'(?:\s*:\s*([^\n]+))?',
    re.IGNORECASE
  )
  return [(m.group(1), m.group(2), m.group(3), m.group(4),
            (m.group(5) or "").strip().strip('"').strip("'"))
          for m in pattern.finditer(content)]


def _card_is_many(card: str) -> bool:
  """Detecta si la cardinalidad implica 'muchos' (acepta '{' o '}')."""
  return '{' in card or '}' in card


def _apply_relationships(schema, relationships):
    for left, lcard, rcard, right, label in relationships:
        lt, rt = schema.table(left), schema.table(right)
        if not lt or not rt:
            continue
        if _card_is_many(rcard) and not _card_is_many(lcard):
            fk = _find_existing_fk(rt, lt.name, label) or _infer_fk_column(lt.name)
            _ensure_fk_column(rt, fk, lt.name)
            rt.foreign_keys.append(ForeignKeySchema(
                column=fk, ref_table=lt.name, ref_column=_primary_key_name(lt)))
        elif _card_is_many(lcard) and not _card_is_many(rcard):
            fk = _find_existing_fk(lt, rt.name, label) or _infer_fk_column(rt.name)
            _ensure_fk_column(lt, fk, rt.name)
            lt.foreign_keys.append(ForeignKeySchema(
                column=fk, ref_table=rt.name, ref_column=_primary_key_name(rt)))


def _primary_key_name(table: TableSchema) -> str:
  for col in table.columns.values():
    if col.is_pk:
      return col.name
  return 'id'


def _ensure_fk_column(table: TableSchema, fk_col: str, ref_table: str) -> None:
  """Si la columna FK no existe, la añade como int nullable."""
  if fk_col.lower() in table.columns:
    return
  table.columns[fk_col.lower()] = ColumnSchema(
    name=fk_col,
    type='int',
    is_pk=False,
    is_nullable=True
  )


def parse_puml_schema(puml_file: str) -> SchemaModel:
  """
  Parsea un archivo PlantUML y devuelve un SchemaModel con:
    - tablas (entity)
    - columnas con tipo y PK
    - FKs inferidas a partir de relaciones 1-N
  """
  if not os.path.exists(puml_file):
    raise FileNotFoundError(f"PUML no encontrado: {puml_file}")

  with open(puml_file, 'r', encoding='utf-8') as f:
    content = f.read()

  schema = SchemaModel()

  entity_pattern = re.compile(
    r'entity\s+("?[A-Za-z_]\w*"?)\s*(?:as\s+\w+)?\s*\{([^}]*)\}',
    re.IGNORECASE | re.DOTALL
  )

  for match in entity_pattern.finditer(content):
    raw_name = match.group(1).strip().strip('"')
    body = match.group(2)
    columns = _parse_entity_attributes(body)

    # Asegurar PK explícita
    if not any(c.is_pk for c in columns):
      for col in columns:
        if col.name.lower() == 'id':
          col.is_pk = True
          col.is_nullable = False
          break
      else:
        columns.insert(0, ColumnSchema(
          name='id',
          type='int',
          is_pk=True,
          is_nullable=False
        ))

    table = TableSchema(
      name=raw_name,
      columns={c.name.lower(): c for c in columns}
    )
    schema.add_table(table)

  relationships = _parse_relationships(content)
  _apply_relationships(schema, relationships)

  logger.info(
    "PUML parsed: %d tables, %d relationships",
    len(schema.tables),
    len(relationships)
  )
  return schema