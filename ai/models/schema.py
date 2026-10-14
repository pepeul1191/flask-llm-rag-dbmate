# ai/models/schema.py
from dataclasses import dataclass, field

@dataclass
class ColumnSchema:
  """Columna dentro de una tabla."""
  name: str
  type: str
  is_pk: bool = False
  is_nullable: bool = True
  is_unique: bool = False
  default: str | None = None


@dataclass
class ForeignKeySchema:
  """Relación de clave foránea."""
  column: str
  ref_table: str
  ref_column: str


@dataclass
class TableSchema:
  """Tabla con sus columnas y FKs."""
  name: str
  columns: dict[str, ColumnSchema] = field(default_factory=dict)
  foreign_keys: list[ForeignKeySchema] = field(default_factory=list)


@dataclass
class SchemaModel:
  """Modelo de esquema completo (esperado o generado)."""
  tables: dict[str, TableSchema] = field(default_factory=dict)

  def table(self, name: str) -> TableSchema | None:
    return self.tables.get(name.lower())

  def add_table(self, table: TableSchema) -> None:
    self.tables[table.name.lower()] = table