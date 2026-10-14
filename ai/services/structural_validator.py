# ai/services/structural_validator.py
import logging
from dataclasses import dataclass, field
from ai.models.schema import SchemaModel

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
  """Resultado de comparar el esquema esperado vs el generado."""
  # Tablas
  missing_tables: list[str] = field(default_factory=list)
  extra_tables: list[str] = field(default_factory=list)
  # Columnas
  missing_columns: dict[str, list[str]] = field(default_factory=dict)
  extra_columns: dict[str, list[str]] = field(default_factory=dict)
  # Tipos
  type_mismatches: dict[str, list[dict]] = field(default_factory=dict)
  # PKs
  pk_mismatches: list[dict] = field(default_factory=list)
  # FKs
  fk_mismatches: list[dict] = field(default_factory=list)
  # Not-null / unique (opcional, útil para el paper)
  nullability_mismatches: dict[str, list[dict]] = field(default_factory=dict)

  # Estadísticas
  stats: dict = field(default_factory=dict)

  @property
  def is_valid(self) -> bool:
    return not any([
      self.missing_tables,
      self.extra_tables,
      self.missing_columns,
      self.extra_columns,
      self.type_mismatches,
      self.pk_mismatches,
      self.fk_mismatches,
      self.nullability_mismatches,
    ])

  def summary(self) -> str:
    lines = []
    if self.is_valid:
      lines.append("✅ Sin errores estructurales detectados.")
      return "\n".join(lines)

    if self.missing_tables:
      lines.append(f"  • Tablas faltantes: {', '.join(self.missing_tables)}")
    if self.extra_tables:
      lines.append(f"  • Tablas extra: {', '.join(self.extra_tables)}")
    for t, cols in self.missing_columns.items():
      lines.append(f"  • [{t}] columnas faltantes: {', '.join(cols)}")
    for t, cols in self.extra_columns.items():
      lines.append(f"  • [{t}] columnas extra: {', '.join(cols)}")
    for t, diffs in self.type_mismatches.items():
      for d in diffs:
        lines.append(
          f"  • [{t}] tipo de '{d['column']}': "
          f"esperado={d['expected']} generado={d['generated']}"
        )
    for diff in self.pk_mismatches:
      lines.append(
        f"  • [{diff['table']}] PK esperada={diff['expected']} "
        f"generada={diff['generated']}"
      )
    for diff in self.fk_mismatches:
      for d in diff['diffs']:
        kind = 'faltante' if 'missing' in d else 'extra'
        lines.append(f"  • [{diff['table']}] FK {kind}: {d.get('missing') or d.get('extra')}")
    for t, diffs in self.nullability_mismatches.items():
      for d in diffs:
        lines.append(
          f"  • [{t}] nullability de '{d['column']}': "
          f"esperado={'NULL' if d['expected'] else 'NOT NULL'} "
          f"generado={'NULL' if d['generated'] else 'NOT NULL'}"
        )
    return "\n".join(lines)

  def to_dict(self) -> dict:
    return {
      'is_valid': self.is_valid,
      'missing_tables': self.missing_tables,
      'extra_tables': self.extra_tables,
      'missing_columns': self.missing_columns,
      'extra_columns': self.extra_columns,
      'type_mismatches': self.type_mismatches,
      'pk_mismatches': self.pk_mismatches,
      'fk_mismatches': self.fk_mismatches,
      'nullability_mismatches': self.nullability_mismatches,
      'stats': self.stats
    }


def _normalize(name: str) -> str:
  return name.strip().strip('`"[]').lower()


