# ai/models/migration.py
from dataclasses import dataclass


@dataclass
class TableMigration:
  """Representa una migración para una tabla."""
  table_name: str
  up: str          # sentencia CREATE TABLE
  down: str        # sentencia DROP TABLE
  complete_block: str  # bloque completo con -- migrate:up/down
  index: int = 0   # orden de aparición