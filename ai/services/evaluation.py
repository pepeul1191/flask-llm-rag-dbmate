# ai/services/evaluation.py
import logging
from ai.services.structural_validator import ValidationReport

logger = logging.getLogger(__name__)


def _safe_div(num: int, den: int) -> float:
  return round(num / den, 4) if den else 0.0


def compute_structural_metrics(report: ValidationReport) -> dict:
  """
  Calcula métricas desglosadas a partir de un ValidationReport.
  Cubre la observación del Reviewer 1 (no basta Table Accuracy).
  """
  s = report.stats

  table_acc = _safe_div(s.get('matched_tables', 0), s.get('expected_tables', 0))
  col_acc = _safe_div(s.get('matched_columns', 0), s.get('expected_columns', 0))
  type_acc = _safe_div(s.get('matched_types', 0), s.get('expected_types', 0))
  pk_acc = _safe_div(s.get('matched_pks', 0), s.get('expected_pks', 0))
  fk_acc = _safe_div(s.get('matched_fks', 0), s.get('expected_fks', 0)) \
         if s.get('expected_fks', 0) else None

  # Full-schema: sólo correcto si las 5 anteriores son 1.0
  full_schema = 1.0 if all([
    table_acc == 1.0,
    col_acc == 1.0,
    type_acc == 1.0,
    pk_acc == 1.0,
    fk_acc == 1.0
  ]) else 0.0

  # Precision/Recall a nivel de "unidad estructural"
  # Tomamos como unidades: columnas + tipos + FKs esperadas
  expected_units = (
    s.get('expected_columns', 0)
    + s.get('expected_types', 0)
    + s.get('expected_fks', 0)
  )
  matched_units = (
    s.get('matched_columns', 0)
    + s.get('matched_types', 0)
    + s.get('matched_fks', 0)
  )

  # Unidades generadas = mismas que esperadas + extras detectadas
  extra_cols = sum(len(v) for v in report.extra_columns.values())
  extra_fks = sum(
    len([d for d in diff['diffs'] if 'extra' in d])
    for diff in report.fk_mismatches
  )
  generated_units = matched_units + extra_cols + extra_fks

  precision = _safe_div(matched_units, generated_units)
  recall = _safe_div(matched_units, expected_units)
  f1 = (
    round(2 * precision * recall / (precision + recall), 4)
    if (precision + recall) > 0 else 0.0
  )

  return {
    'table_accuracy': table_acc,
    'column_accuracy': col_acc,
    'data_type_accuracy': type_acc,
    'primary_key_accuracy': pk_acc,
    'foreign_key_accuracy': fk_acc,
    'full_schema_accuracy': full_schema,
    'precision': precision,
    'recall': recall,
    'f1': f1,
    'counts': {
      'expected_tables': s.get('expected_tables', 0),
      'generated_tables': s.get('generated_tables', 0),
      'missing_tables': len(report.missing_tables),
      'extra_tables': len(report.extra_tables),
      'missing_columns': sum(len(v) for v in report.missing_columns.values()),
      'extra_columns': extra_cols,
      'type_mismatches': sum(len(v) for v in report.type_mismatches.values()),
      'pk_mismatches': len(report.pk_mismatches),
      'fk_mismatches': sum(len(v['diffs']) for v in report.fk_mismatches),
    }
  }


def inject_errors(schema, error_types: list[str]):
  """
  Devuelve una copia del SchemaModel con errores inyectados.
  Útil para medir falsos negativos del validador (Reviewer 1).
  """
  import copy
  mutated = copy.deepcopy(schema)

  for etype in error_types:
    if etype == 'drop_table' and mutated.tables:
      mutated.tables.pop(next(iter(mutated.tables)))
    elif etype == 'drop_column':
      for t in mutated.tables.values():
        if len(t.columns) > 1:
          t.columns.pop(next(k for k in t.columns if not t.columns[k].is_pk))
          break
    elif etype == 'change_type':
      for t in mutated.tables.values():
        for c in t.columns.values():
          c.type = 'blob'
          break
        break
    elif etype == 'drop_pk':
      for t in mutated.tables.values():
        for c in t.columns.values():
          c.is_pk = False
        break
    elif etype == 'drop_fk':
      for t in mutated.tables.values():
        if t.foreign_keys:
          t.foreign_keys.pop()
          break
    elif etype == 'rename_table' and mutated.tables:
      old = next(iter(mutated.tables))
      table = mutated.tables.pop(old)
      table.name = table.name + '_x'
      mutated.tables[table.name.lower()] = table

  return mutated