def validate_schema(expected: SchemaModel, generated: SchemaModel) -> ValidationReport:
  """Compara dos SchemaModel y devuelve un ValidationReport detallado."""
  report = ValidationReport()

  exp_tables = {k.lower(): v for k, v in expected.tables.items()}
  gen_tables = {k.lower(): v for k, v in generated.tables.items()}

  # ----- Tablas -----
  matched_tables = 0
  for tname in exp_tables:
    if tname not in gen_tables:
      report.missing_tables.append(exp_tables[tname].name)
    else:
      matched_tables += 1
  for tname in gen_tables:
    if tname not in exp_tables:
      report.extra_tables.append(gen_tables[tname].name)

  # Contadores para métricas
  stats = {
    'expected_tables': len(exp_tables),
    'generated_tables': len(gen_tables),
    'matched_tables': matched_tables,
    'expected_columns': 0,
    'generated_columns': 0,
    'matched_columns': 0,
    'expected_types': 0,
    'matched_types': 0,
    'expected_pks': 0,
    'matched_pks': 0,
    'expected_fks': 0,
    'matched_fks': 0,
  }

  # ----- Por tabla -----
  for tname, exp_table in exp_tables.items():
    if tname not in gen_tables:
      continue
    gen_table = gen_tables[tname]

    exp_cols = {k.lower(): v for k, v in exp_table.columns.items()}
    gen_cols = {k.lower(): v for k, v in gen_table.columns.items()}

    stats['expected_columns'] += len(exp_cols)
    stats['generated_columns'] += len(gen_cols)

    missing = [exp_cols[c].name for c in exp_cols if c not in gen_cols]
    extra = [gen_cols[c].name for c in gen_cols if c not in exp_cols]
    if missing:
      report.missing_columns[exp_table.name] = missing
    if extra:
      report.extra_columns[exp_table.name] = extra

    # Tipos y nullability en las columnas coincidentes
    type_diffs = []
    null_diffs = []
    for ckey in exp_cols:
      if ckey not in gen_cols:
        continue
      stats['matched_columns'] += 1
      ec = exp_cols[ckey]
      gc = gen_cols[ckey]
      stats['expected_types'] += 1
      if _normalize(ec.type) == _normalize(gc.type):
        stats['matched_types'] += 1
      else:
        type_diffs.append({
          'column': ec.name,
          'expected': ec.type,
          'generated': gc.type
        })
      if bool(ec.is_nullable) != bool(gc.is_nullable):
        null_diffs.append({
          'column': ec.name,
          'expected': ec.is_nullable,
          'generated': gc.is_nullable
        })
    if type_diffs:
      report.type_mismatches[exp_table.name] = type_diffs
    if null_diffs:
      report.nullability_mismatches[exp_table.name] = null_diffs

    # ----- PKs -----
    exp_pks = sorted([c.name.lower() for c in exp_table.columns.values() if c.is_pk])
    gen_pks = sorted([c.name.lower() for c in gen_table.columns.values() if c.is_pk])
    if exp_pks:
      stats['expected_pks'] += 1
      if exp_pks == gen_pks:
        stats['matched_pks'] += 1
      else:
        report.pk_mismatches.append({
          'table': exp_table.name,
          'expected': exp_pks,
          'generated': gen_pks
        })

    # ----- FKs -----
    exp_fk_set = {
      (fk.column.lower(), fk.ref_table.lower(), fk.ref_column.lower())
      for fk in exp_table.foreign_keys
    }
    gen_fk_set = {
      (fk.column.lower(), fk.ref_table.lower(), fk.ref_column.lower())
      for fk in gen_table.foreign_keys
    }
    stats['expected_fks'] += len(exp_fk_set)
    stats['matched_fks'] += len(exp_fk_set & gen_fk_set)

    fk_diffs = []
    for fk in exp_fk_set - gen_fk_set:
      fk_diffs.append({'missing': list(fk)})
    for fk in gen_fk_set - exp_fk_set:
      fk_diffs.append({'extra': list(fk)})
    if fk_diffs:
      report.fk_mismatches.append({
        'table': exp_table.name,
        'diffs': fk_diffs
      })

  report.stats = stats
  logger.info("Structural validation finished. Valid=%s", report.is_valid)
  return report